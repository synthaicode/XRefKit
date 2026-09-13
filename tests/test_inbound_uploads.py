from __future__ import annotations

import hashlib
import json
import os
import uuid
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from xrefkit.mcp.audit import SessionRunBinding
from xrefkit.mcp.contribution_returns import MAX_FILE_BYTES
import xrefkit.mcp.inbound_uploads as inbound_module
from xrefkit.mcp.inbound_uploads import (
    MAX_ACTIVE_RESERVATIONS_PER_SESSION,
    InboundUploadManager,
    UploadError,
    _declared_content_length,
    add_inbound_webdav_routes,
)
from xrefkit.mcp.server import _build_inbound_upload_manager, main as server_main


def binding() -> SessionRunBinding:
    return SessionRunBinding(
        run_id=str(uuid.uuid4()),
        mcp_session_id=str(uuid.uuid4()),
        repository_fingerprint="a" * 64,
        skill_id="sample",
    )


def manager(root: Path, *, clock=lambda: 1_800_000_000) -> InboundUploadManager:
    return InboundUploadManager(
        root,
        public_base_url="http://127.0.0.1:8765",
        listener={"mode": "test", "process_lifecycle": "test"},
        clock=clock,
    )


def app_for(upload_manager: InboundUploadManager):
    pytest.importorskip("starlette")
    from starlette.applications import Starlette

    app = Starlette()
    add_inbound_webdav_routes(app, upload_manager)
    return app


def test_scoped_webdav_upload_freezes_and_seals_exact_tree(tmp_path: Path) -> None:
    from starlette.testclient import TestClient

    active = binding()
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=active)
    token = issued["bearer_token"]
    base = f"/webdav/uploads/{issued['upload_id']}"
    auth = {"Authorization": f"Bearer {token}"}
    with TestClient(app_for(upload_manager)) as client:
        assert client.options(base, headers=auth).status_code == 204
        assert client.request("MKCOL", base + "/nested", headers=auth).status_code == 201
        body = b"# inert observation\n"
        put = client.put(
            base + "/nested/observation.md",
            content=body,
            headers={**auth, "If-None-Match": "*"},
        )
        assert put.status_code == 201
        assert client.head(base + "/nested/observation.md", headers=auth).status_code == 200
        assert client.request("PROPFIND", base, headers={**auth, "Depth": "infinity"}).status_code == 207
        assert client.get(base + "/nested/observation.md", headers=auth).status_code == 405
        assert client.request("MOVE", base + "/nested/observation.md", headers=auth).status_code == 405
        assert client.put(base + "/%252e%252e/escape.md", content=b"x", headers={**auth, "If-None-Match": "*"}).status_code == 400

        calls: list[list[dict]] = []

        def submit(files: list[dict]) -> dict:
            calls.append(files)
            return {"contribution_id": str(uuid.uuid4()), "payload_hash": "b" * 64, "status": "pending_review"}

        expected = [{
            "path": "nested/observation.md",
            "content_hash": hashlib.sha256(body).hexdigest(),
            "byte_count": len(body),
        }]
        result = upload_manager.seal(
            binding=active,
            upload_id=issued["upload_id"],
            expected_files=expected,
            submit=submit,
            request_basis={"kind": "skill_observation"},
        )
        assert result["status"] == "pending_review"
        assert calls[0][0]["content"] == body.decode()
        assert client.put(base + "/late.md", content=b"late", headers={**auth, "If-None-Match": "*"}).status_code == 401

    state_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (tmp_path / ".xrefkit/inbound-uploads").rglob("*.json")
    )
    assert token not in state_text
    assert not (tmp_path / "canonical").exists()


def test_seal_rejects_extra_or_hash_mismatched_tree_terminally(tmp_path: Path) -> None:
    from starlette.testclient import TestClient

    active = binding()
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=active)
    auth = {"Authorization": f"Bearer {issued['bearer_token']}", "If-None-Match": "*"}
    base = f"/webdav/uploads/{issued['upload_id']}"
    with TestClient(app_for(upload_manager)) as client:
        assert client.put(base + "/one.md", content=b"one", headers=auth).status_code == 201
        assert client.put(base + "/extra.md", content=b"extra", headers=auth).status_code == 201
    with pytest.raises(UploadError, match="exactly match"):
        upload_manager.seal(
            binding=active,
            upload_id=issued["upload_id"],
            expected_files=[{"path": "one.md", "content_hash": hashlib.sha256(b"wrong").hexdigest(), "byte_count": 3}],
            submit=lambda files: {},
            request_basis={"kind": "knowledge"},
        )
    state = json.loads((tmp_path / ".xrefkit/inbound-uploads" / issued["upload_id"] / "session.json").read_text())
    assert state["status"] == "invalid"
    with pytest.raises(UploadError, match="terminal"):
        upload_manager.seal(
            binding=active,
            upload_id=issued["upload_id"],
            expected_files=[{"path": "one.md", "content_hash": hashlib.sha256(b"one").hexdigest(), "byte_count": 3}],
            submit=lambda files: {},
            request_basis={"kind": "knowledge"},
        )


