from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

# Deterministic, machine-only diff-content checks for the Agent Diff Review Gate.
# See knowledge/organization/180_agent_diff_review_gate_design.md (xid 7A2F4C8D1801).
#
# These checks are a forced-attention trigger, not a correctness judgment.
# They run with no LLM and are decoupled from the producer context: a clean
# result is a precondition for a `proceed` verdict, never a proof of correctness.

# block  -> hard condition; gate verdict must be `blocked`
# review -> must be looked at; gate verdict must be at least `needs-review`
DISPOSITION_BLOCK = "block"
DISPOSITION_REVIEW = "review"

# Aggregate eval verdicts. `clean` is the only state that lets the gate reach
# `proceed`; it still does not prove correctness.
EVAL_CLEAN = "clean"
EVAL_NEEDS_REVIEW = "needs-review"
EVAL_BLOCKED = "blocked"


TEST_PATH_PATTERNS = (
    "*test*.cs",
    "*tests.cs",
    "test_*.py",
    "*_test.py",
    "*.spec.ts",
    "*.test.ts",
    "*.spec.js",
    "*.test.js",
)
TEST_PATH_SEGMENTS = ("test", "tests", "__tests__", "spec")

# Removed test declarations (on `-` lines) signal a deleted test.
TEST_DECL_RE = re.compile(
    r"\[\s*Fact\b|\[\s*Theory\b|\[\s*Test\b|\[\s*TestMethod\b"
    r"|\bdef\s+test_\w+|\bit\s*\(|\btest\s*\(|\bdescribe\s*\("
)

# Added lines that disable or neuter a test.
TEST_DISABLE_RES = (
    re.compile(r"\[\s*Fact\s*\(\s*Skip\s*="),
    re.compile(r"\[\s*Theory\s*\(\s*Skip\s*="),
    re.compile(r"\[\s*Ignore\b"),
    re.compile(r"@pytest\.mark\.skip\b"),
    re.compile(r"@pytest\.mark\.xfail\b"),
    re.compile(r"@unittest\.skip\b"),
    re.compile(r"\b(?:xit|xdescribe)\s*\("),
    re.compile(r"\b(?:it|describe|test)\.skip\s*\("),
    re.compile(r"Assert\.True\s*\(\s*true\s*\)", re.IGNORECASE),
    re.compile(r"Assert\.IsTrue\s*\(\s*true\s*\)", re.IGNORECASE),
)

# Schema / migration change signals: by path or by added DDL statements.
MIGRATION_PATH_PATTERNS = (
    "*/migrations/*",
    "*/migration/*",
    "*.sql",
    "*.edmx",
    "*schema*.sql",
    "*_migration.*",
)
DDL_RE = re.compile(
    r"\b(?:ALTER\s+TABLE|CREATE\s+TABLE|DROP\s+TABLE|ADD\s+COLUMN|DROP\s+COLUMN"
    r"|RENAME\s+COLUMN|ALTER\s+COLUMN|CREATE\s+INDEX|DROP\s+INDEX)\b",
    re.IGNORECASE,
)

# Secret / credential leakage on added lines.
SECRET_RES = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("connection_string", re.compile(r"(?:Server|Data Source)\s*=.*?(?:Password|Pwd)\s*=", re.IGNORECASE)),
    ("password_assignment", re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*[\"']?[^\s\"']{6,}", re.IGNORECASE)),
    ("api_token", re.compile(r"\b(?:api[_-]?key|api[_-]?token|access[_-]?token|secret[_-]?key)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{16,}", re.IGNORECASE)),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9_\-\.]{20,}")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
)

# Placeholder values that should not be flagged as real secrets.
SECRET_PLACEHOLDER_RE = re.compile(
    r"(?:xxx+|\.\.\.|<[^>]+>|\$\{[^}]+\}|example|changeme|placeholder|dummy|your[_-]?\w+|redacted|\*\*\*)",
    re.IGNORECASE,
)


@dataclass
class DiffFile:
    path: str
    status: str  # added | deleted | modified | renamed
    added: list[tuple[int, str]] = field(default_factory=list)  # (new line no, text)
    removed: list[str] = field(default_factory=list)
    old_path: str | None = None


@dataclass
class Finding:
    check: str
    disposition: str
    path: str
    line: int | None
    evidence: str

    def to_dict(self) -> dict[str, object]:
        return {
            "check": self.check,
            "disposition": self.disposition,
            "path": self.path,
            "line": self.line,
            "evidence": self.evidence,
        }


