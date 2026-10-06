"""Check reviewable ontology evidence, never infer semantic identity or merge content.

JSON is a machine-checkable evidence sidecar, not a required human report format.
Concept decisions and relationship vocabulary come from XID 5803607419B9.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DECISIONS = {"create", "extend", "split", "supersede", "reject_duplicate"}
COMPARISONS = {"new_concept", "synonym", "specialization", "different_conditions"}
RELATIONS = {"broader_than", "narrower_than", "part_of", "depends_on", "constrains", "applies_to", "related_to"}
XID = re.compile(r"<!--\s*xid\s*:\s*([A-Za-z0-9_-]+)\s*-->", re.I)
MAX_BYTES = 2 * 1024 * 1024


def validate(root: Path, record: object, *, for_publication: bool = False) -> list[str]:
    """Validate evidence slots and references; successful checks do not approve meaning."""
    if not isinstance(record, dict):
        return ["assessment must be an object"]
    errors: list[str] = []
    for field in ("target_knowledge_path", "proposed_primary_concept", "source_basis", "publication_or_handoff_decision"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"missing reviewable {field}")
    target = record.get("target_knowledge_path")
    if isinstance(target, str):
        path = (root / target).resolve()
        if Path(target).is_absolute() or not path.is_relative_to((root / "knowledge").resolve()) or path.suffix != ".md":
            errors.append("target must be a knowledge Markdown path")
    known: dict[str, Path] = {}
    for path in sorted(path for folder in ("knowledge", "docs", "agent", "capabilities", "skills", "tools") for path in (root / folder).rglob("*.md")):
        for xid in XID.findall(path.read_text(encoding="utf-8-sig")):
            if xid in known and known[xid] != path:
                errors.append(f"ambiguous canonical XID: {xid}")
            known[xid] = path
    lists = ("aliases_or_competing_terms_searched", "candidate_existing_xids", "accepted_relationships", "rejected_relationship_candidates", "unresolved_semantic_conflicts")
    for field in lists:
        if not isinstance(record.get(field), list):
            errors.append(f"{field} must be an explicit list")
    searched = record.get("aliases_or_competing_terms_searched")
    if isinstance(searched, list) and (not searched or any(not isinstance(v, str) or not v.strip() for v in searched)):
        errors.append("search terms must be nonempty strings")
    candidates = record.get("candidate_existing_xids")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, str) or candidate not in known:
                errors.append(f"unresolved candidate XID: {candidate}")
    if not isinstance(record.get("concept_decision"), str) or record["concept_decision"] not in DECISIONS:
        errors.append("invalid concept_decision")
    comparison = record.get("concept_comparison")
    if not isinstance(comparison, dict):
        errors.append("missing concept_comparison")
    else:
        if not isinstance(comparison.get("classification"), str) or comparison["classification"] not in COMPARISONS:
            errors.append("invalid concept comparison classification")
        for field in ("rationale", "applicability", "version", "constraints", "source_authority"):
            if not isinstance(comparison.get(field), str) or not comparison[field].strip():
                errors.append(f"missing comparison {field}; record a supported absence or unknown explicitly")
        if comparison.get("classification") != "new_concept" and not candidates:
            errors.append("comparison to existing knowledge requires a candidate XID")
    accepted = record.get("accepted_relationships")
    seen: set[tuple[str, str]] = set()
    if isinstance(accepted, list):
        if not accepted and (not isinstance(record.get("no_relation_reason"), str) or not record["no_relation_reason"].strip()):
            errors.append("no_relation_reason is required when no semantic edge is justified")
        for relation in accepted:
            if not isinstance(relation, dict):
                errors.append("relationship must be an object")
                continue
            kind, xid = relation.get("type"), relation.get("target_xid")
            if not isinstance(kind, str) or kind not in RELATIONS:
                errors.append("unsupported semantic relationship type")
            if not isinstance(xid, str) or xid not in known:
                errors.append(f"unresolved relationship target: {xid}")
            elif isinstance(target, str) and known[xid].resolve() == (root / target).resolve():
                errors.append("self relationship is not allowed")
            if isinstance(kind, str) and isinstance(xid, str):
                if (kind, xid) in seen:
                    errors.append("duplicate semantic relationship")
                seen.add((kind, xid))
            if not isinstance(relation.get("rationale"), str) or not relation["rationale"].strip():
                errors.append("semantic relationship needs an evidence-based rationale")
    rejected = record.get("rejected_relationship_candidates")
    if isinstance(rejected, list):
        for rejection in rejected:
            if not isinstance(rejection, dict) or not isinstance(rejection.get("reason"), str) or not rejection["reason"].strip():
                errors.append("rejected relationship candidate needs a reason")
    # Load dependencies are optional operational evidence. Never convert them to
    # ontology edges, even when their XIDs coincide with semantic candidates.
    if "runtime_load_dependencies" in record and not isinstance(record["runtime_load_dependencies"], list):
        errors.append("runtime_load_dependencies must be a separate list")
    conflicts = record.get("unresolved_semantic_conflicts")
    if isinstance(conflicts, list) and any(not isinstance(v, str) or not v.strip() for v in conflicts):
        errors.append("semantic conflicts must be explicit nonempty descriptions")
    if for_publication and conflicts:
        errors.append("unresolved semantic conflicts block canonical publication")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assessment", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--for-publication", action="store_true")
    args = parser.parse_args()
    try:
        with args.assessment.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("assessment exceeds size bound")
        record = json.loads(raw.decode("utf-8-sig"))
        errors = validate(args.root.resolve(), record, for_publication=args.for_publication)
    except RecursionError:
        errors = ["assessment nesting exceeds parser limit"]
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    # Escape unpaired surrogates and non-ASCII diagnostics safely on any console.
    print(json.dumps({"ok": not errors, "errors": errors, "semantic_acceptance": "not_verified"}, ensure_ascii=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
