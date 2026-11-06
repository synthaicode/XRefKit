"""Local Windows host bridge; analysis, host attestation and human action stay separate.

This is an operator-controlled adapter, not protection against another process
running as the same OS user. It never accepts an imported analyst receipt or an
automatic human-approval flag. Existing governance validators own acceptance.
"""
from __future__ import annotations

import argparse
import ctypes
import difflib
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import uuid

from .governance_entry import apply_update, digest, revalidate, snapshot, validate_result
from .governance_entry_cli import _read
from .mcp.contribution_adoption import HmacHumanApprovalVerifier, issue_hmac_approval_assertion
from .skillrun import _log_field


class AppliedEvidenceError(RuntimeError):
    """The target changed successfully; retry must inspect reflection first."""

    def __init__(self, reflection: dict):
        super().__init__("canonical application completed but reflection evidence save failed")
        self.reflection = reflection


def _write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def _work_path(root: Path, path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to((root / "work").resolve()):
        raise ValueError("host evidence must remain under repository work/")
    return path


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _child_environment() -> dict[str, str]:
    # Do not pass any existing operator authority to the analyst. New host keys
    # are generated only AFTER the analyst exits, not inherited or put on disk.
    return {key: value for key, value in os.environ.items()
            if not key.upper().startswith("XREFKIT_GOVERNANCE_")
            and key.upper() != "XREFKIT_CONTRIBUTION_APPROVAL_SECRET"}


def _protect(raw: bytes, *, decrypt: bool = False) -> bytes:
    if os.name != "nt":
        raise RuntimeError("this operator adapter requires Windows DPAPI")

    class Blob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(raw)
    source = Blob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        success = crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None,
                                          1, ctypes.byref(output))
    else:
        success = crypt.CryptProtectData(ctypes.byref(source), "XRefKit governance host",
                                        None, None, None, 1, ctypes.byref(output))
    if not success:
        raise OSError("Windows authority storage failed")
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel.LocalFree(output.data)


def _state_path(execution_id: str) -> Path:
    location = os.environ.get("LOCALAPPDATA")
    if not location:
        raise RuntimeError("LOCALAPPDATA is required for operator authority storage")
    return Path(location) / "XRefKit" / "governance-host" / (execution_id + ".dpapi")


