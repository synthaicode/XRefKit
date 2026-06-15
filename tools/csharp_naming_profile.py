"""Extract the de-facto C# naming conventions from an existing (brownfield)
codebase so new code can match what is already there.

It is **descriptive, not enforcing**: for each declaration kind it reports the
dominant casing (with share), the affix rules actually in use (interface `I`
prefix, async `Async` suffix), common type suffixes, and the outliers that
deviate (with `file:line`). The dominant rule is the convention to follow for
new code; the outliers are existing exceptions a human should weigh, not a
verdict.

Scope (first version): types (`class`/`record`/`struct`), `interface`, and
methods. Method detection is a **heuristic**: a declaration must carry at least
one access/declaration modifier, which excludes call sites and most
constructors but also misses modifier-less / interface-body method signatures.
This is intentional — a representative sample beats a noisy one. Full coverage
is a Roslyn follow-up.

Reuses the comment/string scrubber from ``tools/error_policy_locator.py`` so
identifiers inside comments or string literals are not mistaken for
declarations.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.error_policy_locator import _scrub, _is_generated, _is_test, _discover, _line_col

# record struct / record class first so the *name* is captured, not the 2nd keyword
_TYPE_RE = re.compile(r"\b(?:record\s+struct|record\s+class|record|class|struct)\s+([A-Za-z_]\w*)")
_INTERFACE_RE = re.compile(r"\binterface\s+([A-Za-z_]\w*)")

# Reserved words that can be captured by the patterns in non-declaration positions
# (e.g. the `class`/`struct` in a generic constraint `where T : class`).
_CS_KEYWORDS = frozenset(
    "where class struct record interface enum new base this void return null true false "
    "in out ref params async await get set value var dynamic when".split()
)
_MODIFIERS = (
    "public|private|protected|internal|static|async|virtual|override|sealed|"
    "abstract|extern|partial|new|unsafe|readonly"
)
_METHOD_RE = re.compile(
    r"(?:^|[;{}\)])\s*"
    r"(?:\[[^\]]*\]\s*)*"                       # optional attributes
    rf"(?:(?:{_MODIFIERS})\s+)+"                # >= 1 modifier (excludes call sites)
    r"(?:[\w<>\[\],\.\?]+\s+)+"                 # return type (>= 1 token; excludes ctors)
    r"([A-Za-z_]\w*)\s*(?:<[^>]+>)?\s*\(",      # method name + (
    re.MULTILINE,
)


def classify_casing(name: str) -> str:
    underscore = name.startswith("_")
    core = name.lstrip("_")
    if not core:
        return "other"
    if core.isupper() and (len(core) > 1 or core.isalpha()):
        label = "SCREAMING_SNAKE"
    elif re.fullmatch(r"[A-Z][a-z0-9]*([A-Z][a-z0-9]*)*", core):
        label = "PascalCase"
    elif re.fullmatch(r"[a-z][a-z0-9]*([A-Z][a-z0-9]*)*", core):
        label = "camelCase"
    else:
        label = "other"
    return f"_{label}" if underscore else label


_SUFFIX_RE = re.compile(r"[A-Z][a-z0-9]+$")


def _suffix(name: str) -> str | None:
    m = _SUFFIX_RE.search(name)
    return m.group(0) if m else None


@dataclass
class KindProfile:
    kind: str
    count: int
    dominant_casing: str
    dominant_share: float
    casing_distribution: dict
    affixes: dict = field(default_factory=dict)
    top_suffixes: list = field(default_factory=list)
    outliers: list = field(default_factory=list)


@dataclass
class NamingScope:
    included_files: int = 0
    excluded_generated: int = 0
    excluded_tests: int = 0
    tests_included: bool = False
    method_detection: str = "heuristic: requires >=1 modifier; misses interface/modifier-less methods"


def _profile_kind(kind: str, items: list[tuple[str, str, int]]) -> KindProfile | None:
    """items: list of (name, file, line)."""
    if not items:
        return None
    dist = Counter(classify_casing(n) for n, _, _ in items)
    dominant, dom_count = dist.most_common(1)[0]
    outliers = [
        {"name": n, "file": f, "line": ln, "casing": classify_casing(n)}
        for n, f, ln in items
        if classify_casing(n) != dominant
    ]
    affixes: dict = {}
    if kind == "interface":
        i_pref = sum(1 for n, _, _ in items if re.match(r"^I[A-Z]", n))
        affixes["I_prefix"] = {"count": i_pref, "share": round(i_pref / len(items), 3)}
    if kind == "method":
        async_names = [n for n, _, _ in items if n.endswith("Async")]
        affixes["Async_suffix"] = {
            "count": len(async_names),
            "share": round(len(async_names) / len(items), 3),
        }
    top_suffixes = []
    if kind in ("type", "interface"):
        suf = Counter(s for n, _, _ in items if (s := _suffix(n)))
        top_suffixes = suf.most_common(8)
    return KindProfile(
        kind=kind,
        count=len(items),
        dominant_casing=dominant,
        dominant_share=round(dom_count / len(items), 3),
        casing_distribution=dict(dist),
        affixes=affixes,
        top_suffixes=top_suffixes,
        outliers=outliers,
    )


def extract_text(rel: str, src: str, types: list, interfaces: list, methods: list, type_names: set) -> None:
    scrubbed = _scrub(src)
    for m in _TYPE_RE.finditer(scrubbed):
        name = m.group(1)
        if name in _CS_KEYWORDS:  # e.g. `class` in a `where T : class` constraint
            continue
        type_names.add(name)
        line, _ = _line_col(scrubbed, m.start(1))
        types.append((name, rel, line))
    for m in _INTERFACE_RE.finditer(scrubbed):
        name = m.group(1)
        if name in _CS_KEYWORDS:
            continue
        line, _ = _line_col(scrubbed, m.start(1))
        interfaces.append((name, rel, line))
    for m in _METHOD_RE.finditer(scrubbed):
        name = m.group(1)
        if name in type_names or name in _CS_KEYWORDS:  # ctor / type ref / keyword
            continue
        line, _ = _line_col(scrubbed, m.start(1))
        methods.append((name, rel, line))


def profile_paths(paths, *, include_tests=False, root=None):
    root = root or Path.cwd()
    scope = NamingScope(tests_included=include_tests)
    types: list = []
    interfaces: list = []
    methods: list = []
    type_names: set = set()
    for path in _discover([Path(p) for p in paths]):
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
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
        scope.included_files += 1
        extract_text(rel, src, types, interfaces, methods, type_names)
    profile = {
        "type": _profile_kind("type", types),
        "interface": _profile_kind("interface", interfaces),
        "method": _profile_kind("method", methods),
    }
    return {k: asdict(v) for k, v in profile.items() if v}, scope


def _parse_added_lines(diff_text: str) -> dict[str, set[int]]:
    """Parse `git diff --unified=0` output -> {repo-relative file: set of added line numbers}."""
    added: dict[str, set[int]] = {}
    current: str | None = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            if target == "/dev/null":
                current = None
            else:
                current = target[2:] if target.startswith(("a/", "b/")) else target
                added.setdefault(current, set())
        elif line.startswith("@@") and current is not None:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) is not None else 1
                added[current].update(range(start, start + count))
    return {f: s for f, s in added.items() if s}


def git_added_lines(rev_range: str, paths, cwd) -> dict[str, set[int]]:
    out = subprocess.run(
        ["git", "diff", "--unified=0", rev_range, "--", *[str(p) for p in paths]],
        cwd=str(cwd), capture_output=True, text=True,
    )
    return _parse_added_lines(out.stdout)


def changed_declarations(paths, added_lines, *, include_tests=False, root=None):
    """Return (kind, name, file, line) for declarations whose line is in added_lines."""
    root = root or Path.cwd()
    out: list[tuple[str, str, str, int]] = []
    for path in _discover([Path(p) for p in paths]):
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
        if rel not in added_lines:
            continue
        if _is_generated(path) or (not include_tests and _is_test(path)):
            continue
        try:
            src = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            continue
        types, interfaces, methods, names = [], [], [], set()
        extract_text(rel, src, types, interfaces, methods, names)
        wanted = added_lines[rel]
        for kind, items in (("type", types), ("interface", interfaces), ("method", methods)):
            for name, f, ln in items:
                if ln in wanted:
                    out.append((kind, name, f, ln))
    return out


def check_changed(profile, changed_decls, *, i_prefix_threshold=0.9):
    """Check only new/changed declarations against the derived dominant convention.

    Existing code is never re-checked, so historical outliers are not flagged.
    """
    results = []
    for kind, name, file, line in changed_decls:
        kp = profile.get(kind)
        actual = classify_casing(name)
        expected = kp["dominant_casing"] if kp else None
        issues = []
        if expected and actual != expected:
            issues.append(f"casing: expected {expected}, got {actual}")
        if kind == "interface" and kp:
            share = kp.get("affixes", {}).get("I_prefix", {}).get("share", 0)
            if share >= i_prefix_threshold and not re.match(r"^I[A-Z]", name):
                issues.append(f"interface 'I' prefix expected (existing share {share:.0%})")
        results.append({
            "kind": kind, "name": name, "file": file, "line": line,
            "expected_casing": expected, "actual_casing": actual,
            "conforms": not issues, "issues": issues,
        })
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract de-facto C# naming conventions (descriptive, not enforcing)"
    )
    parser.add_argument("paths", nargs="+", help="C# files or directories")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-outliers", type=int, default=15)
    parser.add_argument(
        "--changed-vs",
        default=None,
        metavar="GITREF",
        help="check ONLY declarations on lines added vs GITREF (e.g. main, HEAD~1); "
        "convention is still derived from the whole tree, so existing outliers are not flagged",
    )
    parser.add_argument("--strict", action="store_true", help="exit non-zero if a changed declaration deviates")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else None
    paths = [Path(p).resolve() for p in args.paths]
    profile, scope = profile_paths(paths, include_tests=args.include_tests, root=root)

    if args.changed_vs is not None:
        base = root or Path.cwd()
        added = git_added_lines(args.changed_vs, paths, cwd=base)
        decls = changed_declarations(paths, added, include_tests=args.include_tests, root=base)
        results = check_changed(profile, decls)
        deviations = [r for r in results if not r["conforms"]]
        if args.json:
            print(json.dumps({"checked": len(results), "deviations": deviations}, indent=2))
        else:
            print(f"changed declarations checked vs {args.changed_vs}: {len(results)} "
                  f"(existing code not re-checked)")
            print(f"deviations from existing convention: {len(deviations)}")
            for r in deviations:
                print(f"  [{r['kind']}] {r['name']}  {r['file']}:{r['line']}  -> {'; '.join(r['issues'])}")
        return 1 if (args.strict and deviations) else 0

    if args.json:
        print(json.dumps({"scope": asdict(scope), "profile": profile}, indent=2))
        return 0

    print(f"files: {scope.included_files} (excluded generated {scope.excluded_generated}, tests {scope.excluded_tests})")
    print(f"method detection: {scope.method_detection}")
    for kind, p in profile.items():
        print(f"\n## {kind}  (n={p['count']})")
        print(f"  dominant casing: {p['dominant_casing']}  ({p['dominant_share']:.0%})")
        print(f"  distribution: {p['casing_distribution']}")
        if p["affixes"]:
            print(f"  affixes: {p['affixes']}")
        if p["top_suffixes"]:
            print(f"  top suffixes: {p['top_suffixes'][:6]}")
        if p["outliers"]:
            print(f"  outliers ({len(p['outliers'])}): " + ", ".join(
                f"{o['name']}({o['casing']}) {o['file']}:{o['line']}" for o in p["outliers"][: args.max_outliers]
            ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
