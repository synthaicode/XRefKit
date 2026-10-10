"""Opt-in fixed-output checks and model qualification; never invokes a model.

Approved artifacts and evaluator assets stay outside the evaluated target.
Collection and independent review are caller responsibilities, not inferred here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_contract(path: Path) -> tuple[dict, str]:
    contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    return validate_contract(contract, path)


def validate_contract(contract: dict, path: Path) -> tuple[dict, str]:
    required = {"schema_version", "skill_id", "output_id", "kind", "revision",
                "accepted_output", "samples", "format", "subjective", "repetitions", "knowledge_refs"}
    if not isinstance(contract, dict) or set(contract) != required:
        raise ValueError("reporting contract requires exactly " + ", ".join(sorted(required)))
    if contract["schema_version"] != 1 or contract["kind"] != "fixed_format":
        raise ValueError("only schema 1 fixed_format outputs are supported; code edits are out of scope")
    for name in ("skill_id", "output_id", "revision", "accepted_output"):
        if not isinstance(contract[name], str) or not contract[name].strip():
            raise ValueError(f"non-empty {name} required")
    fmt = contract["format"]
    if not isinstance(fmt, dict) or set(fmt) != {"headings", "tables", "placement"}:
        raise ValueError("format requires headings, tables, placement")
    if not isinstance(fmt["headings"], list) or not fmt["headings"] or any(
        not isinstance(h, str) or not re.fullmatch(r"#{1,6} .+", h) for h in fmt["headings"]
    ) or len(set(fmt["headings"])) != len(fmt["headings"]):
        raise ValueError("unique non-empty Markdown headings required")
    for key in ("tables", "placement"):
        if not isinstance(fmt[key], list):
            raise ValueError(f"format.{key} must be a list")
    for table in fmt["tables"]:
        if not isinstance(table, dict) or set(table) != {"section", "columns"} or table["section"] not in fmt["headings"]:
            raise ValueError("table requires declared section and columns")
        if not isinstance(table["columns"], list) or not table["columns"] or any(not isinstance(c, str) or not c for c in table["columns"]):
            raise ValueError("non-empty table columns required")
    for rule in fmt["placement"]:
        if not isinstance(rule, dict) or set(rule) != {"section", "required_text"} or rule["section"] not in fmt["headings"] or not isinstance(rule["required_text"], str) or not rule["required_text"]:
            raise ValueError("placement requires declared section and non-empty required_text")
    if not isinstance(contract["subjective"], list) or any(not isinstance(s, str) or not s.strip() for s in contract["subjective"]):
        raise ValueError("subjective must list review criteria; empty is allowed")
    samples = contract["samples"]
    if type(contract["repetitions"]) is not int or not 1 <= contract["repetitions"] <= 100:
        raise ValueError("approved repetitions must be an integer (1..100)")
    knowledge = contract["knowledge_refs"]
    if not isinstance(knowledge, list) or any(not isinstance(k, dict) or set(k) != {"xid", "path"} or not re.fullmatch(r"[A-F0-9]{12}", k["xid"]) or not isinstance(k["path"], str) or not k["path"] for k in knowledge):
        raise ValueError("knowledge_refs requires XID and resolved artifact path")
    if not isinstance(samples, list) or not samples or any(not isinstance(s, str) or not s for s in samples):
        raise ValueError("samples must reference fixed input artifacts")
    assets = [contract["accepted_output"], *samples, *(k["path"] for k in knowledge)]
    identity = {"contract": contract, "assets": {a: file_hash(path.parent / a) for a in assets}}
    for ref in knowledge:
        body = (path.parent / ref["path"]).read_text(encoding="utf-8")
        if f"<!-- xid: {ref['xid']} -->" not in body:
            raise ValueError("resolved Knowledge artifact does not carry its declared XID")
    failures = check_format(contract, (path.parent / contract["accepted_output"]).read_text(encoding="utf-8"))
    if failures:
        raise ValueError("accepted artifact contradicts format rules: " + "; ".join(failures))
    return contract, digest(identity)


def check_format(contract: dict, text: str) -> list[str]:
    """Exact structure and information placement, not semantic quality scoring."""
    # Ignore fenced examples so they cannot masquerade as real report sections.
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)[0]
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is None:
            lines.append(line.rstrip())
    headings = [line for line in lines if re.match(r"^#{1,6} ", line)]
    errors = []
    if headings != contract["format"]["headings"]:
        errors.append("heading names/order differ from accepted format")
    sections: dict[str, list[str]] = {}
    current = None
    for line in lines:
        if re.match(r"^#{1,6} ", line):
            current = line
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    for table in contract["format"]["tables"]:
        found = []
        body = sections.get(table["section"], [])
        for index, line in enumerate(body[:-1]):
            if line.strip().startswith("|") and re.fullmatch(r"\s*\|(?:\s*:?-+:?\s*\|)+\s*", body[index + 1]):
                found.append([cell.strip() for cell in line.strip().strip("|").split("|")])
                for row in body[index + 2:]:
                    if not row.strip().startswith("|"):
                        break
                    if len(row.strip().strip("|").split("|")) != len(table["columns"]):
                        errors.append(f"table row width differs in {table['section']}")
        if found != [table["columns"]]:
            errors.append(f"table columns/order differ in {table['section']}")
    for rule in contract["format"]["placement"]:
        if rule["required_text"] not in "\n".join(sections.get(rule["section"], [])):
            errors.append(f"required information placement missing in {rule['section']}: {rule['required_text']}")
    return errors


def model_identity(model: dict) -> dict | None:
    if set(model) != {"provider", "snapshot", "parameters"}:
        raise ValueError("model requires provider, exact snapshot, parameters (no display-name inference)")
    if not isinstance(model["parameters"], dict):
        raise ValueError("model parameters must be an object")
    for key in ("provider", "snapshot"):
        value = model[key]
        if value is None or isinstance(value, str) and value.strip().lower() in {"", "unknown"}:
            return None
        if not isinstance(value, str):
            raise ValueError(f"model.{key} must be a string or null")
    digest(model)  # reject non-finite values
    return model


def identity(contract: dict, baseline_hash: str, procedure: Path, model: dict) -> dict:
    from .skill_definition import load_skill_definition
    if load_skill_definition(procedure)["metadata"]["skill_id"] != contract["skill_id"]:
        raise ValueError("output contract must belong to the evaluated Skill")
    key = {"skill_id": contract["skill_id"], "output_id": contract["output_id"],
            "procedure_hash": file_hash(procedure), "baseline_hash": baseline_hash,
            "model": model_identity(model)}
    if "_quality_profile" in contract:
        key["quality_profile"] = contract["_quality_profile"]
    return key


def load_registry(path: Path) -> dict:
    registry = read_json(path) if path.exists() else {"schema_version": 1, "qualifications": {}}
    if set(registry) != {"schema_version", "qualifications"} or registry["schema_version"] != 1 or not isinstance(registry["qualifications"], dict):
        raise ValueError("invalid qualification registry")
    for key, record in registry["qualifications"].items():
        if not isinstance(record, dict) or set(record) != {"identity", "evidence", "qualified_at"} or digest(record["identity"]) != key or record["identity"].get("model") is None:
            raise ValueError("invalid qualification identity")
    return registry


def assess(key: dict, registry: dict, *, requested: bool = False) -> dict:
    reason = ("user_requested" if requested else "unapproved_profile" if key.get("quality_profile", {}).get("approval_status", "approved") != "approved"
              else "unknown_model_identity" if key["model"] is None
              else "qualified" if digest(key) in registry["qualifications"] else "unqualified_combination")
    return {"status": "qualified" if reason == "qualified" else "assessment_required",
            "reason": reason, "identity": key, "modification_authorized": False}


def evaluate(contract: dict, baseline_hash: str, outputs: list[Path], review: dict | None = None,
             *, repetitions: int = 3) -> dict:
    if repetitions < 1 or len(outputs) < repetitions or len({p.resolve() for p in outputs}) != len(outputs):
        raise ValueError("distinct raw output artifacts required for every repetition")
    hashes = [file_hash(p) for p in outputs]
    errors = [{"output": str(p), "findings": check_format(contract, p.read_text(encoding="utf-8"))} for p in outputs]
    passed = not any(e["findings"] for e in errors)
    reviewed = not contract["subjective"]
    subjective_failed = False
    if review is not None:
        if set(review) != {"baseline_hash", "output_hashes", "reviewer", "decisions"}:
            raise ValueError("review requires baseline_hash, output_hashes, reviewer, decisions")
        if review["baseline_hash"] != baseline_hash or review["output_hashes"] != hashes:
            raise ValueError("review is not bound to these outputs and approved criteria")
        if not isinstance(review["reviewer"], str) or not review["reviewer"].strip():
            raise ValueError("independent reviewer identity required")
        if set(review["decisions"]) != set(contract["subjective"]) or any(v not in {"pass", "fail", "needs_review"} for v in review["decisions"].values()):
            raise ValueError("review must cover every subjective criterion")
        reviewed = all(v == "pass" for v in review["decisions"].values())
        subjective_failed = any(v == "fail" for v in review["decisions"].values())
    approved = contract.get("_quality_profile", {}).get("approval_status", "approved") == "approved"
    result = {"status": "alarm" if not passed or subjective_failed else "pass" if reviewed and approved else "needs_review",
            "baseline_hash": baseline_hash, "output_hashes": hashes, "checks": errors,
            "subjective_review": review, "collection": "caller_supplied; model execution provenance must be retained separately"}
    if "_quality_profile" in contract:
        result["quality_profile"] = contract["_quality_profile"]
    return result


def bind_collection(contract_path: Path, contract: dict, key: dict, evidence: dict, collection: dict) -> dict:
    """Check collection provenance; recorded identity is not provider attestation."""
    if set(collection) != {"identity", "runs", "producer"} or collection["identity"] != key or not isinstance(collection["producer"], str) or not collection["producer"].strip():
        raise ValueError("collection must bind evaluated procedure, baseline, and model identity")
    runs = collection["runs"]
    if not isinstance(runs, list) or len(runs) != len(evidence["output_hashes"]):
        raise ValueError("collection must cover every raw output")
    expected = {file_hash(contract_path.parent / sample) for sample in contract["samples"]}
    contexts = []
    counts = dict.fromkeys(expected, 0)
    for run, output_hash in zip(runs, evidence["output_hashes"]):
        if not isinstance(run, dict) or set(run) != {"output_hash", "input_hash", "context_id"} or run["output_hash"] != output_hash or run["input_hash"] not in expected:
            raise ValueError("collection input/output hash mismatch")
        if not isinstance(run["context_id"], str) or not run["context_id"].strip():
            raise ValueError("fresh execution context identity required")
        contexts.append(run["context_id"])
        counts[run["input_hash"]] += 1
    if len(set(contexts)) != len(contexts) or any(n < contract["repetitions"] for n in counts.values()):
        raise ValueError("approved independent repetition count required for every sample")
    if evidence["subjective_review"] and evidence["subjective_review"]["reviewer"] == collection["producer"]:
        raise ValueError("producer cannot self-approve subjective quality")
    return {**evidence, "collection": collection}


def qualify(registry: dict, key: dict, evidence: dict) -> None:
    if key["model"] is None or evidence["status"] != "pass" or evidence["baseline_hash"] != key["baseline_hash"]:
        raise ValueError("qualification requires known model and passing bound evidence")
    if key.get("quality_profile", {}).get("approval_status", "approved") != "approved" or evidence.get("quality_profile") != key.get("quality_profile"):
        raise ValueError("qualification requires matching approved target quality profile")
    if not isinstance(evidence.get("collection"), dict) or evidence["collection"].get("identity") != key:
        raise ValueError("qualification requires identity-bound collection evidence")
    registry["qualifications"][digest(key)] = {"identity": key, "evidence": evidence,
                                              "qualified_at": datetime.now(timezone.utc).isoformat()}


def authorize(key: dict, instruction: str, max_attempts: int) -> dict:
    if key["model"] is None or not instruction.strip() or not 1 <= max_attempts <= 10:
        raise ValueError("explicit scoped user instruction, known model and bounded attempts (1..10) required")
    if key.get("quality_profile", {}).get("approval_status", "approved") != "approved":
        raise ValueError("example/proposed profiles cannot authorize production correction")
    return {"schema_version": 1, "identity": key, "instruction": instruction,
            "max_attempts": max_attempts, "attempts": 0, "status": "authorized"}


def recalibrate(contract_path: Path, procedure: Path, model: dict, request_path: Path,
                candidate: Path, outputs: list[Path], registry_path: Path, collection: dict,
                review: dict | None = None, procedure_review: dict | None = None,
                profile_context: dict | None = None) -> dict:
    """Adopt an externally generated candidate only after fixed-baseline checks.

    On a failed attempt, the live procedure is untouched (rollback by staging).
    Authorization is consumed on success and cannot be reused after revision.
    """
    if profile_context is None:
        contract, baseline_hash = load_contract(contract_path)
    else:
        from .reporting_profiles import load_profile
        contract, baseline_hash = load_profile(contract_path, **profile_context)
    key = identity(contract, baseline_hash, procedure, model)
    request = read_json(request_path)
    if set(request) != {"schema_version", "identity", "instruction", "max_attempts", "attempts", "status"} or request["schema_version"] != 1:
        raise ValueError("invalid corrective authorization record")
    if request["identity"] != key or request["status"] != "authorized" or not isinstance(request["instruction"], str) or not request["instruction"].strip():
        raise ValueError("explicit authorization does not match this current scope")
    if type(request["attempts"]) is not int or type(request["max_attempts"]) is not int or not 0 <= request["attempts"] < request["max_attempts"] <= 10:
        raise ValueError("corrective attempt limit exhausted or invalid")
    assets = [(contract_path.parent / a).resolve() for a in
              [contract["accepted_output"], *contract["samples"], *(k["path"] for k in contract["knowledge_refs"]),
               *contract.get("_profile_assets", [])]]
    protected = [contract_path.resolve(), request_path.resolve(), registry_path.resolve(), *assets]
    if procedure.resolve() in protected or candidate.resolve() in {procedure.resolve(), *protected}:
        raise ValueError("procedure and staged candidate must be separate from protected baseline/request/registry assets")
    # Preserve Skill identity and declared acceptance criteria when changing wording.
    from .skill_definition import load_skill_definition
    original = load_skill_definition(procedure)["metadata"]
    proposed = load_skill_definition(candidate)["metadata"]
    for field in ("schema_version", "skill_id", "xid", "summary", "applies_when", "inputs", "criteria", "outputs", "exclusions", "control_refs", "knowledge_needs", "aliases"):
        if original.get(field) != proposed.get(field):
            raise ValueError(f"corrective wording cannot change approved {field}")
    registry = load_registry(registry_path)
    request["attempts"] += 1
    evidence = evaluate(contract, baseline_hash, outputs, review, repetitions=contract["repetitions"])
    candidate_bytes = candidate.read_bytes()
    candidate_key = {**key, "procedure_hash": hashlib.sha256(candidate_bytes).hexdigest()}
    evidence = bind_collection(contract_path, contract, candidate_key, evidence, collection)
    if not isinstance(procedure_review, dict) or set(procedure_review) != {"original_hash", "candidate_hash", "reviewer", "decision"} or procedure_review["original_hash"] != key["procedure_hash"] or procedure_review["candidate_hash"] != candidate_key["procedure_hash"]:
        raise ValueError("independent procedure-obligation review bound to original and candidate required")
    if not isinstance(procedure_review["reviewer"], str) or not procedure_review["reviewer"].strip() or procedure_review["reviewer"] == collection["producer"]:
        raise ValueError("candidate producer cannot self-approve procedure obligations")
    if procedure_review["decision"] not in {"pass", "fail", "needs_review"}:
        raise ValueError("invalid procedure review decision")
    evidence["procedure_review"] = procedure_review
    if procedure_review["decision"] != "pass":
        evidence["status"] = "alarm" if procedure_review["decision"] == "fail" else "needs_review"
    if evidence["status"] != "pass":
        request["status"] = "exhausted" if request["attempts"] >= request["max_attempts"] else "authorized"
        write_json(request_path, request)
        return {"status": evidence["status"], "adopted": False, "evidence": evidence}
    # Read staging bytes before adoption; candidate qualification never transfers
    # other models' records to the new procedure revision.
    qualify(registry, candidate_key, evidence)
    # A repository adoption receipt is another hash-bound authority boundary.
    # Stage a handoff rather than breaking the repository's startup/catalog.
    for ancestor in procedure.resolve().parents:
        adoption_path = ancestor / "skills" / "repository_adoption.json"
        if adoption_path.exists():
            adoption = read_json(adoption_path)
            if any((ancestor / entry["definition_path"]).resolve() == procedure.resolve()
                   for entry in adoption.get("entries", [])):
                request["status"] = "handoff"
                write_json(request_path, request)
                return {"status": "needs_adoption_review", "adopted": False,
                        "candidate": str(candidate), "identity": candidate_key, "evidence": evidence,
                        "governance": "Owner must update hash-bound repository adoption; no live procedure or receipt changed"}
            break
    temporary = procedure.with_suffix(procedure.suffix + ".recalibrated")
    temporary.write_bytes(candidate_bytes)
    temporary.replace(procedure)
    request["status"] = "adopted"
    write_json(request_path, request)
    write_json(registry_path, registry)
    return {"status": "pass", "adopted": True, "identity": candidate_key, "evidence": evidence,
            "governance": "Changed procedure hash invalidates prior maturity/adoption receipts; no promotion or receipt refresh performed"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit skill reporting")
    parser.add_argument("action", choices=["select", "assess", "check", "qualify", "authorize", "recalibrate"])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--contract", type=Path, help="Legacy local manifest (not a target Knowledge profile)")
    source.add_argument("--profile", type=Path, action="append", default=[], help="XID-resolved candidate Knowledge profile; repeat for selection")
    parser.add_argument("--target")
    parser.add_argument("--target-revision")
    parser.add_argument("--skill-id")
    parser.add_argument("--output-id")
    parser.add_argument("--profile-xid")
    parser.add_argument("--procedure", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", type=Path, action="append", default=[])
    parser.add_argument("--review", type=Path)
    parser.add_argument("--collection", type=Path)
    parser.add_argument("--procedure-review", type=Path)
    parser.add_argument("--result", type=Path, help="Persist evidence for existing per-run artifact/quality-review hooks")
    parser.add_argument("--reevaluate", action="store_true")
    parser.add_argument("--instruction")
    parser.add_argument("--request", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        sources = [args.contract, *args.profile, args.procedure, args.model, args.registry, args.request,
                   args.candidate, args.review, args.collection, args.procedure_review, *args.output]
        profile_context = None
        if args.profile:
            from .reporting_profiles import load_profile, profile_metadata, select_profile, attachment
            if not args.target or not args.skill_id or not args.output_id:
                raise ValueError("Knowledge profiles require explicit --target, --skill-id, --output-id")
            for path in args.profile:
                metadata = profile_metadata(path)
                sources.extend(attachment(path, value) for value in
                               [metadata["approval"]["evidence"], *(e["path"] for e in metadata["exemplars"]),
                                *(s["path"] for s in metadata["input_samples"]), *(r["path"] for r in metadata["knowledge_refs"])])
            if args.result and args.result.resolve() in {p.resolve() for p in sources if p is not None}:
                raise ValueError("--result must not overwrite source, evaluation, baseline, or state assets")
            selection = select_profile(args.profile, target_id=args.target, skill_id=args.skill_id,
                                       output_id=args.output_id, target_revision=args.target_revision, xid=args.profile_xid)
            if args.action == "select" or selection["status"] != "selected":
                if args.result:
                    write_json(args.result, selection)
                print(json.dumps(selection, indent=2, ensure_ascii=False))
                return 0 if selection["status"] == "selected" else 1
            source_path = Path(selection["selected"]["path"])
            profile_context = {"target_id": args.target, "skill_id": args.skill_id,
                               "output_id": args.output_id, "target_revision": args.target_revision}
            contract, baseline_hash = load_profile(source_path, **profile_context)
        else:
            if args.action == "select" or any((args.target, args.skill_id, args.output_id, args.target_revision, args.profile_xid)):
                raise ValueError("target selection requires Knowledge --profile; --contract is legacy local-manifest mode")
            source_path = args.contract
            contract, baseline_hash = load_contract(source_path)
            sources.extend(source_path.parent / p for p in [contract["accepted_output"], *contract["samples"],
                                                           *(k["path"] for k in contract["knowledge_refs"])])
        if args.result and args.result.resolve() in {p.resolve() for p in sources if p is not None}:
            raise ValueError("--result must not overwrite source, evaluation, baseline, or state assets")
        review = read_json(args.review) if args.review else None
        if args.action == "check":
            result = evaluate(contract, baseline_hash, args.output, review, repetitions=1)
        else:
            if args.procedure is None or args.model is None:
                raise ValueError("--procedure and --model required")
            model = read_json(args.model)
            key = identity(contract, baseline_hash, args.procedure, model)
            if args.action == "authorize":
                if args.request is None or args.instruction is None:
                    raise ValueError("--request and explicit --instruction required")
                if args.request.exists():
                    raise ValueError("use a fresh authorization path; do not reset used attempt records")
                result = authorize(key, args.instruction, args.max_attempts)
                write_json(args.request, result)
            else:
                if args.registry is None:
                    raise ValueError("--registry required")
                registry = load_registry(args.registry)
                if args.action == "assess":
                    result = assess(key, registry, requested=args.reevaluate)
                elif args.action == "qualify":
                    if args.collection is None:
                        raise ValueError("--collection required for qualification provenance")
                    result = evaluate(contract, baseline_hash, args.output, review, repetitions=contract["repetitions"])
                    result = bind_collection(source_path, contract, key, result, read_json(args.collection))
                    if result["status"] == "pass":
                        qualify(registry, key, result)
                        write_json(args.registry, registry)
                else:
                    if args.request is None or args.candidate is None or args.collection is None or args.procedure_review is None:
                        raise ValueError("--request, --candidate, --collection and --procedure-review required")
                    result = recalibrate(source_path, args.procedure, model, args.request,
                                         args.candidate, args.output, args.registry, read_json(args.collection),
                                         review, read_json(args.procedure_review), profile_context=profile_context)
        result["quality_source"] = "Knowledge_profile" if profile_context is not None else "legacy_local_manifest"
        if args.result:
            write_json(args.result, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["status"] in {"pass", "qualified", "authorized"} else 1
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 2