def _save_state(path: Path, state: dict, *, create: bool = True) -> None:
    raw = _protect(json.dumps(state, sort_keys=True).encode("utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    if create:
        with path.open("xb") as stream:
            stream.write(raw)
        return
    descriptor, temporary = tempfile.mkstemp(prefix=".authority-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_state(path: Path) -> dict:
    state = json.loads(_protect(path.read_bytes(), decrypt=True))
    if not isinstance(state, dict) or state.get("schema") != "xrefkit.local_host_authority/v1":
        raise ValueError("invalid local host authority")
    return state


def _completed_session(path: Path) -> str:
    started = []
    completed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event.get("type") in {"error", "turn.failed"}:
            raise ValueError("analyst stream reported failure")
        if event.get("type") == "thread.started":
            started.append(event.get("thread_id"))
        if event.get("type") == "turn.completed":
            completed += 1
    if len(started) != 1 or not isinstance(started[0], str) or not started[0] or completed != 1:
        raise ValueError("one actual completed Codex thread is required")
    return started[0]


def _prompt(packet_path: Path, child_log: Path, result: Path) -> str:
    return f"""Act only as the isolated shared_asset_update_gate analyst.
The host has already opened your correlated Skill run. Do not open another run.
Read the repository startup sources, then the selected method
skills/os/shared_asset_update_gate/SKILL.v1.md and the immutable packet:
{packet_path}
Your opened run log: {child_log}
Save the strict JSON result body (without output pointer) to: {result}
Consume only packet materials and required startup/method contracts. Do not edit
the packet, candidate, canonical target, specialist evidence, parent log or code.
Use the existing skill workitem/artifact/concern/phase/verify/close commands to
record and close your own run. Never advance check yourself; use deterministic
verify. Never sign a receipt or approve/apply a target. Record the designated
result as a done output artifact using its repository-relative path; record
evidence, explicit handoff and all concerns. Report failed/unknown findings
honestly. Successful process exit is not evidence that checks pass.
Return only a short completion message after the output and run are saved.
"""


def dispatch_local(root: Path, packet_path: Path, codex: Path, out_dir: Path,
                   *, timeout: int = 1800) -> dict:
    """Run the actual CLI child, then attest its validated, closed result."""
    root = root.resolve()
    packet_path = packet_path.resolve()
    packet = _read(str(packet_path))
    revalidate(root, packet)
    if packet["kind"] != "asset_update" or "endpoint" in packet["payload"]:
        raise ValueError("local host requires a canonical single-target asset_update packet")
    codex = codex.resolve(strict=True)
    if not codex.is_file() or codex.suffix.lower() != ".exe":
        raise ValueError("select the trusted native Codex executable, not a shell wrapper")
    out_dir = _work_path(root, out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    child = out_dir / f"{date.today().isoformat()}_skill_run_shared_asset_update_gate.md"
    output = out_dir / "analysis.json"
    final = out_dir / "last-message.txt"
    events = out_dir / "events.jsonl"
    stderr = out_dir / "stderr.log"
    binding = packet["binding"]
    command = [sys.executable, "-m", "xrefkit", "skill", "run", "--root", str(root),
               "--definition", "skills/os/shared_asset_update_gate/SKILL.v1.md",
               "--task", "Analyze frozen canonical governance packet " + packet["packet_hash"],
               "--capability", "governance analysis", "--tuning", "shared asset management",
               "--responsibility", "Analyze only the frozen common management checks without adoption",
               "--execution-mode", "subagent_required", "--parent-run-id", binding["run_id"],
               "--root-run-id", binding["run_snapshot"]["fields"]["root_run_id"],
               "--work-item-id", binding["work_item_id"], "--out", str(child), "--json"]
    opened = subprocess.run(command, cwd=root, env=_child_environment(), capture_output=True,
                            text=True, encoding="utf-8", timeout=60, check=False)
    (out_dir / "open-run.json").write_text(opened.stdout, encoding="utf-8")
    opened_record = json.loads(opened.stdout)
    if opened.returncode or not opened_record.get("ok") or not opened_record.get("run_id"):
        raise ValueError("analyst Skill run refused; inspect open-run.json")
    execution_id = str(uuid.uuid4())
    argv = [str(codex), "exec", "--json", "--color", "never", "--sandbox", "workspace-write",
            "--cd", str(root), "--output-last-message", str(final), "-"]
    before = time.time()
    with events.open("xb") as stdout, stderr.open("xb") as error:
        process = subprocess.Popen(argv, cwd=root, env=_child_environment(), stdin=subprocess.PIPE,
                                   stdout=stdout, stderr=error)
        try:
            process.communicate(_prompt(packet_path, child, output).encode("utf-8"), timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, timeout=30, check=False)
            process.kill()
            process.wait()
            raise ValueError("analyst timed out; no attestation or approval created") from None
    if process.returncode:
        raise ValueError("analyst process failed; inspect stderr.log")
    session = _completed_session(events)
    if not final.is_file() or not final.read_text(encoding="utf-8").strip():
        raise ValueError("analyst final message missing")
    revalidate(root, packet)
    if _log_field(child.read_text(encoding="utf-8"), "run_id") != opened_record["run_id"]:
        raise ValueError("analyst replaced the host-opened child identity")
    body = _read(str(output))
    if "output" in body:
        raise ValueError("analyst must not supply a host output pointer")
    result = {**body, "output": snapshot(root, _relative(root, output))}
    event = {"schema": "xrefkit.governance_execution/v1", "packet_hash": packet["packet_hash"],
             "execution_id": execution_id, "child_log": _relative(root, child),
             "child_log_hash": snapshot(root, _relative(root, child))["sha256"],
             "skill_id": "shared_asset_update_gate", "result": result, "result_hash": digest(result)}
    host_secret = secrets.token_hex(32)
    verifier = HmacHumanApprovalVerifier(host_secret)
    receipt = {"event": event, "signature": verifier.seal_event(event)}
    validate_result(root, packet, receipt, verifier)
    state_path = _state_path(execution_id)
    provenance = {"schema": "xrefkit.local_host_dispatch/v1", "execution_id": execution_id,
                  "packet_hash": packet["packet_hash"], "thread_id": session, "pid": process.pid,
                  "started_at": before, "completed_at": time.time(), "exit_code": process.returncode,
                  "executable": str(codex), "executable_sha256": hashlib.sha256(codex.read_bytes()).hexdigest(),
                  "events": snapshot(root, _relative(root, events)), "receipt_hash": digest(receipt)}
    _save_state(state_path, {"schema": "xrefkit.local_host_authority/v1", "root": str(root),
                            "packet_hash": packet["packet_hash"], "receipt_hash": digest(receipt),
                            "host_secret": host_secret, "applied": False})
    _write_new(out_dir / "receipt.json", receipt)
    _write_new(out_dir / "dispatch.json", {"event": provenance, "signature": verifier.seal_event(provenance)})
    handoff = {"receipt": str(out_dir / "receipt.json"), "authority_state": str(state_path),
               "status": "dispatched_not_approved", "human_action": "run apply and review the native dialog"}
    _write_new(out_dir / "handoff.json", handoff)
    return handoff


def _review_dialog(target: str, candidate_hash: str, difference: str) -> bool:
    # No command-line/STDIN yes path. The operator must act in this native UI.
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText

    window = tk.Tk()
    window.title("XRefKit — 正式Skillソースへの反映")
    window.geometry("1000x750")
    accepted = False
    tk.Label(window, text="次の差分を正式ソースへ反映します。成熟度・採用・配布版は変更しません。",
             anchor="w").pack(fill="x", padx=12, pady=8)
    tk.Label(window, text=f"対象: {target}\n候補 SHA-256: {candidate_hash}",
             anchor="w", justify="left", wraplength=970).pack(fill="x", padx=12)
    text = ScrolledText(window, wrap="none")
    text.insert("1.0", difference)
    text.configure(state="disabled")
    text.pack(fill="both", expand=True, padx=12, pady=12)

    def approve() -> None:
        nonlocal accepted
        accepted = True
        window.destroy()

    buttons = tk.Frame(window)
    buttons.pack(fill="x", padx=12, pady=10)
    tk.Button(buttons, text="反映せず終了", command=window.destroy).pack(side="right", padx=8)
    tk.Button(buttons, text="この差分を正式ソースへ反映", command=approve).pack(side="right", padx=8)
    window.mainloop()
    return accepted


def apply_local(root: Path, packet_path: Path, receipt_path: Path, state_path: Path,
                output: Path) -> dict:
    root = root.resolve()
    packet = _read(str(packet_path))
    receipt = _read(str(receipt_path))
    state = _load_state(state_path)
    if (state.get("root") != str(root) or state.get("packet_hash") != packet["packet_hash"]
            or state.get("receipt_hash") != digest(receipt) or state.get("applied")):
        raise ValueError("authority state does not match this unapplied dispatch")
    verifier = HmacHumanApprovalVerifier(state["host_secret"])
    result = validate_result(root, packet, receipt, verifier)
    if result["unknowns"] or any(row["result"] not in {"pass", "not_applicable"} for row in result["findings"]):
        raise ValueError("failed or unknown analysis cannot be approved")
    output = _work_path(root, output)
    protected = {packet_path.resolve(), receipt_path.resolve(), state_path.resolve(),
                 (root / packet["log"]).resolve(), (root / packet["payload"]["target"]).resolve(),
                 (root / receipt["event"]["child_log"]).resolve(),
                 *((root / row["path"]).resolve() for row in packet["materials"]),
                 (root / result["output"]["path"]).resolve()}
    if output in protected:
        raise ValueError("reflection output would overwrite governance input")
    _write_new(output, {"status": "awaiting_native_human_action"})
    target = packet["payload"]["target"]
    old_bytes = (root / target).read_bytes() if (root / target).exists() else None
    candidate = packet["payload"]["candidate"]
    new_bytes = (root / candidate).read_bytes()
    candidate_hash = next(row["sha256"] for row in packet["materials"] if row["path"] == candidate)
    if (hashlib.sha256(new_bytes).hexdigest() != candidate_hash
            or (hashlib.sha256(old_bytes).hexdigest() if old_bytes is not None else None)
            != packet["payload"]["expected_target_hash"]):
        raise ValueError("review display differs from frozen candidate or target")
    revalidate(root, packet)
    old = old_bytes.decode("utf-8") if old_bytes is not None else ""
    new = new_bytes.decode("utf-8")
    difference = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                            fromfile=target, tofile=candidate))
    if not _review_dialog(target, candidate_hash, difference):
        output.write_text('{"status":"human_declined_no_application"}\n', encoding="utf-8")
        return {"status": "human_declined_no_application"}
    # Authority is issued only after the native action, in the operator process.
    # Revalidation inside apply_update rejects changes made while the UI was open.
    human_secret = secrets.token_hex(32)
    assertion = issue_hmac_approval_assertion(human_secret, {
        "action": "apply_governed_asset", "packet_hash": packet["packet_hash"],
        "target": target, "result_hash": digest(result)})
    reflected = apply_update(root, packet, receipt, host_verifier=verifier,
                             approval_verifier=HmacHumanApprovalVerifier(human_secret),
                             approval_assertion=assertion)
    state.update({"human_secret": human_secret, "approval_assertion": assertion, "applied": True,
                  "approved_at": time.time(), "reflected_target": reflected["target"]})
    try:
        _save_state(state_path, state, create=False)
        output.write_text(json.dumps(reflected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError) as exc:
        raise AppliedEvidenceError(reflected) from exc
    return reflected


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m xrefkit.governance_host")
    parser.add_argument("--root", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("dispatch")
    start.add_argument("--packet", required=True, type=Path)
    start.add_argument("--codex", type=Path, default=os.environ.get("CODEX_APP_RUNTIME_CLI_PATH"))
    start.add_argument("--out-dir", required=True, type=Path)
    start.add_argument("--timeout", type=int, default=1800)
    apply = commands.add_parser("apply")
    apply.add_argument("--packet", required=True, type=Path)
    apply.add_argument("--receipt", required=True, type=Path)
    apply.add_argument("--authority-state", required=True, type=Path)
    apply.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "dispatch":
            if args.codex is None or args.timeout <= 0:
                raise ValueError("native Codex executable and positive timeout required")
            result = dispatch_local(args.root, args.packet, args.codex, args.out_dir, timeout=args.timeout)
        else:
            result = apply_local(args.root, args.packet, args.receipt, args.authority_state, args.out)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except AppliedEvidenceError as exc:
        print(str(exc))
        print(json.dumps(exc.reflection, ensure_ascii=False))
        return 3
    except (ValueError, OSError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(f"local governance host refused: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
