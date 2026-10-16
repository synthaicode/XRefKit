from __future__ import annotations

import asyncio
import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from xrefkit.mcp.legacy_guidance import inspect_legacy_environment, prepare_legacy_bundle, bind_migration_tasks
from xrefkit.mcp.legacy_migration import register_legacy_bundle, migration_context, record_mcp_retrieval
from xrefkit.mcp.legacy_resources import materialize_legacy_resources, manifest_hash
from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.mcp.contribution_returns import submit_contribution_return, adopt_contribution_return
from test_contribution_returns import adoption_repo, binding, source, file, signed_review, approval_verifier
from test_subagent_startup import command


def legacy_tree(tmp_path: Path) -> Path:
    root = tmp_path / "old-client"
    for skill in ("one", "two"):
        folder = root / "skills" / skill
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(f"# {skill}\n\nRun `python tools/report.py` from the legacy root.\n", encoding="utf-8")
    (root / "tools").mkdir()
    (root / "tools/shared.py").write_bytes(b"def total(values):\r\n    return sum(values)\r\n")
    (root / "tools/report.py").write_text("from shared import total\nprint(total([2, 3]))\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests/test_existing.py").write_text("# Existing tests are inspected, never automatically run\n", encoding="utf-8")
    (root / ".env").write_text("PASSWORD=secret-value", encoding="utf-8")
    (root / "tools/credentials.json").write_text('{"password":"secret-value"}', encoding="utf-8")
    return root


def prepared(tmp_path: Path) -> dict:
    root = legacy_tree(tmp_path)
    return prepare_legacy_bundle(root, tmp_path / "client-bundle",
        skills=["skills/one", "skills/two"], resources=["tools/shared.py", "tools/report.py", "tests/test_existing.py"])


def adopt_bundle(tmp_path: Path, prepared: dict) -> tuple[Path, str]:
    root = tmp_path / "server"
    root.mkdir()
    adoption_repo(root)
    # A canonical target fixture: tools and imported document families are owned.
    with (root / "ownership.yaml").open("a", encoding="utf-8") as stream:
        stream.write("  - id: custom-skills\n    owner: project\n    paths:\n      - skills/\n    catalog: true\n    distribution: true\n    base_sync: false\n    shadowing: false\n")
    contribution_id = str(uuid.uuid4())
    bundle = Path(prepared["bundle"])
    files = [file(row["path"], (bundle / row["path"]).read_bytes().decode("utf-8")) for row in prepared["upload"]["files"]]
    submit_contribution_return(root, binding=binding(), source_snapshot=source(),
        contribution_id=contribution_id, kind="deterministic_tool", title="Legacy fixture", summary="Test-only inert migration",
        files=files, deterministic_tool=prepared["upload"]["deterministic_tool"], proposed_target_path="tools/legacy-fixture")
    review = signed_review(root, contribution_id=contribution_id, decision_id=str(uuid.uuid4()),
        decision="accepted", reviewer="human:test-fixture", decision_evidence="Test-only approval fixture",
        approved_target_path="tools/legacy-fixture")
    adopt_contribution_return(root, contribution_id=contribution_id, adoption_id=str(uuid.uuid4()),
        reviewer="human:test-fixture", decision_evidence="Test-only adoption fixture",
        approval_token=review["approval_token"], approval_verifier=approval_verifier())
    return root, contribution_id


def test_inventory_preserves_shared_resources_and_excludes_secrets(tmp_path):
    root = legacy_tree(tmp_path)
    inventory = inspect_legacy_environment(root)
    assert inventory["skills"] == ["skills/one", "skills/two"]
    assert inventory["imports"]["tools/report.py"] == ["shared"]
    assert inventory["existing_tests"] == ["tests/test_existing.py"]
    assert {row["path"] for row in inventory["excluded"]} == {".env", "tools/credentials.json"}
    assert inventory["execution_performed"] is False
    with pytest.raises(ValueError, match="excluded"):
        prepare_legacy_bundle(root, tmp_path / "bad", skills=["skills/one"], resources=[".env"])


