"""Deterministic proposal discovery over the host-approved engineering XID catalog."""

AREAS = {
    "api_integration": ("contract", "failure", "idempotency", "external_side_effects"),
    "state_management": ("consistency", "invariants", "transactions"),
    "concurrency": ("contention", "exclusion", "visibility"),
    "failure_recovery": ("safe_replay", "recovery", "unknown_outcome"),
    "architecture_change": ("responsibility", "dependencies", "change_impact"),
    "security": ("authorization", "least_privilege", "boundary_validation"),
}
FLAGS = {
    "external_side_effects": ("external_side_effects", "idempotency", "unknown_outcome", "consistency"),
    "state_management": AREAS["state_management"],
    "concurrency": AREAS["concurrency"],
}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _texts(value):
    return isinstance(value, list) and all(_text(item) for item in value) and len(set(value)) == len(value)


def validate_context(context):
    lists = {"requirements", "constraints", "assumptions", "existing_xids", "related_decision_ids"}
    texts = {"category", "target", "failure_impact"}
    if not isinstance(context, dict) or set(context) != lists | texts | FLAGS.keys() | {"candidate"}:
        raise ValueError("invalid principle discovery context fields")
    if any(not _texts(context[key]) for key in lists) or any(not _text(context[key]) for key in texts):
        raise ValueError("invalid principle discovery context values")
    if context["category"] not in AREAS:
        raise ValueError("unsupported principle discovery category")
    if any(context[key] not in ("yes", "no", "unknown") for key in FLAGS):
        raise ValueError("discovery flags must be yes, no or unknown")
    if all(context[key] != "unknown" for key in FLAGS):
        return []
    return sorted(key for key in FLAGS if context[key] == "unknown")


def catalog_metadata(ref):
    metadata = ref["discovery"] if isinstance(ref, dict) and "discovery" in ref else None
    if metadata is None and not (isinstance(ref, dict) and "discovery" in ref):
        return None
    if (not isinstance(metadata, dict) or set(metadata) != {"areas", "conditions", "source", "related_xids"}
            or not _texts(metadata["areas"]) or not _texts(metadata["related_xids"])
            or not _text(metadata["conditions"]) or not _text(metadata["source"])):
        raise ValueError("invalid principle catalog discovery metadata")
    return metadata


def discover(context, configured, catalog, prior):
    unknown_flags = validate_context(context)
    areas = set(AREAS[context["category"]])
    for flag, extra in FLAGS.items():
        if context[flag] != "no":
            areas.update(extra)
    matched = {}
    metadata = {xid: catalog_metadata(ref) for xid, ref in catalog.items()}

    def include(xid, reason):
        matched.setdefault(xid, set()).add(reason)

    for xid in configured:
        include(xid, "configured")
    for xid in context["existing_xids"]:
        include(xid, "existing_xid")
    for decision_id, xids in prior.items():
        for xid in xids:
            include(xid, f"existing_decision:{decision_id}")
    covered = set()
    for xid, record in metadata.items():
        if record is not None:
            for area in areas.intersection(record["areas"]):
                include(xid, f"area:{area}")
                covered.add(area)

    pending = list(matched)
    while pending:
        origin = pending.pop()
        for xid in (metadata.get(origin) or {}).get("related_xids", ()):
            if xid not in matched:
                pending.append(xid)
            include(xid, f"related_xid:{origin}")
    return {"strategy": "approved_catalog_areas_and_xid_links_v1", "areas": sorted(areas),
            "uncovered_areas": sorted(areas - covered), "unknown_flags": unknown_flags,
            "configured_xids": sorted(configured),
            "matches": {xid: sorted(reasons) for xid, reasons in sorted(matched.items())}}


def resolve(prepared, basis, conflicts):
    snapshot = prepared["principle_discovery"]
    candidates = snapshot["matches"]
    if not isinstance(basis, dict) or basis.keys() != candidates.keys():
        raise ValueError("applicability must account for every discovered and configured XID")
    required, not_applicable, unresolved = [], [], []
    for xid, evaluation in sorted(basis.items()):
        if (not isinstance(evaluation, dict) or set(evaluation) != {"applicability", "reason"}
                or not _text(evaluation["reason"])):
            raise ValueError("applicability requires a reason for each XID")
        state = evaluation["applicability"]
        if xid in prepared["context"]["unresolved_xids"] and state != "unresolved":
            raise ValueError("unavailable XID must remain unresolved")
        if state == "applies":
            required.append(xid)
        elif state == "not_applicable":
            not_applicable.append(xid)
        elif state == "unresolved":
            unresolved.append(xid)
        else:
            raise ValueError("unknown principle applicability")
    if not isinstance(conflicts, list):
        raise ValueError("principle conflicts must be a list")
    requirements = set(prepared["decision_context"]["requirements"])
    for conflict in conflicts:
        if (not isinstance(conflict, dict) or set(conflict) != {"xids", "status", "requirements", "reason"}
                or not _texts(conflict["xids"]) or len(conflict["xids"]) < 2
                or set(conflict["xids"]) - candidates.keys()
                or not _texts(conflict["requirements"]) or set(conflict["requirements"]) - requirements
                or conflict["status"] not in ("resolved", "unresolved") or not _text(conflict["reason"])
                or (conflict["status"] == "resolved" and not conflict["requirements"])):
            raise ValueError("invalid principle conflict or missing requirement comparison")
    return {"configured_xids": snapshot["configured_xids"],
            "discovered_xids": sorted(candidates.keys() - set(snapshot["configured_xids"])),
            "required": required, "not_applicable": not_applicable, "unresolved": unresolved,
            "basis": basis, "conflicts": conflicts,
            "uncovered_areas": snapshot["uncovered_areas"], "unknown_flags": snapshot["unknown_flags"]}
