import hashlib
from pathlib import Path

import pytest

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


def test_package_markdown_skill_definition_is_single_document(monkeypatch, tmp_path: Path) -> None:
    package_root = tmp_path / "installed" / "one_document"
    (package_root / "skills").mkdir(parents=True)
    (package_root / "package_manifest.yaml").write_text(
        """package_id: xrefkit.skills.one_document
package_type: skill_package
version: 0.1.0
requires:
  xrefkit_core: '>=2.0.0 <3.0.0'
provides:
  skills:
    - id: one_document
      xid: ABCDEF123456
      path: skills/one_document.md
      required_outputs: [result]
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
    document = """---
schema_version: 1
skill_id: one_document
xid: ABCDEF123456
summary: A packaged one document Skill
applies_when: [one document task]
exclusions: []
inputs: [task]
outputs: [result]
criteria:
  - id: complete
    statement: result is complete
    verification: inspect result
knowledge_needs: []
control_refs: ['111111111111']
---
<!-- xid: ABCDEF123456 -->
<a id="xid-ABCDEF123456"></a>

# One document

Perform the task.
"""
    skill_path = package_root / "skills" / "one_document.md"
    raw = b"\xef\xbb\xbf" + document.encode("utf-8")
    skill_path.write_bytes(raw)
    package = DiscoveredSkillPackage(
        entry_point_name="one_document",
        package_root=package_root,
        manifest_path=package_root / "package_manifest.yaml",
        manifest=load_package_manifest(package_root / "package_manifest.yaml"),
    )
    monkeypatch.setattr(catalog_module, "discover_skill_packages", lambda: [package])
    repo = tmp_path / "repo"
    repo.mkdir()
    catalog = XRefCatalog.build(repo, discover_packages=True)
    entry = next(item for item in catalog.list_skills() if item["skill_id"] == "one_document")
    assert entry["definition_format"] == "skill_definition_v1"
    assert entry["definition_xid"] == "ABCDEF123456"
    assert entry["definition_content_hash"] == hashlib.sha256(raw).hexdigest()
    assert entry["package_id"] == "xrefkit.skills.one_document"
    result = catalog.get_skill("one_document", {})
    assert len(result["documents"]) == 1
    assert result["documents"][0]["content"].encode("utf-8") == raw
    assert result["documents"][0]["xid"] == "ABCDEF123456"

    package.manifest.provides.skills[0].xid = "111111111111"
    with pytest.raises(ValueError, match="identity does not match manifest"):
        XRefCatalog.build(repo, discover_packages=True).list_skills()
