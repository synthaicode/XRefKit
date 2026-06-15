"""Deterministic error-policy locator pass (First Batch).

Implements the locators defined in
``knowledge/source_analysis/131_csharp_error_policy_locator_tiers.md`` against
the detection spec in
``knowledge/source_analysis/130_csharp_error_policy_detection_patterns.md``.

This module emits *candidates only*, per the binding boundary in 131:

- locator, not verdict (``confidence`` is always ``candidate``)
- no auto-fix, no auto-fail gate
- detected-range-only with an explicit scan-scope declaration

Enabled locator (131 First Batch):

- ``cs.err.empty_catch`` (#2) — catch block with no statements (comment-only counts)

``cs.err.throw_variable_rethrow`` (#1) has been **retired** from this custom
pass and delegated to the built-in analyzer CA2200 via the SARIF path
(``tools/collect_analyzer_sarif.py`` -> ``tools/sarif_to_locator.py``). CA2200
does true semantic rethrow analysis, so the lexical heuristic was redundant.
Empty-catch detection scrubs comments/strings and brace-matches catch blocks;
no analyzer matches the 131 empty-catch shape (comment-only + marker note), so
it stays custom. See knowledge/132 for the delegation rationale.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

GENERATED_SUFFIXES = (".g.cs", ".designer.cs")
GENERATED_DIR_PARTS = ("obj", "bin", "migrations")

# PascalCase test-file leaf, case-sensitive so "Contest.cs"/"Pretest.cs" are not test files.
_TEST_FILE_RE = re.compile(r"Tests?\.cs$")

_EMPTY_CATCH = "cs.err.empty_catch"

_ENABLED_LOCATORS = [_EMPTY_CATCH]


@dataclass
class LocatorHit:
    locator_id: str
    source_pattern_id: str
    file: str
    line: int
    column: int
    snippet: str
    tier: str
    detection_method: str
    scope_id: str
    confidence: str = "candidate"
    judgment_status: str = "unset"
    notes: str = ""


@dataclass
class ScanScope:
    scan_id: str
    included_files: list[str] = field(default_factory=list)
    excluded_generated: list[str] = field(default_factory=list)
    excluded_tests: list[str] = field(default_factory=list)
    tests_included: bool = False
    enabled_locators: list[str] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)


def _scrub(src: str) -> str:
    """Return src with comments and string/char literals blanked to spaces.

    Newlines are preserved so line/column positions still map to the original.
    """
    out: list[str] = []
    i = 0
    n = len(src)

    def blank(ch: str) -> None:
        out.append("\n" if ch == "\n" else " ")

    while i < n:
        ch = src[i]
        two = src[i : i + 2]

        if two == "//":
            while i < n and src[i] != "\n":
                blank(src[i])
                i += 1
            continue
        if two == "/*":
            while i < n and src[i : i + 2] != "*/":
                blank(src[i])
                i += 1
            for _ in range(2):
                if i < n:
                    blank(src[i])
                    i += 1
            continue
        # raw string literal, optionally interpolated: $* then a run of >=3 quotes.
        # Must precede the @/$ prefix branch so $""" / $$""" are not mis-parsed.
        dollars = 0
        while i + dollars < n and src[i + dollars] == "$":
            dollars += 1
        quote_at = i + dollars
        quote_run = 0
        while quote_at + quote_run < n and src[quote_at + quote_run] == '"':
            quote_run += 1
        if quote_run >= 3:
            closing = '"' * quote_run
            while i < quote_at + quote_run:  # blank $-prefix and opening quotes
                blank(src[i])
                i += 1
            while i < n and src[i : i + quote_run] != closing:
                blank(src[i])
                i += 1
            for _ in range(quote_run):
                if i < n:
                    blank(src[i])
                    i += 1
            continue
        if ch in "@$":
            j = i
            has_at = False
            while j < n and src[j] in "@$":
                has_at = has_at or src[j] == "@"
                j += 1
            if j < n and src[j] == '"':
                while i <= j:  # blank prefix chars and opening quote
                    blank(src[i])
                    i += 1
                if has_at:  # verbatim: "" escapes a quote
                    while i < n:
                        if src[i] == '"':
                            if i + 1 < n and src[i + 1] == '"':
                                blank(src[i])
                                blank(src[i + 1])
                                i += 2
                                continue
                            blank(src[i])
                            i += 1
                            break
                        blank(src[i])
                        i += 1
                else:  # interpolated non-verbatim: backslash escapes
                    while i < n:
                        if src[i] == "\\" and i + 1 < n:
                            blank(src[i])
                            blank(src[i + 1])
                            i += 2
                            continue
                        if src[i] == '"':
                            blank(src[i])
                            i += 1
                            break
                        if src[i] == "\n":
                            break
                        blank(src[i])
                        i += 1
                continue
        if ch == '"':
            blank(src[i])
            i += 1
            while i < n:
                if src[i] == "\\" and i + 1 < n:
                    blank(src[i])
                    blank(src[i + 1])
                    i += 2
                    continue
                if src[i] == '"':
                    blank(src[i])
                    i += 1
                    break
                if src[i] == "\n":
                    break
                blank(src[i])
                i += 1
            continue
        if ch == "'":
            blank(src[i])
            i += 1
            while i < n:
                if src[i] == "\\" and i + 1 < n:
                    blank(src[i])
                    blank(src[i + 1])
                    i += 2
                    continue
                if src[i] == "'":
                    blank(src[i])
                    i += 1
                    break
                if src[i] == "\n":
                    break
                blank(src[i])
                i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _match_pair(text: str, open_idx: int, open_ch: str, close_ch: str) -> int:
    """Return the index just past the matching close char, or len(text)."""
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _catch_blocks(scrubbed: str) -> list[tuple[int, int, int]]:
    """Return (catch_keyword_pos, body_start, body_end) for every catch block.

    Unlike _catch_scopes this includes bare ``catch`` and ``catch (Type)`` with
    no variable, because empty-catch detection does not need a variable.
    ``body_start``/``body_end`` bound the text between the braces (exclusive).
    """
    blocks: list[tuple[int, int, int]] = []
    n = len(scrubbed)
    for m in re.finditer(r"\bcatch\b", scrubbed):
        catch_pos = m.start()
        pos = m.end()
        while pos < n and scrubbed[pos].isspace():
            pos += 1
        if pos < n and scrubbed[pos] == "(":  # optional exception type clause
            pos = _match_pair(scrubbed, pos, "(", ")")
            while pos < n and scrubbed[pos].isspace():
                pos += 1
        if scrubbed[pos : pos + 4] == "when" and (  # optional exception filter
            pos + 4 >= n or not (scrubbed[pos + 4].isalnum() or scrubbed[pos + 4] == "_")
        ):
            pos += 4
            while pos < n and scrubbed[pos].isspace():
                pos += 1
            if pos < n and scrubbed[pos] == "(":
                pos = _match_pair(scrubbed, pos, "(", ")")
                while pos < n and scrubbed[pos].isspace():
                    pos += 1
        if pos < n and scrubbed[pos] == "{":
            block_end = _match_pair(scrubbed, pos, "{", "}")
            blocks.append((catch_pos, pos + 1, block_end - 1))
    return blocks


def _line_col(text: str, pos: int) -> tuple[int, int]:
    line = text.count("\n", 0, pos) + 1
    col = pos - (text.rfind("\n", 0, pos))
    return line, col


def scan_text(rel_path: str, src: str, scan_id: str) -> list[LocatorHit]:
    scrubbed = _scrub(src)
    lines = src.splitlines()

    def snippet_at(line: int) -> str:
        return lines[line - 1].strip() if 0 <= line - 1 < len(lines) else ""

    hits: list[LocatorHit] = []

    # cs.err.empty_catch — catch block with no statements (comment-only counts)
    for catch_pos, body_start, body_end in _catch_blocks(scrubbed):
        if scrubbed[body_start:body_end].strip() != "":
            continue
        # comments were scrubbed to whitespace; check the original for a marker
        has_marker = src[body_start:body_end].strip() != ""
        line, col = _line_col(scrubbed, catch_pos)
        hits.append(
            LocatorHit(
                locator_id=_EMPTY_CATCH,
                source_pattern_id="130:catch-blocks/empty-catch",
                file=rel_path,
                line=line,
                column=col,
                snippet=snippet_at(line),
                tier="T2",
                detection_method="python_scrub_block_heuristic",
                scope_id=scan_id,
                notes=(
                    "empty catch body; intentional marker (comment) present in body"
                    if has_marker
                    else "empty catch body; no intentional marker in body"
                ),
            )
        )

    hits.sort(key=lambda h: (h.line, h.column, h.locator_id))
    return hits


def _is_generated(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith(GENERATED_SUFFIXES):
        return True
    parts = {p.lower() for p in path.parts}
    return any(part in parts for part in GENERATED_DIR_PARTS)


def _is_test(path: Path) -> bool:
    dir_parts = [p.lower() for p in path.parts[:-1]]
    if any(p in {"test", "tests"} for p in dir_parts):
        return True
    if any(p.endswith((".tests", ".test")) for p in dir_parts):
        return True
    # leaf must end with a PascalCase Test/Tests token; case-sensitive avoids
    # false positives like Contest.cs / Pretest.cs / Testament.cs.
    return bool(_TEST_FILE_RE.search(path.name))


def _discover(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for p in paths:
        if p.is_dir():
            found.extend(sorted(p.rglob("*.cs")))
        elif p.suffix == ".cs":
            found.append(p)
    return found


def scan_paths(
    paths: list[Path], *, include_tests: bool = False, root: Path | None = None
) -> tuple[list[LocatorHit], ScanScope]:
    root = root or Path.cwd()
    scan_id = "scan-" + hashlib.sha1(
        (_dt.datetime.now(_dt.timezone.utc).isoformat() + repr(paths)).encode()
    ).hexdigest()[:12]
    scope = ScanScope(scan_id=scan_id, enabled_locators=list(_ENABLED_LOCATORS))
    hits: list[LocatorHit] = []
    for path in _discover(paths):
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
        if _is_generated(path):
            scope.excluded_generated.append(rel)
            continue
        if not include_tests and _is_test(path):
            scope.excluded_tests.append(rel)
            continue
        try:
            src = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            scope.parse_errors.append(f"{rel}: {exc}")
            continue
        scope.included_files.append(rel)
        hits.extend(scan_text(rel, src, scan_id))
    scope.tests_included = include_tests
    return hits, scope


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic error-policy locator (candidates only, never a verdict)"
    )
    parser.add_argument("paths", nargs="+", help="C# files or directories to scan")
    parser.add_argument("--include-tests", action="store_true", help="include test/sample projects")
    parser.add_argument("--json", action="store_true", help="emit the locator output contract as JSON")
    parser.add_argument("--root", default=None, help="root for relative paths (default: cwd)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else Path.cwd()
    paths = [Path(p).resolve() for p in args.paths]
    hits, scope = scan_paths(paths, include_tests=args.include_tests, root=root)

    if args.json:
        print(json.dumps({"scope": asdict(scope), "hits": [asdict(h) for h in hits]}, indent=2))
    else:
        print(f"scan_id: {scope.scan_id}")
        print(f"enabled locators: {', '.join(scope.enabled_locators)}")
        print(f"included files: {len(scope.included_files)}")
        print(f"excluded generated: {len(scope.excluded_generated)}")
        print(f"excluded tests: {len(scope.excluded_tests)}")
        print(f"tests included: {scope.tests_included}")
        if scope.parse_errors:
            print(f"parse errors: {len(scope.parse_errors)}")
        print(f"candidates (NOT verdicts): {len(hits)}")
        for h in hits:
            print(f"  [{h.locator_id}] {h.file}:{h.line}:{h.column}  {h.snippet}")

    # candidates are never an error: locator does not auto-fail the build
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