def _read_diff_text(args) -> tuple[str | None, str | None]:
    """Return (diff_text, error)."""
    if args.diff:
        if args.diff == "-":
            import sys

            return sys.stdin.read(), None
        p = Path(args.diff)
        if not p.is_file():
            return None, f"diff file not found: {args.diff}"
        return p.read_text(encoding="utf-8", errors="replace"), None

    cmd = ["git", "-C", args.root, "diff", "--no-color", "--unified=3"]
    if args.staged:
        cmd.append("--cached")
    if args.base:
        cmd.append(args.base)
    try:
        out = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return None, "git not found; pass --diff to supply a unified diff file"
    if out.returncode != 0:
        return None, f"git diff failed: {out.stderr.strip()}"
    return out.stdout, None


def parse_unified_diff(text: str) -> list[DiffFile]:
    files: list[DiffFile] = []
    cur: DiffFile | None = None
    new_lineno = 0
    pending_status = "modified"
    old_path: str | None = None
    rename_from: str | None = None
    for raw in text.splitlines():
        if raw.startswith("diff --git"):
            cur = None
            pending_status = "modified"
            old_path = None
            rename_from = None
            continue
        if raw.startswith("new file mode"):
            pending_status = "added"
            continue
        if raw.startswith("deleted file mode"):
            pending_status = "deleted"
            continue
        if raw.startswith("rename from "):
            pending_status = "renamed"
            rename_from = raw[len("rename from "):].strip()
            continue
        if raw.startswith("rename to "):
            pending_status = "renamed"
            rename_to = raw[len("rename to "):].strip()
            cur = DiffFile(path=rename_to, status="renamed", old_path=rename_from)
            files.append(cur)
            continue
        if raw.startswith("rename "):
            pending_status = "renamed"
            continue
        if raw.startswith("--- "):
            old_path = raw[4:].strip()
            if old_path.startswith("a/"):
                old_path = old_path[2:]
            continue
        if raw.startswith("+++ "):
            path = raw[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            if path == "/dev/null":
                # Deleted files have no new path; retain the old path for gates.
                pending_status = "deleted"
                path = old_path or "(deleted)"
            cur = DiffFile(path=path, status=pending_status, old_path=old_path if pending_status == "deleted" else None)
            files.append(cur)
            continue
        if raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            new_lineno = int(m.group(1)) if m else 0
            continue
        if cur is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            cur.added.append((new_lineno, raw[1:]))
            new_lineno += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            cur.removed.append(raw[1:])
        elif raw.startswith(" "):
            new_lineno += 1
    return files


def _is_test_path(path: str) -> bool:
    low = path.lower()
    name = low.rsplit("/", 1)[-1]
    if any(fnmatch.fnmatch(name, pat) for pat in TEST_PATH_PATTERNS):
        return True
    return any(seg in low.split("/") for seg in TEST_PATH_SEGMENTS)


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    low = path.lower()
    return any(fnmatch.fnmatch(low, pat) for pat in patterns)


def check_removed_tests(files: list[DiffFile]) -> list[Finding]:
    out: list[Finding] = []
    for f in files:
        source_path = f.old_path or f.path
        if f.status == "deleted" and _is_test_path(source_path):
            out.append(Finding("test_removed", DISPOSITION_REVIEW, source_path, None, "test file deleted"))
            continue
        if f.status == "renamed" and _is_test_path(source_path) and not _is_test_path(f.path):
            out.append(Finding("test_removed", DISPOSITION_REVIEW, source_path, None, f"test file renamed to {f.path}"))
            continue
        if not _is_test_path(f.path):
            continue
        for text in f.removed:
            if TEST_DECL_RE.search(text):
                out.append(Finding("test_removed", DISPOSITION_REVIEW, f.path, None, text.strip()[:160]))
    return out


def check_disabled_tests(files: list[DiffFile]) -> list[Finding]:
    out: list[Finding] = []
    for f in files:
        for lineno, text in f.added:
            for rx in TEST_DISABLE_RES:
                if rx.search(text):
                    out.append(Finding("test_disabled", DISPOSITION_REVIEW, f.path, lineno, text.strip()[:160]))
                    break
    return out


def check_schema_migration(files: list[DiffFile]) -> list[Finding]:
    out: list[Finding] = []
    for f in files:
        if _matches_any(f.path, MIGRATION_PATH_PATTERNS):
            out.append(Finding("schema_migration", DISPOSITION_REVIEW, f.path, None, f"migration/schema path ({f.status})"))
            continue
        for lineno, text in f.added:
            if DDL_RE.search(text):
                out.append(Finding("schema_migration", DISPOSITION_REVIEW, f.path, lineno, text.strip()[:160]))
                break
    return out


def check_out_of_scope(files: list[DiffFile], scope: list[str]) -> list[Finding]:
    if not scope:
        return []
    out: list[Finding] = []
    for f in files:
        low = f.path.lower()
        if not any(fnmatch.fnmatch(low, pat.lower()) for pat in scope):
            out.append(Finding("out_of_scope", DISPOSITION_REVIEW, f.path, None, "changed file outside declared scope"))
    return out


def check_secret_leak(files: list[DiffFile]) -> list[Finding]:
    out: list[Finding] = []
    for f in files:
        for lineno, text in f.added:
            for name, rx in SECRET_RES:
                if rx.search(text) and not SECRET_PLACEHOLDER_RE.search(text):
                    out.append(Finding(f"secret_leak:{name}", DISPOSITION_BLOCK, f.path, lineno, text.strip()[:120]))
                    break
    return out


def run_evals(files: list[DiffFile], scope: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    findings += check_removed_tests(files)
    findings += check_disabled_tests(files)
    findings += check_schema_migration(files)
    findings += check_out_of_scope(files, scope)
    findings += check_secret_leak(files)
    return findings


def aggregate(findings: list[Finding]) -> str:
    if any(f.disposition == DISPOSITION_BLOCK for f in findings):
        return EVAL_BLOCKED
    if findings:
        return EVAL_NEEDS_REVIEW
    return EVAL_CLEAN


def cmd_gate(args) -> int:
    if args.gate_cmd != "eval":
        return 2

    if getattr(args, "profile", None) == "command-cutover-readiness":
        return _command_cutover_readiness(args)

    text, err = _read_diff_text(args)
    if err is not None:
        result = {"ok": False, "errors": [err], "eval_verdict": EVAL_BLOCKED, "findings": []}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"error: {err}")
        return 1

    files = parse_unified_diff(text or "")
    scope = list(args.scope or [])
    findings = run_evals(files, scope)
    verdict = aggregate(findings)

    result = {
        "ok": True,
        "errors": [],
        "eval_verdict": verdict,
        "files_changed": len(files),
        "scope": scope,
        "findings": [f.to_dict() for f in findings],
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"eval_verdict: {verdict}")
        print(f"files_changed: {len(files)}")
        if scope:
            print(f"scope: {' '.join(scope)}")
        if not findings:
            print("findings: none (clean; precondition for proceed met, not proof of correctness)")
        else:
            print(f"findings: {len(findings)}")
            for f in findings:
                loc = f"{f.path}:{f.line}" if f.line else f.path
                print(f"  [{f.disposition}] {f.check} @ {loc}")
                print(f"      {f.evidence}")

    # Non-zero exit when the diff cannot proceed to CI, so the gate can run in
    # scripts and pre-CI hooks.
    if verdict != EVAL_CLEAN:
        return 1
    return 0


def _command_cutover_readiness(args) -> int:
    root = Path(args.root).resolve()
    checks = [
        ("package_manifest", (root / "pyproject.toml").is_file()),
        ("instance_manifest", (root / "xrefkit.toml").is_file()),
        ("base_generation_pointer", (root / "xrefkit/resources/base/current.json").is_file()),
        ("compiled_contract", (root / "xrefkit/resources/base/contracts.json").is_file()),
        ("compiled_model_body", (root / "xrefkit/resources/base/model_body.md").is_file()),
        ("tool_contracts", (root / "tools/contracts.yaml").is_file()),
        ("target_catalog", (root / "knowledge/source_analysis/source_structure_catalog.yaml").is_file()),
        ("integrated_mcp", (root / "xrefkit/mcp/server.py").is_file()),
        ("site_builder", (root / "tools/site_build.py").is_file()),
        ("site_manifest", (root / "site/source_manifest.json").is_file()),
    ]
    failed = [name for name, ok in checks if not ok]
    authority = "missing"
    instance_path = root / "xrefkit.toml"
    if instance_path.is_file():
        match = re.search(
            r'^command_authority\s*=\s*"([^"]+)"',
            instance_path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        authority = match.group(1) if match else "missing"
    if authority != "legacy_authoritative":
        failed.append("legacy_authority_entry_state")

    inputs = sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts)
        and (
            path.name in {"pyproject.toml", "xrefkit.toml", "contracts.yaml", "source_manifest.json"}
            or "xrefkit" in path.parts
            or path.suffix in {".yaml", ".yml"}
        )
    )
    digest = hashlib.sha256()
    for relative in inputs:
        digest.update(relative.encode("utf-8"))
        digest.update((root / relative).read_bytes())
    result = {
        "ok": not failed,
        "profile": "command-cutover-readiness",
        "entry_authority": authority,
        "checks": [{"id": name, "ok": ok} for name, ok in checks],
        "failed": failed,
        "evidence_hash": digest.hexdigest(),
        "input_count": len(inputs),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"profile: {result['profile']}")
        print(f"readiness: {'passed' if result['ok'] else 'failed'}")
        print(f"evidence_hash: {result['evidence_hash']}")
        for name in failed:
            print(f"- failed: {name}")
    return 0 if result["ok"] else 1