def test_seal_rejects_content_hash_mismatch(tmp_path: Path) -> None:
    from starlette.testclient import TestClient

    active = binding()
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=active)
    base = f"/webdav/uploads/{issued['upload_id']}"
    headers = {
        "Authorization": f"Bearer {issued['bearer_token']}",
        "If-None-Match": "*",
    }
    with TestClient(app_for(upload_manager)) as client:
        assert client.put(base + "/one.md", content=b"one", headers=headers).status_code == 201
    with pytest.raises(UploadError, match="content_hash mismatch"):
        upload_manager.seal(
            binding=active,
            upload_id=issued["upload_id"],
            expected_files=[{
                "path": "one.md",
                "content_hash": hashlib.sha256(b"two").hexdigest(),
                "byte_count": 3,
            }],
            submit=lambda files: {},
            request_basis={"kind": "knowledge"},
        )


def test_streaming_quota_failure_removes_partial_file(tmp_path: Path) -> None:
    from starlette.testclient import TestClient

    active = binding()
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=active)
    base = f"/webdav/uploads/{issued['upload_id']}"
    headers = {
        "Authorization": f"Bearer {issued['bearer_token']}",
        "If-None-Match": "*",
    }
    with TestClient(app_for(upload_manager)) as client:
        response = client.put(base + "/too-large.bin", content=b"x" * (MAX_FILE_BYTES + 1), headers=headers)
        assert response.status_code == 413
        assert client.head(base + "/too-large.bin", headers=headers).status_code == 404
        assert client.put(base + "/valid.md", content=b"ok", headers=headers).status_code == 201


def test_hard_link_injection_is_rejected(tmp_path: Path) -> None:
    active = binding()
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=active)
    session_dir = tmp_path / ".xrefkit/inbound-uploads" / issued["upload_id"]
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    os.link(outside, session_dir / "files" / "linked.md")
    with pytest.raises(UploadError, match="hard-linked"):
        upload_manager.head(
            issued["upload_id"],
            "linked.md",
            f"Bearer {issued['bearer_token']}",
        )


def test_finish_put_removes_internal_hardlink_before_seal(tmp_path: Path) -> None:
    active = binding()
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=active)
    session_dir, temp, state = upload_manager.begin_put(
        issued["upload_id"], "one.md", f"Bearer {issued['bearer_token']}"
    )
    temp.write_bytes(b"one")
    upload_manager.reserve_chunk(state["reservation_id"], 3)
    digest = upload_manager.finish_put(session_dir, temp, "one.md", 3, state["reservation_id"])
    assert digest == hashlib.sha256(b"one").hexdigest()
    assert not temp.exists()
    assert (session_dir / "files/one.md").stat().st_nlink == 1
    result = upload_manager.seal(
        binding=active,
        upload_id=issued["upload_id"],
        expected_files=[{"path": "one.md", "content_hash": digest, "byte_count": 3}],
        submit=lambda files: {"status": "pending_review", "payload_hash": "f" * 64},
        request_basis={"kind": "knowledge"},
    )
    assert result["status"] == "pending_review"


def test_global_inflight_reservations_are_atomic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(inbound_module, "MAX_GLOBAL_STAGING_BYTES", 5)
    first = manager(tmp_path)
    first_session = first.issue(binding=binding())
    _, _, first_state = first.begin_put(
        first_session["upload_id"], "one", f"Bearer {first_session['bearer_token']}"
    )
    first.reserve_chunk(first_state["reservation_id"], 3)
    second_session = first.issue(binding=binding())
    _, second_temp, second_state = first.begin_put(
        second_session["upload_id"], "two", f"Bearer {second_session['bearer_token']}"
    )
    with pytest.raises(UploadError, match="global upload staging-byte quota"):
        first.reserve_chunk(second_state["reservation_id"], 3)
    first.abort_put(second_temp, second_state["reservation_id"])


