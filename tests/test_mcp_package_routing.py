from pathlib import Path

from xrefkit.discovery import DiscoveredSkillPackage
from xrefkit.loaders import load_package_manifest
from xrefkit.mcp import catalog as catalog_module
from xrefkit.mcp.catalog import XRefCatalog


def test_installed_skill_package_is_registered_for_mcp_routing(monkeypatch, tmp_path: Path) -> None:
    package_root = tmp_path / "installed" / "xrefkit_skills_brownfield"
    (package_root / "skills" / "brownfield_workflow").mkdir(parents=True)
    (package_root / "review_axes").mkdir()
    (package_root / "package_manifest.yaml").write_text(
        """package_id: xrefkit.skills.brownfield
package_type: skill_package
version: 0.1.4
requires:
  xrefkit_core: '>=2.0.0 <3.0.0'
provides:
  skills:
    - id: brownfield.workflow
      xid: xid-skill-brownfield-workflow
      path: skills/brownfield_workflow.skill.yaml
      required_outputs: [phase_summary]
      required_knowledge: []
  fragments: []
  knowledge: []
  review_axes: []
  schemas: []
  templates: []
contract: {}
""",
        encoding="utf-8",
    )
    (package_root / "skills" / "brownfield_workflow.skill.yaml").write_text(
        """skill_id: brownfield.workflow
xid: xid-skill-brownfield-workflow
entry:
  xid: xid-entry-brownfield-workflow
  path: skills/brownfield_workflow/entry.md
  load_policy: required_inline
required_outputs: [phase_summary]
required_knowledge: []
review_axes: []
schemas: []
must_not: []
extension_policy: {}
""",
        encoding="utf-8",
    )
    (package_root / "skills" / "brownfield_workflow" / "entry.md").write_text(
        "# Brownfield Workflow\n\nCarry a brownfield change through planning and testing.\n",
        encoding="utf-8",
    )
    package = DiscoveredSkillPackage(
        entry_point_name="brownfield",
        package_root=package_root,
        manifest_path=package_root / "package_manifest.yaml",
        manifest=load_package_manifest(package_root / "package_manifest.yaml"),
    )
    monkeypatch.setattr(catalog_module, "discover_skill_packages", lambda: [package])

    repo = tmp_path / "repo"
    repo.mkdir()
    catalog = XRefCatalog.build(repo, discover_packages=True)
    listed = catalog.list_skills()
    ranked = catalog.rank_skills_for_purpose("brownfield change planning")

    assert any(item["skill_id"] == "brownfield.workflow" for item in listed)
    result = next(item for item in ranked if item["skill_id"] == "brownfield.workflow")
    assert result["score"] > 0
    assert result["matched_facets"]
    assert catalog.get_skill("brownfield.workflow")["package_id"] == "xrefkit.skills.brownfield"
