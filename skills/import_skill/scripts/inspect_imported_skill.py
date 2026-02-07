#!/usr/bin/env python3
"""Inspect imported skill content for malicious or risky instructions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT_EXTENSIONS = {
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".bat",
    ".cmd",
    ".py",
    ".js",
    ".ts",
    ".rb",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    rule_id: str
    message: str
    file: str
    line: int
    snippet: str


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect imported skill content.")
    parser.add_argument("skill_dir", help="Path to extracted skill directory")
    parser.add_argument(
        "--policy",
        default=str(Path(__file__).resolve().parent.parent / "policy" / "inspection_rules.yaml"),
        help="Path to policy file (YAML-compatible JSON)",
    )
    parser.add_argument("--repo", default=None, help="Source repo in owner/repo format")
    parser.add_argument("--ref", default=None, help="Source ref (branch/tag/commit)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args(argv)


def load_policy(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Policy file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Policy parse error: {path}: {exc}") from exc


def iter_text_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() in {".md", ".txt", ".py", ".sh", ".ps1", ".bat", ".cmd", ".js", ".ts", ".rb"}:
            files.append(path)
    return files


def classify_target(path: Path, skill_root: Path) -> str:
    rel = path.relative_to(skill_root).as_posix()
    if rel == "SKILL.md":
        return "skill_md"
    if path.suffix.lower() in SCRIPT_EXTENSIONS or rel.startswith("scripts/"):
        return "script"
    return "other"


def find_matches(pattern: str, text: str) -> list[tuple[int, str]]:
    regex = re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE)
    matches: list[tuple[int, str]] = []
    for m in regex.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        snippet = text[m.start() : m.end()].replace("\n", " ").strip()
        snippet = snippet[:180]
        matches.append((line, snippet))
    return matches


def is_sha(ref: str | None) -> bool:
    if not ref:
        return False
    return bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", ref.strip()))


def check_trust(policy: dict, repo: str | None, ref: str | None) -> list[Finding]:
    findings: list[Finding] = []
    trust = policy.get("trust", {})
    allowed_owners = set(trust.get("allowed_owners", []))

    if repo:
        owner = repo.split("/", 1)[0] if "/" in repo else repo
        if allowed_owners and owner not in allowed_owners:
            findings.append(
                Finding(
                    severity="warn",
                    rule_id="untrusted-owner",
                    message=f"Repo owner '{owner}' is not in allowlist.",
                    file="-",
                    line=1,
                    snippet=repo,
                )
            )

    if bool(trust.get("require_sha_pinning", False)) and not is_sha(ref):
        findings.append(
            Finding(
                severity="warn",
                rule_id="ref-not-pinned",
                message="Source ref is not a commit SHA.",
                file="-",
                line=1,
                snippet=str(ref or ""),
            )
        )
    return findings


def inspect(skill_dir: Path, policy: dict, repo: str | None, ref: str | None) -> list[Finding]:
    findings: list[Finding] = []
    rules = policy.get("rules", [])
    files = iter_text_files(skill_dir)

    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        target = classify_target(path, skill_dir)
        rel = path.relative_to(skill_dir).as_posix()
        for rule in rules:
            targets = set(rule.get("targets", []))
            if targets and target not in targets:
                continue
            pattern = str(rule.get("pattern", "")).strip()
            if not pattern:
                continue
            for line, snippet in find_matches(pattern, text):
                findings.append(
                    Finding(
                        severity=str(rule.get("severity", "warn")),
                        rule_id=str(rule.get("id", "unknown-rule")),
                        message=str(rule.get("message", "")),
                        file=rel,
                        line=line,
                        snippet=snippet,
                    )
                )

    findings.extend(check_trust(policy, repo=repo, ref=ref))
    return findings


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    skill_dir = Path(args.skill_dir).resolve()
    policy_path = Path(args.policy).resolve()

    if not skill_dir.is_dir():
        print(f"Error: skill directory not found: {skill_dir}", file=sys.stderr)
        return 2

    try:
        policy = load_policy(policy_path)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    findings = inspect(skill_dir, policy, repo=args.repo, ref=args.ref)
    blocks = [f for f in findings if f.severity.lower() == "block"]
    warns = [f for f in findings if f.severity.lower() == "warn"]

    payload = {
        "ok": (len(blocks) == 0) and (len(warns) == 0 or not args.strict),
        "summary": {"block": len(blocks), "warn": len(warns), "total": len(findings)},
        "strict": bool(args.strict),
        "findings": [f.__dict__ for f in findings],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"block: {len(blocks)}")
        print(f"warn: {len(warns)}")
        print(f"total: {len(findings)}")
        for f in findings[:50]:
            print(f"- [{f.severity}] {f.rule_id} {f.file}:{f.line} {f.message}")
            if f.snippet:
                print(f"  snippet: {f.snippet}")
        if len(findings) > 50:
            print(f"... +{len(findings) - 50} more")

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