def test_active_put_reservation_count_is_bounded(tmp_path: Path) -> None:
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=binding())
    reservations = []
    for index in range(MAX_ACTIVE_RESERVATIONS_PER_SESSION):
        _, temp, state = upload_manager.begin_put(
            issued["upload_id"], f"{index}.md", f"Bearer {issued['bearer_token']}"
        )
        reservations.append((temp, state["reservation_id"]))
    with pytest.raises(UploadError, match="active upload reservation quota"):
        upload_manager.begin_put(
            issued["upload_id"], "overflow.md", f"Bearer {issued['bearer_token']}"
        )
    for temp, reservation_id in reservations:
        upload_manager.abort_put(temp, reservation_id)


def test_zero_ttl_and_negative_content_length_are_rejected(tmp_path: Path) -> None:
    upload_manager = manager(tmp_path)
    with pytest.raises(ValueError, match="30 through 3600"):
        upload_manager.issue(binding=binding(), expires_in_seconds=0)
    with pytest.raises(UploadError, match="invalid Content-Length"):
        _declared_content_length("-1")


def test_expired_session_cleanup_reclaims_staging(tmp_path: Path) -> None:
    now = [1_800_000_000]
    upload_manager = manager(tmp_path, clock=lambda: now[0])
    issued = upload_manager.issue(binding=binding(), expires_in_seconds=30)
    session_dir, temp, state = upload_manager.begin_put(
        issued["upload_id"], "one", f"Bearer {issued['bearer_token']}"
    )
    temp.write_bytes(b"one")
    upload_manager.reserve_chunk(state["reservation_id"], 3)
    upload_manager.finish_put(session_dir, temp, "one", 3, state["reservation_id"])
    now[0] += 30
    upload_manager.issue(binding=binding())
    assert not (session_dir / "files").exists()


def test_collection_quota_is_enforced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from starlette.testclient import TestClient

    monkeypatch.setattr(inbound_module, "MAX_COLLECTIONS", 1)
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=binding())
    assert issued["limits"]["max_collections"] == 1
    base = f"/webdav/uploads/{issued['upload_id']}"
    headers = {"Authorization": f"Bearer {issued['bearer_token']}"}
    with TestClient(app_for(upload_manager)) as client:
        assert client.request("MKCOL", base + "/one", headers=headers).status_code == 201
        assert client.request("MKCOL", base + "/two", headers=headers).status_code == 413


def test_seal_recovers_crash_before_freeze(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    active = binding()
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=active)
    session_dir, temp, state = upload_manager.begin_put(
        issued["upload_id"], "one", f"Bearer {issued['bearer_token']}"
    )
    temp.write_bytes(b"one")
    upload_manager.reserve_chunk(state["reservation_id"], 3)
    digest = upload_manager.finish_put(session_dir, temp, "one", 3, state["reservation_id"])
    real_replace = os.replace

    def crash_before_freeze(source, target):
        if Path(source).name == "files":
            raise SystemExit("crash")
        return real_replace(source, target)

    kwargs = dict(
        binding=active, upload_id=issued["upload_id"],
        expected_files=[{"path": "one", "content_hash": digest, "byte_count": 3}],
        submit=lambda files: {"status": "pending_review", "payload_hash": "a" * 64},
        request_basis={"kind": "knowledge"},
    )
    with monkeypatch.context() as context:
        context.setattr(inbound_module.os, "replace", crash_before_freeze)
        with pytest.raises(SystemExit):
            upload_manager.seal(**kwargs)
    assert upload_manager.seal(**kwargs)["status"] == "pending_review"


def test_seal_recovers_existing_sealed_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    active = binding()
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=active)
    session_dir, temp, state = upload_manager.begin_put(
        issued["upload_id"], "one", f"Bearer {issued['bearer_token']}"
    )
    temp.write_bytes(b"one")
    upload_manager.reserve_chunk(state["reservation_id"], 3)
    digest = upload_manager.finish_put(session_dir, temp, "one", 3, state["reservation_id"])
    real_atomic = inbound_module._atomic_json

    def crash_before_sealed_status(path, value):
        if path.name == "session.json" and value.get("status") == "sealed":
            raise SystemExit("crash")
        return real_atomic(path, value)

    calls = 0
    def submit(files):
        nonlocal calls
        calls += 1
        return {"status": "pending_review", "payload_hash": "b" * 64}
    kwargs = dict(
        binding=active, upload_id=issued["upload_id"],
        expected_files=[{"path": "one", "content_hash": digest, "byte_count": 3}],
        submit=submit, request_basis={"kind": "knowledge"},
    )
    with monkeypatch.context() as context:
        context.setattr(inbound_module, "_atomic_json", crash_before_sealed_status)
        with pytest.raises(SystemExit):
            upload_manager.seal(**kwargs)
    recovered = upload_manager.seal(**kwargs)
    assert recovered["seal_idempotent_replay"] is True
    assert calls == 1


