"""Local host integration checks use simulated subprocess/UI, never real approval."""
import copy
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from test_governance_entry import case, host_receipt, HOST_KEY
from test_subagent_startup import startup
from xrefkit.governance_entry import digest, validate_result
from xrefkit.mcp.contribution_adoption import HmacHumanApprovalVerifier
from xrefkit import governance_host as host


@pytest.fixture
def local(case, monkeypatch):
    root, packet, _ = case
    packet_file = root / "work/packet.json"
    packet_file.write_text(json.dumps(packet))
    receipt = host_receipt(root, packet)
    receipt_file = root / "work/receipt.json"
    receipt_file.write_text(json.dumps(receipt))
    state_file = root / "authority.dpapi"
    state = {"schema": "xrefkit.local_host_authority/v1", "root": str(root),
             "packet_hash": packet["packet_hash"], "receipt_hash": digest(receipt),
             "host_secret": HOST_KEY, "applied": False}
    monkeypatch.setattr(host, "_load_state", lambda path: copy.deepcopy(state))
    monkeypatch.setattr(host, "_save_state", lambda path, value, **kwargs: state.update(value))
    return root, packet, packet_file, receipt_file, state_file, state


def test_native_decline_never_applies_or_issues_human_secret(local, monkeypatch):
    root, _, packet, receipt, state_file, state = local
    monkeypatch.setattr(host, "_review_dialog", lambda *args: False)
    result = host.apply_local(root, packet, receipt, state_file, root / "work/reflection.json")
    assert result["status"] == "human_declined_no_application"
    assert not (root / "knowledge/item.md").exists()
    assert "human_secret" not in state and not state["applied"]


def test_native_action_applies_with_separate_keys_and_stale_replay_refuses(local, monkeypatch):
    root, _, packet, receipt, state_file, state = local
    observed = []
    monkeypatch.setattr(host, "_review_dialog", lambda *args: observed.append(args) or True)
    result = host.apply_local(root, packet, receipt, state_file, root / "work/reflection.json")
    assert result["runtime_activation"] == "not_performed"
    assert observed[0][0] == "knowledge/item.md" and "+# New" in observed[0][2]
    assert state["human_secret"] != state["host_secret"]
    assert (root / "knowledge/item.md").read_bytes() == (root / "work/candidate.md").read_bytes()
    with pytest.raises(ValueError, match="unapplied dispatch"):
        host.apply_local(root, packet, receipt, state_file, root / "work/replay.json")


@pytest.mark.parametrize("mutation", ["candidate", "target"])
def test_change_during_dialog_refuses_even_after_ui_accepts(local, monkeypatch, mutation):
    root, _, packet, receipt, state_file, state = local
    def change(*args):
        path = root / ("work/candidate.md" if mutation == "candidate" else "knowledge/item.md")
        path.parent.mkdir(exist_ok=True)
        path.write_text("external change")
        return True
    monkeypatch.setattr(host, "_review_dialog", change)
    with pytest.raises(ValueError, match="changed"):
        host.apply_local(root, packet, receipt, state_file, root / "work/reflection.json")
    assert not state["applied"]
    if mutation == "target":
        assert (root / "knowledge/item.md").read_text() == "external change"


@pytest.mark.parametrize("field", ["packet_hash", "receipt_hash", "root"])
def test_wrong_dispatch_state_rejected_before_dialog(local, monkeypatch, field):
    root, _, packet, receipt, state_file, state = local
    state[field] = "wrong"
    monkeypatch.setattr(host, "_review_dialog", lambda *args: pytest.fail("UI must not open"))
    with pytest.raises(ValueError, match="does not match"):
        host.apply_local(root, packet, receipt, state_file, root / "work/reflection.json")


def test_failed_gate_cannot_be_human_approved(local, monkeypatch):
    root, packet, packet_file, receipt_file, state_file, state = local
    receipt = host_receipt(root, packet, failed=True)
    receipt_file.write_text(json.dumps(receipt))
    state["receipt_hash"] = digest(receipt)
    monkeypatch.setattr(host, "_review_dialog", lambda *args: pytest.fail("UI must not open"))
    with pytest.raises(ValueError, match="failed or unknown"):
        host.apply_local(root, packet_file, receipt_file, state_file, root / "work/reflection.json")


