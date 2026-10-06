"""Source receipts and on-demand resolution for the approved criteria split."""
import hashlib
from pathlib import Path
import shutil

import pytest

from xrefkit.mcp.catalog import XRefCatalog


ROOT = Path(__file__).resolve().parents[1]
CORE = "5F21C8A41001"
# Digests of the original normative sections, not the new routing prose.
TOPICS = [
    ("101_resource_efficiency_review.md", "5F21C8A41101", "Resource Efficiency Review", "c07e30affa9004a745fd4d52f88dab96e52904575a4e20ad52f7ead93b64d152"),
    ("102_operational_resilience_review.md", "5F21C8A41102", "Operational Hazard Taxonomy", "2aa23a748d10e2454089bf006dfa0f6a0ed099701c2913ecb99e71edb6105759"),
    ("103_synchronization_concurrency_review.md", "5F21C8A41103", "Synchronization And Concurrency Review", "99fdd558e34fd1a88108c1b6b38f66a880b1c025bee73826a3c99a99d8f4afab"),
    ("104_required_input_integrity_review.md", "5F21C8A41104", "Required Input Integrity Review", "211af9a09b23f75507638be850743ebfac5131b6cdd0b7486bd41f654329edfe"),
    ("105_error_exception_path_review.md", "5F21C8A41105", "Error Handling And Exception Path Review", "c940937faac9c00caa540399b0fb83e2aa0683803550697cb17f226959703b2d"),
    ("106_time_culture_review.md", "5F21C8A41106", "Time And Culture Review", "e6e8e90f1757104570532c1f72d8f879b411d5f96da4963a68dbe1ff8962df9f"),
    ("107_state_determinism_review.md", "5F21C8A41107", "State And Determinism Boundary Review", "ad8154ce5858f28bc31467aebcf59961e3f83bb0f7f7bd75be80853509b81c77"),
    ("108_uncertainty_escalation_review.md", "5F21C8A41108", "Uncertainty And Escalation Path Review", "51a0bd8df66c0594508bc3f2ccf34258b041fe5259e26d7bba8d86aeee6fec85"),
    ("109_contract_schema_resilience_review.md", "5F21C8A41109", "Contract And Schema Resilience Review", "8e2f18d75a62e61d246c4de4509ef68569455c73c30f605e3a1bfc9879de1d0e"),
    ("112_trace_context_propagation_review.md", "5F21C8A41110", "Traceability And Context Propagation Review", "f1568abc2d40ba2b884fd598ca8cb1c1762c13b19c1065a52bd05d3cb9eb47b0"),
    ("113_overload_resource_source_basis.md", "5F21C8A41111", "Overload And Resource-Control Source Basis", "8ab7ef1ca0d3adccad8b302f9e3ec50f9bf186edb1eb4c2bf7282ac6aa184610"),
]


@pytest.mark.parametrize("name,xid,heading,digest", TOPICS)
def test_normative_sections_retain_original_source_receipts(name, xid, heading, digest):
    text = (ROOT / "knowledge/source_analysis" / name).read_text(encoding="utf-8")
    body = text.split("## " + heading + "\n", 1)[1]
    body = "## " + heading + "\n" + body.split("\n## Knowledge Relations", 1)[0]
    body = body.split("\nWhen the same resource pattern", 1)[0].rstrip() + "\n"
    assert hashlib.sha256(body.encode()).hexdigest() == digest
    assert f"<!-- xid: {xid} -->" in text
    assert f"#xid-{CORE}" in text
    # No alternative copies are canonicalized by this split.
    for other_name, _, _, _ in TOPICS:
        if other_name != name:
            other = (ROOT / "knowledge/source_analysis" / other_name).read_text(encoding="utf-8")
            assert body not in other


@pytest.fixture
def catalog(tmp_path):
    target = tmp_path / "knowledge/source_analysis"
    target.mkdir(parents=True)
    for name in ["100_common_source_analysis_criteria.md", *[t[0] for t in TOPICS]]:
        shutil.copyfile(ROOT / "knowledge/source_analysis" / name, target / name)
    return XRefCatalog.build(tmp_path, discover_packages=False)


def test_old_entry_point_and_narrow_load_do_not_materialize_all_criteria(catalog):
    core = catalog.get_document_by_xid(CORE)
    assert "## Core Viewpoints" in core["content"]
    assert "## Planning Rule" in core["content"]
    assert "If a core viewpoint cannot be confirmed" in core["content"]
    assert "Do not invent a cleaner target structure" in core["content"]
    assert len(core["content"].splitlines()) < 80
    assert "Shared resource exhaustion:" not in core["content"]
    assert "When code uses a virtual clock" not in core["content"]
    error = catalog.get_document_by_xid("5F21C8A41105")
    narrow = core["content"] + error["content"]
    assert "Findings must name the failure path concretely" in narrow
    assert "usage-dependent" not in narrow.lower()
    assert "## Required Input Result Facts" not in narrow
    cached = catalog.get_document_by_xid(CORE, core["content_hash"])
    assert cached["content_omitted"] is True
    assert "content" not in cached
    assert (cached["xid"], cached["content_hash"]) == (CORE, core["content_hash"])
    assert catalog.get_document_by_xid(CORE)["content"] == core["content"]


def test_language_overlays_keep_all_active_axis_requirements():
    for language in ["csharp", "python"]:
        text = (ROOT / f"knowledge/{language}/100_{language}_review_spec.md").read_text(encoding="utf-8")
        assert f"#xid-{CORE}" in text
        assert all(f"#xid-{xid}" in text for _, xid, _, _ in TOPICS[:10])
        assert "headline" in text or "every required category" in text


def test_resource_source_basis_is_required_without_an_operational_incident(catalog):
    for xid in ["5F21C8A41101", "5F21C8A41102"]:
        body = catalog.get_document_by_xid(xid)["content"]
        assert "#xid-5F21C8A41111" in body
        assert "required even without a confirmed incident" in body
    basis = catalog.get_document_by_xid("5F21C8A41111")["content"]
    assert "Use these source-backed lenses when reviewing resource consumption" in basis
    assert "operational resilience" in basis
    assert "CWE-400" in basis


def test_semantic_cycle_and_diamond_links_are_not_load_commands(catalog):
    path = catalog.repo_root / "knowledge/source_analysis/100_common_source_analysis_criteria.md"
    # Both branches already point back to CORE; repeated diamond lookup handles
    # and a semantic cycle must not become recursive body expansion.
    with path.open("a", encoding="utf-8") as stream:
        stream.write("\n## Knowledge Relations\n- related_to: [errors](105_error_exception_path_review.md#xid-5F21C8A41105)\n")
    body = catalog.get_document_by_xid(CORE)["content"]
    assert "Findings must name the failure path concretely" not in body
    assert "Shared resource exhaustion:" not in body


def test_missing_and_duplicate_knowledge_identity_do_not_silently_resolve(catalog):
    path = catalog.repo_root / "knowledge/source_analysis/105_error_exception_path_review.md"
    path.unlink()
    with pytest.raises(KeyError):
        catalog.get_document_by_xid("5F21C8A41105")
    path.write_text(f"<!-- xid: {CORE} -->\n# Conflicting criteria\n", encoding="utf-8")
    conflict = catalog.get_document_by_xid(CORE)
    assert conflict["error"] == "xid_conflict"
    assert "content" not in conflict