@pytest.mark.parametrize("key", ["api_key", "apiKey", "access_token", "client-secret", "password"])
def test_quoted_config_credentials_excluded_even_without_secret_filename(tmp_path, key):
    root = tmp_path / "source"
    root.mkdir()
    (root / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    (root / "settings.json").write_text(json.dumps({key: "EXAMPLE_FAKE_TEST_ONLY_123456"}), encoding="utf-8")
    inventory = inspect_legacy_environment(root)
    assert "settings.json" not in inventory["files"]
    assert any(row["path"] == "settings.json" and "credential" in row["reason"] for row in inventory["excluded"])
    result = prepare_legacy_bundle(root, tmp_path / "bundle", skills=["."], resources=[])
    assert "settings.json" not in {row["path"] for row in result["manifest"]["files"]}


@pytest.mark.parametrize("reserved", ["LEGACY-RESOURCES.JSON", "MIGRATION_CHECKS/TEST_PREPARATION.PY", "migration_checks/CASES.JSON"])
def test_preparation_rejects_case_alias_of_generated_files(tmp_path, reserved):
    root = tmp_path / "source"
    root.mkdir()
    (root / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    path = root / reserved
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="reserved"):
        prepare_legacy_bundle(root, tmp_path / "bundle", skills=["."], resources=[])


def test_embedded_bootstrap_lookup_never_spawns_git_inside_request(tmp_path, monkeypatch):
    import xrefkit.mcp.catalog as catalog_module

    catalog = XRefCatalog.build(tmp_path)
    def unexpected_identity(_root):
        raise AssertionError("live bootstrap lookup must not spawn Git identity subprocesses")
    monkeypatch.setattr(catalog_module, "repository_identity", unexpected_identity)
    assert catalog.get_startup_context()["legacy_migration"]["status"] == "not_started"
    assert catalog.get_skill("legacy_flow_skill_migration")["skill_id"] == "legacy_flow_skill_migration"
    assert catalog.get_document_by_xid("7B3E5D1A6104")["content"]


def test_inventory_prunes_environment_directories_before_traversal(tmp_path, monkeypatch):
    import os
    root = tmp_path / "source"
    root.mkdir()
    (root / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    ignored = {".venv", "venv", "node_modules", ".git", "__pycache__"}
    for name in ignored:
        (root / name).mkdir()
        (root / name / "never_read.py").write_text("raise RuntimeError('must never inspect')", encoding="utf-8")
    original = os.scandir
    def guarded(path):
        assert Path(path).name not in ignored, "excluded subtree was traversed"
        return original(path)
    monkeypatch.setattr(os, "scandir", guarded)
    inventory = inspect_legacy_environment(root)
    assert inventory["files"] == ["SKILL.md"]
    assert {row["path"] for row in inventory["excluded"]} == {name + "/" for name in ignored}


def test_preparation_scaffolds_do_not_execute_legacy_code(tmp_path):
    prepared_result = prepared(tmp_path)
    bundle = Path(prepared_result["bundle"])
    original = tmp_path / "old-client/tools/shared.py"
    assert (bundle / "tools/shared.py").read_bytes() == original.read_bytes()
    assert prepared_result["status"] == "prepared_not_verified"
    assert prepared_result["expected_results"].startswith("unknown")
    assert all("tools/shared.py" in row["resources"] for row in prepared_result["manifest"]["skills"])
    result = subprocess.run([sys.executable, "-B", "migration_checks/test_preparation.py"], cwd=bundle,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "skipped=1" in result.stderr
    assert "business" in (bundle / "migration_checks/test_preparation.py").read_text()
    (bundle / "tools/report.py").write_text("edited", encoding="utf-8")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        prepare_legacy_bundle(tmp_path / "old-client", bundle, skills=["skills/one", "skills/two"],
                              resources=["tools/shared.py", "tools/report.py", "tests/test_existing.py"])


def test_real_work_items_are_resumable_and_missing_baseline_not_done(tmp_path):
    log = tmp_path / "migration.md"
    code, output = command("workflow", "run", "--root", str(tmp_path), "--task", "migrate legacy fixture",
                           "--out", str(log), "--completion-condition", "migration verified", "--json")
    assert code == 0, output
    tasks = bind_migration_tasks(log, "a" * 64)
    baseline = next(row for row in tasks if row["item_id"].endswith("baseline"))
    code, output = command("skill", "workitem", "--log", str(log), "--item", baseline["item_id"],
        "--status", "unknown", "--role", "executor", "--criterion-unknown-reason", "Old environment unavailable")
    assert code == 0, output
    before = log.read_bytes()
    bind_migration_tasks(log, "a" * 64)
    assert log.read_bytes() == before
    assert "Old environment unavailable" in log.read_text(encoding="utf-8")


def test_adopt_register_two_skills_fetch_shared_tools_and_pending_behavior(tmp_path):
    prep = prepared(tmp_path)
    root, contribution_id = adopt_bundle(tmp_path, prep)
    registered = register_legacy_bundle(root, contribution_id, approval_verifier=approval_verifier())
    assert registered["ok"], registered
    assert len(registered["converted_skills"]) == 2
    assert registered["behavior_verification"] == "pending"
    catalog = XRefCatalog.build(root)
    documents = []
    for unit in registered["migration"]["remaining"]:
        for receipt in unit["retrievals"]:
            documents.append(catalog.get_document_by_xid(receipt["xid"]))
    record_mcp_retrieval(root, documents)
    assert migration_context(root)["status"] == "in_progress"
    for skill in registered["converted_skills"]:
        selected = catalog.get_skill(skill["skill_id"])
        assert selected["client_resources"]["namespace"] == "legacy-fixture"
        assert "materialized bundle root" in selected["skill_content"]
    manifest = catalog.get_legacy_resource_manifest("legacy-fixture")
    cache = materialize_legacy_resources(manifest,
        lambda path: (root / "tools/legacy-fixture" / path).read_bytes(), tmp_path / "separate-client-cache",
        expected_manifest_hash=registered["client_resources"]["manifest_hash"])
    result = subprocess.run([sys.executable, "-B", "tools/report.py"], cwd=cache,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0 and result.stdout.strip() == "5"
    # Observed fixture behavior does not satisfy migration's business expectations.
    assert migration_context(root)["status"] == "in_progress"
    again = register_legacy_bundle(root, contribution_id, approval_verifier=approval_verifier())
    assert again["converted_skills"] == registered["converted_skills"]


def test_no_adoption_proof_tamper_and_fake_completed_workflow_rejected(tmp_path):
    prep = prepared(tmp_path)
    root, contribution_id = adopt_bundle(tmp_path, prep)
    with pytest.raises((RuntimeError, ValueError)):
        register_legacy_bundle(root, contribution_id, approval_verifier=None)
    with pytest.raises(ValueError, match="work item|Closure Gate|Skill Load Gate"):
        register_legacy_bundle(root, contribution_id, approval_verifier=approval_verifier(),
                               verification_workflow="## Closure Gate\n- status: `done`\n")
    adopted = root / "tools/legacy-fixture/tools/report.py"
    adopted.write_text("print('tampered')", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        register_legacy_bundle(root, contribution_id, approval_verifier=approval_verifier())
    assert not (root / "skills").exists()


def test_single_root_skill_and_unsupported_sources(tmp_path):
    source_root = tmp_path / "root-skill"
    source_root.mkdir()
    (source_root / "SKILL.md").write_text("# Root Skill\n", encoding="utf-8")
    (source_root / "helper.py").write_text("pass\n", encoding="utf-8")
    prepared_result = prepare_legacy_bundle(source_root, tmp_path / "out", skills=["."], resources=[])
    assert prepared_result["manifest"]["skills"][0]["source"] == "."
    with pytest.raises(ValueError, match="non-overlapping"):
        prepare_legacy_bundle(source_root, source_root / "out", skills=["."], resources=[])


@pytest.mark.parametrize("extra", ["skills/one/SKILL.v1.md", "knowledge/unapproved.md"])
def test_registration_rejects_unapproved_extra_files(tmp_path, extra):
    root, contribution_id = adopt_bundle(tmp_path, prepared(tmp_path))
    path = root / "tools/legacy-fixture" / extra
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Unapproved\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unapproved files"):
        register_legacy_bundle(root, contribution_id, approval_verifier=approval_verifier())
    assert not (root / "skills").exists()


def test_completion_uses_existing_closed_workflow_and_rejects_changed_criteria(tmp_path):
    from test_skill_runtime_audit import SkillRuntimeAuditTests
    from xrefkit.mcp.legacy_migration import _verification_errors

    prep = prepared(tmp_path)
    root, contribution_id = adopt_bundle(tmp_path, prep)
    registered = register_legacy_bundle(root, contribution_id, approval_verifier=approval_verifier())
    fixture_root = tmp_path / "test-only-workflow"
    fixture_root.mkdir()
    log = SkillRuntimeAuditTests()._write_closed_skill_run(fixture_root)
    tasks = bind_migration_tasks(log, prep["manifest_hash"])
    # This is solely a deterministic runtime fixture, not real business approval.
    assert _verification_errors(log.read_text(encoding="utf-8"), prep["manifest_hash"])
    for task in tasks:
        code, output = command("skill", "workitem", "--log", str(log), "--item", task["item_id"],
            "--status", "done", "--role", "sample_skill:executor", "--text", "TEST ONLY completed criterion fixture",
            "--completion-criterion", task["completion_criterion"])
        assert code == 0, output
    assert command("skill", "close", "--log", str(log))[0] == 0
    record = log.read_text(encoding="utf-8")
    assert not _verification_errors(record, prep["manifest_hash"])
    altered = record.replace(tasks[0]["completion_criterion"], "weaker invented criterion")
    assert any("criterion differs" in error for error in _verification_errors(altered, prep["manifest_hash"]))
    # A completed process record still does not replace MCP retrieval receipts.
    result = register_legacy_bundle(root, contribution_id, approval_verifier=approval_verifier(), verification_workflow=record)
    assert result["migration"]["status"] == "in_progress"
    catalog = XRefCatalog.build(root)
    record_mcp_retrieval(root, [catalog.get_document_by_xid(receipt["xid"])
        for unit in registered["migration"]["remaining"] for receipt in unit["retrievals"]])
    assert migration_context(root)["status"] == "completed"
    (root / "tools/legacy-fixture/tools/shared.py").write_text("changed", encoding="utf-8")
    assert migration_context(root)["status"] == "in_progress"


def test_http_upload_adopt_register_fetch_from_client_only_source(tmp_path):
    """Real HTTP ingress/distribution, distinct source/server/cache filesystems."""
    import os
    import socket
    import time
    import urllib.request
    from xrefkit.mcp.bootstrap import http_post_json, parse_jsonrpc_response
    from xrefkit.mcp.legacy_guidance import fetch_legacy_bundle
    from test_contribution_returns import APPROVAL_SECRET, approval_assertion

    pytest.importorskip("mcp")
    prep = prepared(tmp_path)
    server = tmp_path / "http-server"
    server.mkdir()
    adoption_repo(server)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    endpoint = f"http://127.0.0.1:{port}/mcp"
    environment = {**os.environ, "XREFKIT_CONTRIBUTION_APPROVAL_SECRET": APPROVAL_SECRET}
    with (tmp_path / "http.log").open("w", encoding="utf-8") as log:
        proc = subprocess.Popen([sys.executable, "-m", "xrefkit", "mcp", "serve", "--repo", str(server),
            "--transport", "streamable-http", "--host", "127.0.0.1", "--port", str(port),
            "--profile", "admin", "--enable-inbound-webdav"], stdout=log, stderr=log, env=environment)
        try:
            deadline = time.monotonic() + 20
            while True:
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=.1):
                        break
                except OSError:
                    if proc.poll() is not None or time.monotonic() > deadline:
                        pytest.fail((tmp_path / "http.log").read_text(encoding="utf-8"))
                    time.sleep(.05)
            raw, headers = http_post_json(endpoint, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "migration-test", "version": "1"}}}, None)
            assert "result" in parse_jsonrpc_response(raw)
            session_headers = {"mcp-session-id": headers["mcp-session-id"]}
            http_post_json(endpoint, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, None, session_headers)
            request_id = 1

            def call(name, arguments=None):
                nonlocal request_id
                request_id += 1
                raw, _ = http_post_json(endpoint, {"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
                    "params": {"name": name, "arguments": arguments or {}}}, None, session_headers)
                result = parse_jsonrpc_response(raw)["result"]
                assert not result.get("isError"), result
                return result.get("structuredContent") or json.loads(result["content"][0]["text"])

            call("get_startup_context")
            skill = call("get_skill", {"skill_id": "legacy_flow_skill_migration"})
            call("bind_skill_run", {"run_id": str(uuid.uuid4()), "skill_id": skill["skill_id"]})
            issued = call("create_contribution_upload_session")
            auth = {"Authorization": "Bearer " + issued["bearer_token"]}
            bundle = Path(prep["bundle"])
            directories = sorted({str(Path(row["path"]).parent).replace("\\", "/") for row in prep["upload"]["files"] if str(Path(row["path"]).parent) != "."}, key=lambda path: (path.count("/"), path))
            all_dirs = set()
            for directory in directories:
                parts = directory.split("/")
                for count in range(1, len(parts) + 1):
                    path = "/".join(parts[:count])
                    if path not in all_dirs:
                        with urllib.request.urlopen(urllib.request.Request(issued["webdav_url"] + "/" + path, method="MKCOL", headers=auth)) as response:
                            assert response.status == 201
                        all_dirs.add(path)
            for row in prep["upload"]["files"]:
                with urllib.request.urlopen(urllib.request.Request(issued["webdav_url"] + "/" + row["path"],
                        data=(bundle / row["path"]).read_bytes(), method="PUT", headers={**auth, "If-None-Match": "*"})) as response:
                    assert response.status == 201
            contribution_id = str(uuid.uuid4())
            sealed = call("seal_contribution_upload", {"upload_id": issued["upload_id"], "contribution_id": contribution_id,
                "kind": "deterministic_tool", "title": "Test migration", "summary": "Test-only isolated migration fixture",
                "expected_files": prep["upload"]["files"], "skill_content_hash": hashlib.sha256(skill["skill_content"].encode()).hexdigest(),
                "package_id": skill["package_id"], "deterministic_tool": prep["upload"]["deterministic_tool"],
                "proposed_target_path": "tools/legacy-http"})
            assert sealed["status"] == "pending_review"
            decision_id = str(uuid.uuid4())
            reviewer = "human:test-fixture"
            assertion = approval_assertion(server, contribution_id, decision_id=decision_id, decision="accepted",
                reviewer=reviewer, approved_target_path="tools/legacy-http")
            review = call("review_contribution_return", {"contribution_id": contribution_id, "decision_id": decision_id,
                "decision": "accepted", "reviewer": reviewer, "decision_evidence": "Test-only reviewed fixture",
                "approved_target_path": "tools/legacy-http", "approval_assertion": assertion})
            call("adopt_contribution_return", {"contribution_id": contribution_id, "adoption_id": str(uuid.uuid4()),
                "reviewer": reviewer, "decision_evidence": "Test-only adoption", "approval_token": review["approval_token"]})
            registered = call("register_legacy_bundle", {"contribution_id": contribution_id})
            assert registered["ok"], registered
            skill_id = registered["converted_skills"][0]["skill_id"]
            fetched = asyncio.run(fetch_legacy_bundle(endpoint, skill_id, "legacy-http",
                registered["client_resources"]["manifest_hash"], tmp_path / "clean-client-cache"))
            result = subprocess.run([sys.executable, "-B", "tools/report.py"], cwd=fetched["cache_root"], capture_output=True, text=True)
            assert result.returncode == 0 and result.stdout.strip() == "5"
            again = asyncio.run(fetch_legacy_bundle(endpoint, skill_id, "legacy-http",
                registered["client_resources"]["manifest_hash"], tmp_path / "clean-client-cache"))
            assert again["cache_root"] == fetched["cache_root"]
            assert call("get_startup_context")["legacy_migration"]["status"] == "in_progress"
        finally:
            proc.terminate()
            proc.wait(timeout=10)
