from __future__ import annotations

from pathlib import Path

import yaml

from xrefkit.structure_catalog import list_findings, list_targets, load_catalog, maintain_catalog


def _catalog(tmp_path: Path) -> Path:
    path = tmp_path / "knowledge/source_analysis/source_structure_catalog.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.safe_dump({"schema": "xrefkit.source_structure_catalog/v1", "targets": [], "findings": []}, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_maintain_promotes_explicit_candidate_once(tmp_path: Path) -> None:
    catalog_path = _catalog(tmp_path)
    report = tmp_path / "work/reports/order.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Order structure\n", encoding="utf-8")
    inbox = tmp_path / "work/inbox/source_structure_findings"
    inbox.mkdir(parents=True)
    receipt = {
        "schema": "xrefkit.source_structure_candidate/v1",
        "candidate_xid": "A1234567890B",
        "artifact_path": "work/reports/order.md",
        "repository_identity": "repo:orders",
        "source_scope": "src/Orders",
        "target_kind": "python_package",
        "target_name": "Orders",
        "source_revision": "abc123",
        "producer_skill": "source_structure_overview",
        "analyzed_at": "2026-07-10",
        "coverage": "entry points and persistence",
        "unresolved_verification": "runtime execution",
    }
    receipt_path = inbox / "candidate.yaml"
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    first = maintain_catalog(tmp_path, catalog_path.relative_to(tmp_path), inbox.relative_to(tmp_path), apply_safe=True)
    second = maintain_catalog(tmp_path, catalog_path.relative_to(tmp_path), inbox.relative_to(tmp_path), apply_safe=True)

    assert first["registered"] == 1
    assert second["registered"] == 0
    catalog = load_catalog(catalog_path)
    assert len(list_targets(catalog)) == 1
    target_xid = catalog["targets"][0]["target_xid"]
    assert len(list_findings(catalog, target_xid)) == 1
    assert (tmp_path / catalog["findings"][0]["detail_path"]).is_file()


def test_maintain_does_not_promote_without_apply_safe(tmp_path: Path) -> None:
    catalog_path = _catalog(tmp_path)
    report = tmp_path / "work/reports/order.md"
    report.parent.mkdir(parents=True)
    report.write_text("# Order structure\n", encoding="utf-8")
    inbox = tmp_path / "work/inbox/source_structure_findings"
    inbox.mkdir(parents=True)
    receipt = {
        "schema": "xrefkit.source_structure_candidate/v1",
        "candidate_xid": "A1234567890B",
        "artifact_path": "work/reports/order.md",
        "repository_identity": "repo:orders",
        "source_scope": "src/Orders",
        "target_kind": "python_package",
        "source_revision": "abc123",
        "producer_skill": "source_structure_overview",
        "analyzed_at": "2026-07-10",
    }
    (inbox / "candidate.yaml").write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")

    result = maintain_catalog(tmp_path, catalog_path.relative_to(tmp_path), inbox.relative_to(tmp_path), apply_safe=False)

    assert result["pending_review"] == 1
    assert load_catalog(catalog_path)["findings"] == []
