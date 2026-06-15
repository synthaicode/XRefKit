"""Extract the de-facto C# naming conventions from an existing (brownfield)
codebase so new code can match what is already there.

Descriptive, not enforcing: for each declaration kind it reports the dominant
casing (with share), affix rules actually in use (interface `I` prefix, method
`Async` suffix, field underscore prefix), common type suffixes, and the outliers
that deviate (with `file:line`). The dominant rule is guidance for new code; the
outliers are existing exceptions a human weighs, not a verdict.

Kinds: types (`class`/`record`/`struct`), `interface`, method, property, field,
parameter. Detection of methods/properties/fields is a **heuristic**: a
declaration must carry at least one access/declaration modifier, which excludes
call sites, locals, and most constructors but also misses interface-body and
modifier-less members. Parameters are read from detected method headers.

Use ``--changed-vs <gitref>`` to apply the convention strictly to *new/changed*
declarations only (git-diff added lines), so a brownfield repo's existing
deviations are not flagged. Field casing is visibility-dependent (private
`_camelCase` vs public/const `PascalCase`); it is reported descriptively but not
strictly enforced on the delta.

Reuses the comment/string scrubber from ``tools/error_policy_locator.py``.
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

from tools.error_policy_locator import _scrub, _is_generated, _is_test, _discover, _line_col, _match_pair

_TYPE_RE = re.compile(r"\b(?:record\s+struct|record\s+class|record|class|struct)\s+([A-Za-z_]\w*)")
_INTERFACE_RE = re.compile(r"\binterface\s+([A-Za-z_]\w*)")
_MODIFIERS = (
    "public|private|protected|internal|static|async|virtual|override|sealed|"
    "abstract|extern|partial|new|unsafe|readonly|const|volatile|required"
)
# guard so a type/event/keyword in the return-type slot is not read as a member
_DECL_GUARD = r"(?!(?:class|struct|interface|record|enum|namespace|event|delegate|void|return|new|using|where)\b)"
_METHOD_RE = re.compile(
    r"(?:^|[;{}\)])\s*(?:\[[^\]]*\]\s*)*"
    rf"(?:(?:{_MODIFIERS})\s+)+(?:[\w<>\[\],\.\?]+\s+)+"
    r"([A-Za-z_]\w*)\s*(?:<[^>]+>)?\s*\(",
    re.MULTILINE,
)
_PROPERTY_RE = re.compile(
    r"(?:^|[;{}])\s*(?:\[[^\]]*\]\s*)*"
    rf"(?:(?:{_MODIFIERS})\s+)+{_DECL_GUARD}(?:[\w<>\[\],\.\?]+\s+)+"
    r"([A-Za-z_]\w*)\s*(?:\{\s*(?:get|set|init)\b|=>)",
    re.MULTILINE,
)
_FIELD_RE = re.compile(
    r"(?:^|[;{}])\s*(?:\[[^\]]*\]\s*)*"
    rf"(?:(?:{_MODIFIERS})\s+)+{_DECL_GUARD}(?:[\w<>\[\],\.\?]+\s+)+"
    r"([A-Za-z_]\w*)\s*(?:=[^=]|;)",
    re.MULTILINE,
)

# Only true reserved words (which can never be identifiers) — contextual keywords
# like value/get/set/init/var/when ARE valid identifiers (e.g. a parameter `value`)
# and must NOT be filtered.
_CS_KEYWORDS = frozenset(
    "where class struct record interface enum namespace new base this void return "
    "null true false in out ref params event delegate using".split()
)

KINDS = ("type", "interface", "method", "property", "field", "parameter")


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


def _split_params(param_str: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in param_str:
        if ch in "([<{":
            depth += 1
        elif ch in ")]>}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def _param_name(chunk: str) -> str | None:
    idents = re.findall(r"[A-Za-z_]\w*", chunk.split("=")[0])
    return idents[-1] if idents else None


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
    method_detection: str = "heuristic: members need >=1 modifier; misses interface/modifier-less members; params from detected methods"


def _profile_kind(kind: str, items: list) -> KindProfile | None:
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
        c = sum(1 for n, _, _ in items if re.match(r"^I[A-Z]", n))
        affixes["I_prefix"] = {"count": c, "share": round(c / len(items), 3)}
    if kind == "method":
        c = sum(1 for n, _, _ in items if n.endswith("Async"))
        affixes["Async_suffix"] = {"count": c, "share": round(c / len(items), 3)}
    if kind == "field":
        c = sum(1 for n, _, _ in items if n.startswith("_"))
        affixes["underscore_prefix"] = {"count": c, "share": round(c / len(items), 3)}
    top_suffixes = Counter(s for n, _, _ in items if (s := _suffix(n))).most_common(8) if kind in ("type", "interface") else []
    return KindProfile(
        kind=kind, count=len(items), dominant_casing=dominant,
        dominant_share=round(dom_count / len(items), 3), casing_distribution=dict(dist),
        affixes=affixes, top_suffixes=top_suffixes, outliers=outliers,
    )


def extract_text(rel: str, src: str, collect: dict, type_names: set) -> None:
    scrubbed = _scrub(src)
    for m in _TYPE_RE.finditer(scrubbed):
        name = m.group(1)
        if name in _CS_KEYWORDS:
            continue
        type_names.add(name)
        collect["type"].append((name, rel, _line_col(scrubbed, m.start(1))[0]))
    for m in _INTERFACE_RE.finditer(scrubbed):
        name = m.group(1)
        if name in _CS_KEYWORDS:
            continue
        collect["interface"].append((name, rel, _line_col(scrubbed, m.start(1))[0]))
    for m in _PROPERTY_RE.finditer(scrubbed):
        name = m.group(1)
        if name in _CS_KEYWORDS or name in type_names:
            continue
        collect["property"].append((name, rel, _line_col(scrubbed, m.start(1))[0]))
    for m in _FIELD_RE.finditer(scrubbed):
        name = m.group(1)
        if name in _CS_KEYWORDS or name in type_names:
            continue
        collect["field"].append((name, rel, _line_col(scrubbed, m.start(1))[0]))
    for m in _METHOD_RE.finditer(scrubbed):
        name = m.group(1)
        if name in type_names or name in _CS_KEYWORDS:
            continue
        line = _line_col(scrubbed, m.start(1))[0]
        collect["method"].append((name, rel, line))
        paren = scrubbed.index("(", m.end(1) - 1)
        end = _match_pair(scrubbed, paren, "(", ")")
        for chunk in _split_params(scrubbed[paren + 1 : end - 1]):
            pname = _param_name(chunk)
            if pname and pname not in _CS_KEYWORDS:
                collect["parameter"].append((pname, rel, line))


def profile_paths(paths, *, include_tests=False, root=None):
    root = root or Path.cwd()
    scope = NamingScope(tests_included=include_tests)
    collect = {k: [] for k in KINDS}
    type_names: set = set()
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
        scope.included_files += 1
        extract_text(rel, src, collect, type_names)
    profile = {k: asdict(p) for k in KINDS if (p := _profile_kind(k, collect[k]))}
    return profile, scope


def _parse_added_lines(diff_text: str) -> dict[str, set[int]]:
    added: dict[str, set[int]] = {}
    current: str | None = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            current = None if target == "/dev/null" else (target[2:] if target.startswith(("a/", "b/")) else target)
            if current is not None:
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
    root = root or Path.cwd()
    out: list[tuple[str, str, str, int]] = []
    for path in _discover([Path(p) for p in paths]):
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
        if rel not in added_lines or _is_generated(path) or (not include_tests and _is_test(path)):
            continue
        try:
            src = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            continue
        collect = {k: [] for k in KINDS}
        extract_text(rel, src, collect, set())
        wanted = added_lines[rel]
        for kind in KINDS:
            for name, f, ln in collect[kind]:
                if ln in wanted:
                    out.append((kind, name, f, ln))
    return out


# field casing is visibility-dependent (private _camelCase vs public/const Pascal),
# so it is reported descriptively but not strictly enforced on the delta.
_NOT_CASING_ENFORCED = {"field"}


def check_changed(profile, changed_decls, *, i_prefix_threshold=0.9):
    results = []
    for kind, name, file, line in changed_decls:
        kp = profile.get(kind)
        actual = classify_casing(name)
        expected = kp["dominant_casing"] if kp else None
        issues = []
        if kind not in _NOT_CASING_ENFORCED and expected and actual != expected:
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


def _outlier_key(o: dict) -> str:
    return f"{o['file']}::{o['name']}"


def baseline_from_profile(profile: dict) -> dict:
    """Snapshot the current outliers as an accepted baseline (file::name per kind)."""
    return {
        k: sorted({_outlier_key(o) for o in p["outliers"]})
        for k, p in profile.items()
        if p["outliers"]
    }


def new_outliers(profile: dict, baseline: dict) -> dict:
    """Return only outliers not present in the accepted baseline, per kind."""
    out: dict = {}
    for k, p in profile.items():
        accepted = set(baseline.get(k, []))
        fresh = [o for o in p["outliers"] if _outlier_key(o) not in accepted]
        if fresh:
            out[k] = fresh
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract de-facto C# naming conventions (descriptive)")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-outliers", type=int, default=15)
    parser.add_argument("--changed-vs", default=None, metavar="GITREF",
                        help="check ONLY declarations on lines added vs GITREF; convention still derived from the whole tree")
    parser.add_argument("--strict", action="store_true", help="exit non-zero if a changed declaration deviates")
    parser.add_argument("--write-baseline", default=None, metavar="PATH",
                        help="snapshot current outliers as an accepted baseline (file::name per kind) and exit")
    parser.add_argument("--baseline", default=None, metavar="PATH",
                        help="JSON baseline of accepted outliers; full-profile mode then shows only NEW outliers")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else None
    paths = [Path(p).resolve() for p in args.paths]
    profile, scope = profile_paths(paths, include_tests=args.include_tests, root=root)

    if args.write_baseline is not None:
        bl = baseline_from_profile(profile)
        Path(args.write_baseline).write_text(json.dumps(bl, indent=2), encoding="utf-8")
        total = sum(len(v) for v in bl.values())
        print(f"baseline written: {total} accepted outliers across {len(bl)} kinds -> {args.write_baseline}")
        return 0

    if args.changed_vs is not None:
        base = root or Path.cwd()
        added = git_added_lines(args.changed_vs, paths, cwd=base)
        decls = changed_declarations(paths, added, include_tests=args.include_tests, root=base)
        results = check_changed(profile, decls)
        deviations = [r for r in results if not r["conforms"]]
        if args.json:
            print(json.dumps({"checked": len(results), "deviations": deviations}, indent=2))
        else:
            print(f"changed declarations checked vs {args.changed_vs}: {len(results)} (existing code not re-checked)")
            print(f"deviations from existing convention: {len(deviations)}")
            for r in deviations:
                print(f"  [{r['kind']}] {r['name']}  {r['file']}:{r['line']}  -> {'; '.join(r['issues'])}")
        return 1 if (args.strict and deviations) else 0

    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8")) if args.baseline else {}
    fresh = new_outliers(profile, baseline) if baseline else None

    if args.json:
        payload = {"scope": asdict(scope), "profile": profile}
        if baseline:
            payload["new_outliers"] = fresh
        print(json.dumps(payload, indent=2))
        return 0
    print(f"files: {scope.included_files} (excluded generated {scope.excluded_generated}, tests {scope.excluded_tests})")
    print(f"member detection: {scope.method_detection}")
    if baseline:
        print("baseline applied: showing NEW outliers only (accepted existing outliers suppressed)")
    for kind, p in profile.items():
        print(f"\n## {kind}  (n={p['count']})")
        print(f"  dominant casing: {p['dominant_casing']}  ({p['dominant_share']:.0%})")
        print(f"  distribution: {p['casing_distribution']}")
        if p["affixes"]:
            print(f"  affixes: {p['affixes']}")
        if p["top_suffixes"]:
            print(f"  top suffixes: {p['top_suffixes'][:6]}")
        shown = fresh.get(kind, []) if baseline else p["outliers"]
        if baseline:
            suppressed = len(p["outliers"]) - len(shown)
            label = f"new outliers ({len(shown)}; {suppressed} baselined)"
        else:
            label = f"outliers ({len(shown)})"
        if shown:
            print(f"  {label}: " + ", ".join(
                f"{o['name']}({o['casing']}) {o['file']}:{o['line']}" for o in shown[: args.max_outliers]))
        elif baseline and p["outliers"]:
            print(f"  {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
