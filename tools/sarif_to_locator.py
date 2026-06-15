"""Normalize analyzer SARIF output into the 131 locator Output Contract.

Consumes SARIF 2.1.0 produced by a Roslyn analyzer run (`dotnet build` with an
ErrorLog, `dotnet format analyzers`, etc.) and emits 131 *candidate* records
using the verified rule maps in
``knowledge/source_analysis/132_csharp_error_policy_analyzer_rule_map.md`` (the
``cs.err.*`` family) and ``knowledge/csharp/130_csharp_custom_attribute_design_principles.md``
(the ``cs.attr.*`` family).

Contract (binding, from 131/132):

- analyzer ``level``/severity is dropped; every hit is ``confidence: candidate``
  with ``judgment_status: unset``
- the pass never auto-fails (exit 0) unless ``--strict`` is set for a missing
  collection
- a missing analyzer run is a ``collection_error`` in the scope, NOT "no hits"
- hits are deduplicated by ``(file, line, column, locator_id)``; corroborating
  rule ids are merged

This is a skeleton: it does the mapping/normalization/scope work. It does not
run the analyzers; produce the SARIF with the collection profile separately.
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
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RuleMapping:
    locator_id: str
    source_pattern_id: str
    tier: str
    note: str = ""


_THROW = ("cs.err.throw_variable_rethrow", "130:throw-sites/variable-rethrow", "T2")
_EMPTY = ("cs.err.empty_catch", "130:catch-blocks/empty-catch", "T2")
_AVOID = ("cs.err.async_void_non_event", "130:dotnet-specific/async-void", "T2")
_SYNC = ("cs.err.sync_wait_result", "130:dotnet-specific/sync-wait", "T1/T2")
_FAF = ("cs.err.fire_and_forget", "130:dotnet-specific/fire-and-forget", "T2")

# Verified 2026-06-15 against 132. external_rule_id -> RuleMapping.
RULE_MAP: dict[str, RuleMapping] = {
    "CA2200": RuleMapping(*_THROW),
    "S3445": RuleMapping(*_THROW),
    "S2486": RuleMapping(*_EMPTY, "signal only; empty_catch stays custom (generic Exception only; comment exempts)"),
    # S108 intentionally NOT mapped: verified 2026-06-15 to fire on ANY empty block
    # (empty try/if/while), not just catch, so mapping it to empty_catch injects
    # false positives. S2486 / RCS1075 are catch-scoped; the custom locator is authoritative.
    "RCS1075": RuleMapping(*_EMPTY, "signal only; System.Exception only; flags comment-only"),
    "AsyncFixer03": RuleMapping(*_AVOID, "near-full; verify event-handler exclusion vs target frameworks"),
    "S3168": RuleMapping(*_AVOID, "near-full; known event-handler FP gaps"),
    "AsyncFixer02": RuleMapping(*_SYNC, "context-limited full"),
    "MA0042": RuleMapping(*_SYNC, "context-limited (async-migration policy)"),
    "MA0045": RuleMapping(*_SYNC, "context-limited (async-migration policy)"),
    "S4462": RuleMapping(*_SYNC, ".Result/.Wait; GetResult arm unconfirmed"),
    "CA1849": RuleMapping(*_SYNC, "context-limited (async context); covers GetAwaiter().GetResult()"),
    "CS4014": RuleMapping(*_FAF, "in-async only"),
    "AsyncFixer04": RuleMapping(*_FAF, "narrow: unawaited async call in using block"),
    "VSTHRD110": RuleMapping(*_FAF, "unobserved async result; broader contexts than CS4014"),
    # --- custom-attribute design principles (knowledge/csharp/130) ---
    # CA1710 intentionally NOT mapped: it is a multi-purpose suffix rule (also
    # EventArgs/Exception/Collection), so a CA1710 hit cannot be attributed to an
    # Attribute-derived type from the rule id alone. CA1018/CA1019/CA1813 are
    # attribute-specific (they only fire on System.Attribute subclasses).
    "CA1018": RuleMapping("cs.attr.attribute_usage", "csharp130:attribute/usage", "T2",
                          "custom attribute should declare [AttributeUsage] with explicit targets"),
    "CA1019": RuleMapping("cs.attr.argument_accessors", "csharp130:attribute/accessors", "T2",
                          "attribute ctor arguments need accessor properties"),
    "CA1813": RuleMapping("cs.attr.sealed", "csharp130:attribute/sealed", "T2",
                          "seal the attribute type (or make it abstract)"),
}


@dataclass
class LocatorHit:
    external_tool: str
    external_rule_id: str
    locator_id: str
    source_pattern_id: str
    tier: str
    file: str
    line: int
    column: int
    detection_method: str
    scope_id: str
    confidence: str = "candidate"
    judgment_status: str = "unset"
    notes: str = ""


@dataclass
class NormalizeScope:
    scan_id: str
    sarif_inputs: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    mapped_rules_fired: list[str] = field(default_factory=list)
    enabled_locators: list[str] = field(default_factory=list)
    unmapped_rule_ids: list[str] = field(default_factory=list)
    results_without_location: int = 0
    collection_errors: list[str] = field(default_factory=list)


def _normalize_uri(uri: str, root: Path | None) -> str:
    if uri.startswith("file:"):
        path = unquote(urlparse(uri).path)
        if re.match(r"/[A-Za-z]:", path):  # /C:/... -> C:/...
            path = path[1:]
        uri = path
    pth = Path(uri)
    if root is not None:
        try:
            return pth.resolve().relative_to(root.resolve()).as_posix()
        except (ValueError, OSError):
            pass
    return uri.replace("\\", "/")


def _iter_results(sarif: dict):
    for run in sarif.get("runs", []) or []:
        driver = (run.get("tool") or {}).get("driver") or {}
        name = driver.get("name") or "unknown"
        version = driver.get("version")
        display = f"{name} {version}".strip() if version else name
        for result in run.get("results", []) or []:
            yield name, display, result


def _location(result: dict) -> tuple[str, int, int] | None:
    for loc in result.get("locations", []) or []:
        phys = loc.get("physicalLocation") or {}
        art = phys.get("artifactLocation") or {}
        region = phys.get("region") or {}
        uri = art.get("uri")
        line = region.get("startLine")
        if uri and line:
            return uri, int(line), int(region.get("startColumn", 1) or 1)
    return None


def normalize(
    sarif_paths: list[Path],
    *,
    root: Path | None = None,
    expected_tools: list[str] | None = None,
) -> tuple[list[LocatorHit], NormalizeScope]:
    scan_id = "norm-" + hashlib.sha1(
        (_dt.datetime.now(_dt.timezone.utc).isoformat() + repr(sarif_paths)).encode()
    ).hexdigest()[:12]
    scope = NormalizeScope(scan_id=scan_id)

    deduped: dict[tuple[str, int, int, str], LocatorHit] = {}
    tools_seen: set[str] = set()
    names_seen: set[str] = set()
    rules_fired: set[str] = set()
    unmapped: set[str] = set()

    for sarif_path in sarif_paths:
        scope.sarif_inputs.append(str(sarif_path))
        try:
            sarif = json.loads(sarif_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            scope.collection_errors.append(f"unreadable SARIF: {sarif_path}: {exc}")
            continue

        # Never silently treat a non-v2 SARIF as "no hits" (132 collection rule).
        # The .NET ErrorLog default is SARIF v1.0.0; v2 needs version=2 with the
        # comma escaped (e.g. -p:ErrorLog=out.sarif%2cversion=2.1).
        version = str(sarif.get("version", ""))
        if not version.startswith("2"):
            scope.collection_errors.append(
                f"unsupported SARIF version {version or 'missing'!r} "
                f"(need 2.x; emit with version=2): {sarif_path}"
            )
            continue

        for name, display, result in _iter_results(sarif):
            tools_seen.add(display)
            names_seen.add(name)
            rule_id = result.get("ruleId") or ""
            mapping = RULE_MAP.get(rule_id)
            if mapping is None:
                if rule_id:
                    unmapped.add(rule_id)
                continue
            loc = _location(result)
            if loc is None:
                scope.results_without_location += 1
                continue
            uri, line, column = loc
            rel = _normalize_uri(uri, root)
            rules_fired.add(rule_id)
            key = (rel, line, column, mapping.locator_id)
            existing = deduped.get(key)
            if existing is None:
                deduped[key] = LocatorHit(
                    external_tool=name,
                    external_rule_id=rule_id,
                    locator_id=mapping.locator_id,
                    source_pattern_id=mapping.source_pattern_id,
                    tier=mapping.tier,
                    file=rel,
                    line=line,
                    column=column,
                    detection_method=f"roslyn:{name}",
                    scope_id=scan_id,
                    notes=mapping.note,
                )
            else:  # corroborating rule at same location -> merge
                rules = sorted(set(existing.external_rule_id.split("+")) | {rule_id})
                existing.external_rule_id = "+".join(rules)

    if expected_tools:
        for want in expected_tools:
            if not any(want.lower() in n.lower() for n in names_seen):
                scope.collection_errors.append(
                    f"expected analyzer not found in SARIF (collection gap, not 'no hits'): {want}"
                )

    hits = sorted(deduped.values(), key=lambda h: (h.file, h.line, h.column, h.locator_id))
    scope.tools = sorted(tools_seen)
    scope.mapped_rules_fired = sorted(rules_fired)
    scope.enabled_locators = sorted({h.locator_id for h in hits})
    scope.unmapped_rule_ids = sorted(unmapped)
    return hits, scope


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize analyzer SARIF into 131 locator candidates (never a verdict)"
    )
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 file(s) to normalize")
    parser.add_argument("--root", default=None, help="root for relative file paths")
    parser.add_argument(
        "--expected-tool",
        action="append",
        default=[],
        help="analyzer driver name expected in the SARIF; missing => collection error",
    )
    parser.add_argument("--json", action="store_true", help="emit the 131 Output Contract as JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if there are collection errors (candidates still never fail)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else None
    hits, scope = normalize(
        [Path(p) for p in args.sarif], root=root, expected_tools=args.expected_tool
    )

    if args.json:
        print(json.dumps({"scope": asdict(scope), "hits": [asdict(h) for h in hits]}, indent=2))
    else:
        print(f"scan_id: {scope.scan_id}")
        print(f"tools: {', '.join(scope.tools) or '-'}")
        print(f"mapped rules fired: {', '.join(scope.mapped_rules_fired) or '-'}")
        print(f"unmapped rule ids: {len(scope.unmapped_rule_ids)}")
        print(f"results without location: {scope.results_without_location}")
        print(f"collection errors: {len(scope.collection_errors)}")
        for err in scope.collection_errors:
            print(f"  ! {err}")
        print(f"candidates (NOT verdicts): {len(hits)}")
        for h in hits:
            print(f"  [{h.locator_id}] {h.file}:{h.line}:{h.column}  <-{h.external_rule_id}  {h.notes}")

    if args.strict and scope.collection_errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
