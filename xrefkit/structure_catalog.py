"""List-first source target/finding catalog and safe candidate promotion."""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


SCHEMA = "xrefkit.source_structure_catalog/v1"
RECEIPT_SCHEMA = "xrefkit.source_structure_candidate/v1"
XID_RE = re.compile(r"^[A-F0-9]{12}$")


def load_catalog(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("unsupported source structure catalog")
    return data


def save_catalog(path: str | Path, catalog: dict[str, Any]) -> None:
    Path(path).write_text(yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _safe_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _safe_value(item) for key, item in value.items()}
    return value


def list_targets(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return [_safe_value(dict(item)) for item in catalog.get("targets", [])]


def list_findings(catalog: dict[str, Any], target_xid: str) -> list[dict[str, Any]]:
    key = target_xid.upper()
    return [_safe_value(dict(item)) for item in catalog.get("findings", []) if str(item.get("target_xid", "")).upper() == key]


def get_entry(catalog: dict[str, Any], xid: str) -> dict[str, Any]:
    key = xid.upper()
    for collection, field in (("targets", "target_xid"), ("findings", "finding_xid")):
        for item in catalog.get(collection, []):
            if str(item.get(field, "")).upper() == key:
                return _safe_value({"kind": collection[:-1], **dict(item)})
    raise KeyError(f"unknown catalog XID: {xid}")


def _target_identity(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(item.get("repository_identity", "")).strip(),
        str(item.get("source_scope", "")).strip(),
        str(item.get("target_kind", "")).strip(),
    )


def _derived_xid(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:12].upper()


def _validate_receipt(receipt: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema") != RECEIPT_SCHEMA:
        errors.append("unsupported receipt schema")
    required = (
        "candidate_xid", "artifact_path", "repository_identity", "source_scope",
        "target_kind", "source_revision", "producer_skill", "analyzed_at",
    )
    for field in required:
        if not str(receipt.get(field, "")).strip():
            errors.append(f"missing {field}")
    xid = str(receipt.get("candidate_xid", "")).upper()
    if xid and not XID_RE.fullmatch(xid):
        errors.append("candidate_xid must be 12 hexadecimal characters")
    artifact = root / str(receipt.get("artifact_path", ""))
    if not artifact.is_file():
        errors.append(f"artifact not found: {artifact}")
    return errors


def maintain_catalog(
    root: str | Path,
    catalog_path: str | Path,
    inbox: str | Path,
    *,
    apply_safe: bool,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    catalog_file = root_path / catalog_path
    catalog = load_catalog(catalog_file)
    results: list[dict[str, Any]] = []
    changed = False
    for receipt_path in sorted((root_path / inbox).glob("*.yaml")):
        receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict):
            results.append({"receipt": str(receipt_path), "status": "invalid", "errors": ["receipt is not a mapping"]})
            continue
        errors = _validate_receipt(receipt, root_path)
        identity = _target_identity(receipt)
        matches = [item for item in catalog.get("targets", []) if _target_identity(item) == identity]
        if len(matches) > 1:
            errors.append("multiple targets match receipt identity")
        finding_xid = str(receipt.get("candidate_xid", "")).upper()
        if any(str(item.get("finding_xid", "")).upper() == finding_xid for item in catalog.get("findings", [])):
            results.append({"receipt": str(receipt_path), "status": "already_registered", "finding_xid": finding_xid})
            continue
        if errors or not apply_safe:
            results.append({
                "receipt": str(receipt_path),
                "status": "pending_review" if not errors else "invalid",
                "errors": errors,
            })
            continue
        if matches:
            target = matches[0]
        else:
            target_xid = str(receipt.get("target_xid", "")).upper() or _derived_xid(*identity)
            target = {
                "target_xid": target_xid,
                "name": str(receipt.get("target_name") or receipt.get("target_hint") or identity[1]),
                "repository_identity": identity[0],
                "source_scope": identity[1],
                "target_kind": identity[2],
                "aliases": list(receipt.get("aliases") or []),
            }
            catalog.setdefault("targets", []).append(target)
        artifact = root_path / str(receipt["artifact_path"])
        slug = re.sub(r"[^a-z0-9]+", "_", str(target["name"]).lower()).strip("_") or "target"
        detail_relative = Path("knowledge/source_analysis") / f"{finding_xid.lower()}_{slug}_structure_findings.md"
        detail = root_path / detail_relative
        body = artifact.read_text(encoding="utf-8")
        if f"xid: {finding_xid}" not in body:
            body = f'<!-- xid: {finding_xid} -->\n<a id="xid-{finding_xid}"></a>\n\n' + body
        detail.parent.mkdir(parents=True, exist_ok=True)
        detail.write_text(body, encoding="utf-8")
        finding = {
            "finding_xid": finding_xid,
            "target_xid": target["target_xid"],
            "title": str(receipt.get("title") or f"{target['name']} structure findings"),
            "analysis_kinds": list(receipt.get("analysis_kinds") or ["source_structure"]),
            "status": "current",
            "source_revision": str(receipt["source_revision"]),
            "last_verified": str(receipt["analyzed_at"]),
            "coverage": str(receipt.get("coverage") or "See canonical finding detail."),
            "unresolved_verification": str(receipt.get("unresolved_verification") or "None recorded."),
            "detail_path": detail_relative.as_posix(),
        }
        catalog.setdefault("findings", []).append(finding)
        receipt["status"] = "registered"
        receipt["target_xid"] = target["target_xid"]
        receipt["canonical_detail_path"] = detail_relative.as_posix()
        receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False, allow_unicode=True), encoding="utf-8")
        results.append({"receipt": str(receipt_path), **finding, "processing_status": "registered"})
        changed = True
    if changed:
        save_catalog(catalog_file, catalog)
    return {
        "ok": all(item["status"] not in {"invalid"} for item in results),
        "changed": changed,
        "results": results,
        "registered": sum(item.get("processing_status") == "registered" for item in results),
        "pending_review": sum(item["status"] == "pending_review" for item in results),
    }


def reconcile_receipts(root: str | Path, reports: str | Path, inbox: str | Path) -> dict[str, Any]:
    root_path = Path(root).resolve()
    inbox_path = root_path / inbox
    inbox_path.mkdir(parents=True, exist_ok=True)
    existing = {
        str(data.get("artifact_path"))
        for path in inbox_path.glob("*.yaml")
        if isinstance((data := yaml.safe_load(path.read_text(encoding="utf-8"))), dict)
    }
    created: list[str] = []
    pattern = re.compile(r"^candidate_xid:\s*([A-Fa-f0-9]{12})\s*$", re.MULTILINE)
    for report in sorted((root_path / reports).glob("*.md")):
        relative = report.relative_to(root_path).as_posix()
        if relative in existing:
            continue
        text = report.read_text(encoding="utf-8")
        match = pattern.search(text[:2000])
        if not match:
            continue
        xid = match.group(1).upper()
        receipt = {"schema": RECEIPT_SCHEMA, "candidate_xid": xid, "artifact_path": relative, "status": "incomplete"}
        target = inbox_path / f"{date.today().isoformat()}_{xid}.yaml"
        target.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")
        created.append(str(target))
    return {"ok": True, "created": created, "count": len(created)}