def test_tampered_signature_refused_even_with_matching_receipt_digest(local, monkeypatch):
    root, _, packet, receipt_file, state_file, state = local
    receipt = json.loads(receipt_file.read_text())
    receipt["signature"] = "wrong"
    receipt_file.write_text(json.dumps(receipt))
    state["receipt_hash"] = digest(receipt)
    monkeypatch.setattr(host, "_review_dialog", lambda *args: pytest.fail("UI must not open"))
    with pytest.raises(ValueError, match="signature"):
        host.apply_local(root, packet, receipt_file, state_file, root / "work/reflection.json")


def test_evidence_destination_cannot_overwrite_packet(local, monkeypatch):
    root, _, packet, receipt, state_file, _ = local
    monkeypatch.setattr(host, "_review_dialog", lambda *args: pytest.fail("UI must not open"))
    with pytest.raises(ValueError, match="overwrite"):
        host.apply_local(root, packet, receipt, state_file, packet)


@pytest.mark.parametrize("events", [[], [{"type": "thread.started", "thread_id": "x"}],
    [{"type": "thread.started", "thread_id": "x"}, {"type": "turn.failed"}],
    [{"type": "thread.started", "thread_id": "x"}, {"type": "turn.completed"}, {"type": "turn.completed"}]])
def test_missing_or_failed_terminal_events_are_not_execution(tmp_path, events):
    path = tmp_path / "events.jsonl"
    path.write_text("\n".join(json.dumps(event) for event in events))
    with pytest.raises(ValueError):
        host._completed_session(path)


def test_valid_single_completion(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"type":"thread.started","thread_id":"actual-session"}\n{"type":"turn.completed"}\n')
    assert host._completed_session(path) == "actual-session"


def test_authority_never_inherited_by_child(monkeypatch):
    monkeypatch.setenv("XREFKIT_GOVERNANCE_HOST_SECRET", "private")
    monkeypatch.setenv("XREFKIT_GOVERNANCE_HUMAN_SECRET", "private")
    monkeypatch.setenv("XREFKIT_CONTRIBUTION_APPROVAL_SECRET", "private")
    env = host._child_environment()
    assert not any(key.startswith("XREFKIT_GOVERNANCE_") for key in env)
    assert "XREFKIT_CONTRIBUTION_APPROVAL_SECRET" not in env


def test_child_open_refusal_never_dispatches(case, monkeypatch):
    root, packet, _ = case
    source = root / "work/packet.json"
    source.write_text(json.dumps(packet))
    binary = root / "codex.exe"
    binary.write_bytes(b"test fixture, never executable")
    monkeypatch.setattr(host.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(returncode=2, stdout='{"ok":false}'))
    monkeypatch.setattr(host.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("must not dispatch"))
    with pytest.raises(ValueError, match="Skill run refused"):
        host.dispatch_local(root, source, binary, root / "work/dispatch")


