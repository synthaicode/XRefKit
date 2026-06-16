"""Surface DRY / common-processing candidates from existing C# at design time.

The semantic commonality signals in
``knowledge/packs/constraint-derivation/180_commonality_derivation_signals.md``
are judgment-bound (an AI reads the code and decides). This tool adds the
**mechanical detection** those signals lacked, with two deterministic signals:

- **duplicate blocks**: >= N consecutive normalized content-lines that appear in
  >= 2 places (copy-paste candidates for extraction)
- **repeated literals**: a magic number / string literal that appears in >= K
  places (shared-constant candidates; covers 180's repeated timeout value /
  error code / validation value)

Candidate-only: it points at duplication, it does not refactor. The extract /
factor-out decision stays with design (per-case), per 180's priority rule
(>= 3 appearances strong, 2 weak). Comments and string literals are scrubbed for
the block signal (so duplicated comments do not count); string *values* are read
from the original for the literal signal.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.error_policy_locator import _scrub, _is_generated, _is_test, _discover

_STRUCTURAL = {"{", "}", "};", "});", "})", "( )", "{ }", "return;", "break;", "continue;"}
_NUM_RE = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")
_STR_RE = re.compile(r'"(?:\\.|[^"\\\n])*"')


def _is_magic_number(v: str) -> bool:
    # single-digit ints are loop/index noise; multi-digit ints and floats are candidates
    if "." in v:
        return True
    return abs(int(v)) >= 10


def _normalized_lines(src: str) -> list[tuple[int, str]]:
    out = []
    for i, line in enumerate(_scrub(src).splitlines(), 1):
        norm = " ".join(line.split())
        # skip blanks, structural braces, and punctuation-only lines (e.g. bare ",")
        if not norm or norm in _STRUCTURAL or not any(c.isalpha() for c in norm):
            continue
        out.append((i, norm))
    return out


def find_duplicate_blocks(files: dict[str, str], *, window: int = 8, min_occurrences: int = 2) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    norm_cache: dict[str, list[tuple[int, str]]] = {}
    for rel, src in files.items():
        entries = _normalized_lines(src)
        norm_cache[rel] = entries
        for j in range(len(entries) - window + 1):
            chunk = entries[j : j + window]
            key = "\n".join(n for _, n in chunk)
            groups[key].append({"file": rel, "start": chunk[0][0], "end": chunk[-1][0]})

    out: list[dict] = []
    covered: dict[str, set[int]] = defaultdict(set)
    for key, occ in sorted(groups.items(), key=lambda kv: (kv[1][0]["file"], kv[1][0]["start"])):
        distinct = {(o["file"], o["start"]) for o in occ}
        if len(distinct) < min_occurrences:
            continue
        first = occ[0]
        span = set(range(first["start"], first["end"] + 1))
        if span & covered[first["file"]]:  # collapse overlapping sliding windows in a region
            continue
        for o in occ:
            covered[o["file"]].update(range(o["start"], o["end"] + 1))
        snippet = " / ".join(key.split("\n")[:3])
        out.append({
            "lines": window,
            "occurrences": sorted(({(o["file"], o["start"]) for o in occ})),
            "count": len(distinct),
            "snippet": snippet[:160],
        })
    out.sort(key=lambda g: g["count"], reverse=True)
    return out


def find_repeated_literals(files: dict[str, str], *, min_occurrences: int = 3) -> list[dict]:
    num_loc: dict[str, list] = defaultdict(list)
    str_loc: dict[str, list] = defaultdict(list)
    for rel, src in files.items():
        scrubbed = _scrub(src)  # numbers from scrubbed (no comment/string noise)
        for i, line in enumerate(scrubbed.splitlines(), 1):
            for m in _NUM_RE.finditer(line):
                if _is_magic_number(m.group(0)):
                    num_loc[m.group(0)].append((rel, i))
        for i, line in enumerate(src.splitlines(), 1):  # strings from original
            for m in _STR_RE.finditer(line):
                val = m.group(0)
                if len(val) >= 5:  # "" and 1-2 char strings are noise
                    str_loc[val].append((rel, i))

    out: list[dict] = []
    for kind, table in (("number", num_loc), ("string", str_loc)):
        for value, locs in table.items():
            distinct = sorted(set(locs))
            if len(distinct) >= min_occurrences and len({f for f, _ in distinct}) >= 2:
                out.append({
                    "kind": kind, "value": value, "count": len(distinct),
                    "locations": [{"file": f, "line": ln} for f, ln in distinct[:12]],
                })
    out.sort(key=lambda c: c["count"], reverse=True)
    return out


@dataclass
class CommonalityScope:
    included_files: int = 0
    excluded_generated: int = 0
    excluded_tests: int = 0
    window: int = 8
    note: str = "candidate-only; >=3 appearances strong, 2 weak (180 priority); extract decision stays with design"


def scan(paths, *, include_tests=False, root=None, window=8, block_min=2, literal_min=3):
    root = root or Path.cwd()
    scope = CommonalityScope(window=window)
    files: dict[str, str] = {}
    for path in _discover([Path(p) for p in paths]):
        if _is_generated(path):
            scope.excluded_generated += 1
            continue
        if not include_tests and _is_test(path):
            scope.excluded_tests += 1
            continue
        try:
            src = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
        files[rel] = src
        scope.included_files += 1
    return {
        "duplicate_blocks": find_duplicate_blocks(files, window=window, min_occurrences=block_min),
        "repeated_literals": find_repeated_literals(files, min_occurrences=literal_min),
    }, scope


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Surface DRY / common-processing candidates from C# (candidate-only)")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--root", default=None)
    parser.add_argument("--window", type=int, default=8, help="min consecutive content-lines for a duplicate block")
    parser.add_argument("--block-min", type=int, default=2, help="min occurrences for a duplicate block")
    parser.add_argument("--literal-min", type=int, default=3, help="min appearances for a repeated literal")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max", type=int, default=20)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else None
    paths = [Path(p).resolve() for p in args.paths]
    result, scope = scan(paths, include_tests=args.include_tests, root=root,
                         window=args.window, block_min=args.block_min, literal_min=args.literal_min)

    if args.json:
        print(json.dumps({"scope": asdict(scope), **result}, indent=2))
        return 0
    print(f"files: {scope.included_files} (excluded generated {scope.excluded_generated}, tests {scope.excluded_tests})")
    print(f"window: {scope.window} lines; candidates only (extract decision stays with design)")
    blocks = result["duplicate_blocks"]
    print(f"\n## duplicate blocks: {len(blocks)}")
    for b in blocks[: args.max]:
        locs = ", ".join(f"{f}:{ln}" for f, ln in b["occurrences"][:6])
        print(f"  x{b['count']} ({b['lines']} lines)  {locs}")
        print(f"      {b['snippet']}")
    lits = result["repeated_literals"]
    print(f"\n## repeated literals: {len(lits)}")
    for c in lits[: args.max]:
        files = ", ".join(sorted({l['file'] for l in c['locations']})[:4])
        print(f"  x{c['count']} {c['kind']}  {c['value'][:48]}  ({files})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