def _server_args(**overrides) -> Namespace:
    values = dict(
        transport="stdio", host="127.0.0.1", port=8000,
        inbound_webdav_host="127.0.0.1", inbound_webdav_port=8765,
        inbound_webdav_public_base_url=None, inbound_webdav_session_seconds=900,
        ssl_certfile=None,
    )
    values.update(overrides)
    return Namespace(**values)


def test_advertised_upload_url_must_match_owned_listener(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exactly match"):
        _build_inbound_upload_manager(
            _server_args(inbound_webdav_public_base_url="http://remote.example:8765"), tmp_path
        )


def test_sse_inbound_listener_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported with SSE"):
        _build_inbound_upload_manager(_server_args(transport="sse"), tmp_path)


def test_streamable_mcp_and_inbound_routes_share_one_asgi_app(tmp_path: Path) -> None:
    from mcp.server.fastmcp import FastMCP
    from starlette.testclient import TestClient

    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=binding())
    app = FastMCP("route-test").streamable_http_app()
    add_inbound_webdav_routes(app, upload_manager)
    with TestClient(app) as client:
        upload = client.options(
            f"/webdav/uploads/{issued['upload_id']}",
            headers={"Authorization": f"Bearer {issued['bearer_token']}"},
        )
        mcp = client.get("/mcp")
    assert upload.status_code == 204
    assert mcp.status_code != 404


def test_upload_expiry_auth_and_binding_fail_closed(tmp_path: Path) -> None:
    now = [1_800_000_000]
    active = binding()
    upload_manager = manager(tmp_path, clock=lambda: now[0])
    issued = upload_manager.issue(binding=active, expires_in_seconds=30)
    with pytest.raises(UploadError, match="authorization"):
        upload_manager.authorize(issued["upload_id"], "Bearer wrong")
    now[0] += 31
    with pytest.raises(UploadError, match="expired"):
        upload_manager.authorize(issued["upload_id"], f"Bearer {issued['bearer_token']}")
    with pytest.raises(UploadError, match="different Skill Run"):
        upload_manager.seal(
            binding=binding(),
            upload_id=issued["upload_id"],
            expected_files=[{"path": "x.md", "content_hash": "0" * 64, "byte_count": 0}],
            submit=lambda files: {},
            request_basis={},
        )


def test_concurrent_same_seal_has_one_submit_and_idempotent_replay(tmp_path: Path) -> None:
    from starlette.testclient import TestClient

    active = binding()
    upload_manager = manager(tmp_path)
    issued = upload_manager.issue(binding=active)
    body = b"one"
    with TestClient(app_for(upload_manager)) as client:
        response = client.put(
            f"/webdav/uploads/{issued['upload_id']}/one.md",
            content=body,
            headers={"Authorization": f"Bearer {issued['bearer_token']}", "If-None-Match": "*"},
        )
        assert response.status_code == 201
    calls = 0

    def submit(files: list[dict]) -> dict:
        nonlocal calls
        calls += 1
        return {"contribution_id": "c", "payload_hash": "d" * 64, "status": "pending_review"}

    kwargs = dict(
        binding=active,
        upload_id=issued["upload_id"],
        expected_files=[{"path": "one.md", "content_hash": hashlib.sha256(body).hexdigest(), "byte_count": len(body)}],
        submit=submit,
        request_basis={"kind": "knowledge"},
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: upload_manager.seal(**kwargs), range(2)))
    assert calls == 1
    assert sorted(row["seal_idempotent_replay"] for row in results) == [False, True]


@pytest.mark.parametrize(
    "legacy_args",
    [
        ["--contribution-adoption-transport", "webdav"],
        ["--webdav-staging-url", "https://old.example/staging"],
        ["--webdav-canonical-url", "https://old.example/canonical"],
    ],
)
def test_legacy_outbound_webdav_cli_fails_with_inbound_migration(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    legacy_args: list[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        server_main(["--repo", str(tmp_path), *legacy_args])
    assert raised.value.code == 2
    assert "Use --enable-inbound-webdav for client-to-MCP staging" in capsys.readouterr().err


def test_legacy_outbound_webdav_environment_fails_with_inbound_migration(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XREFKIT_ADOPTION_WEBDAV_USERNAME", "legacy")
    with pytest.raises(SystemExit) as raised:
        server_main(["--repo", str(tmp_path)])
    assert raised.value.code == 2
    assert "Use --enable-inbound-webdav for client-to-MCP staging" in capsys.readouterr().err