def test_process_failure_never_generates_host_authority(case, monkeypatch):
    root, packet, _ = case
    source = root / "work/packet.json"
    source.write_text(json.dumps(packet))
    binary = root / "codex.exe"
    binary.write_bytes(b"test fixture, never executable")
    monkeypatch.setattr(host.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(returncode=0, stdout='{"ok":true,"run_id":"opened"}'))
    process = SimpleNamespace(returncode=7, pid=123, communicate=lambda *args, **kwargs: None)
    monkeypatch.setattr(host.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(host.secrets, "token_hex", lambda *args: pytest.fail("key must not be generated"))
    with pytest.raises(ValueError, match="process failed"):
        host.dispatch_local(root, source, binary, root / "work/dispatch")


def test_no_cli_automatic_approval_option():
    with pytest.raises(SystemExit) as exc:
        host.main(["--root", ".", "apply", "--packet", "a", "--receipt", "b",
                   "--authority-state", "c", "--out", "d", "--yes"])
    assert exc.value.code == 2


def test_applied_but_authority_save_failure_carries_reflection(local, monkeypatch):
    root, _, packet, receipt, state_file, _ = local
    monkeypatch.setattr(host, "_review_dialog", lambda *args: True)
    def fail_save(*args, **kwargs):
        raise OSError("simulated authority disk failure")
    monkeypatch.setattr(host, "_save_state", fail_save)
    with pytest.raises(host.AppliedEvidenceError) as exc:
        host.apply_local(root, packet, receipt, state_file, root / "work/reflection.json")
    assert (root / "knowledge/item.md").read_bytes() == (root / "work/candidate.md").read_bytes()
    assert exc.value.reflection["target"]["path"] == "knowledge/item.md"


def test_cli_distinguishes_applied_evidence_failure(monkeypatch, capsys):
    reflection = {"target": {"path": "skills/example/SKILL.v1.md", "sha256": "observed-hash"}}
    def failed(*args):
        raise host.AppliedEvidenceError(reflection)
    monkeypatch.setattr(host, "apply_local", failed)
    code = host.main(["--root", ".", "apply", "--packet", "a", "--receipt", "b",
                      "--authority-state", "c", "--out", "d"])
    assert code == 3
    assert "observed-hash" in capsys.readouterr().out


@pytest.mark.parametrize("replace_identity", [False, True])
def test_dispatch_attests_only_actual_opened_run_and_completed_output(case, monkeypatch, replace_identity):
    root, packet, _ = case
    source = root / "work/packet.json"
    source.write_text(json.dumps(packet))
    binary = root / "codex.exe"
    binary.write_bytes(b"test fixture, never executable")
    host_receipt(root, packet)  # Test-only prepared body/closed log.
    out = root / "work/dispatch"
    state = {}
    child_path = None
    def open_run(argv, **kwargs):
        nonlocal child_path
        child_path = Path(argv[argv.index("--out") + 1])
        assert child_path.name.endswith("_skill_run_shared_asset_update_gate.md")
        text = (root / "work/child.md").read_text().replace("work/analysis.md", "work/dispatch/analysis.json")
        child_path.write_text(text)
        return SimpleNamespace(returncode=0, stdout='{"ok":true,"run_id":"child-test-run"}')
    def launch(argv, **kwargs):
        def communicate(prompt, **options):
            assert b"Do not open another run" in prompt
            (out / "analysis.json").write_bytes((root / "work/analysis.md").read_bytes())
            Path(argv[argv.index("--output-last-message") + 1]).write_text("Analysis complete")
            kwargs["stdout"].write(b'{"type":"thread.started","thread_id":"simulated-session"}\n{"type":"turn.completed"}\n')
            if replace_identity:
                child_path.write_text(child_path.read_text().replace("child-test-run", "replaced-run"))
        return SimpleNamespace(returncode=0, pid=123, communicate=communicate)
    monkeypatch.setattr(host.subprocess, "run", open_run)
    monkeypatch.setattr(host.subprocess, "Popen", launch)
    monkeypatch.setattr(host, "_state_path", lambda execution_id: root / "authority.dpapi")
    monkeypatch.setattr(host, "_save_state", lambda path, value, **kwargs: state.update(value))
    if replace_identity:
        with pytest.raises(ValueError, match="host-opened child identity"):
            host.dispatch_local(root, source, binary, out)
        assert not state and not (out / "receipt.json").exists()
    else:
        result = host.dispatch_local(root, source, binary, out)
        receipt = json.loads(Path(result["receipt"]).read_text())
        verifier = HmacHumanApprovalVerifier(state["host_secret"])
        assert validate_result(root, packet, receipt, verifier)["packet_hash"] == packet["packet_hash"]
        provenance = json.loads((out / "dispatch.json").read_text())
        verifier.verify_event(provenance["event"], provenance["signature"])
        assert provenance["event"]["thread_id"] == "simulated-session"
        assert state["host_secret"] not in (out / "receipt.json").read_text()
        assert not (root / "knowledge/item.md").exists()


@pytest.mark.skipif(host.os.name != "nt", reason="Windows operator adapter")
def test_windows_dpapi_roundtrip():
    disposable = b"non-secret disposable integration test"
    ciphertext = host._protect(disposable)
    assert ciphertext != disposable
    assert host._protect(ciphertext, decrypt=True) == disposable
