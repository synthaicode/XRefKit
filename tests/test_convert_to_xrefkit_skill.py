from __future__ import annotations

import re
import tempfile
from pathlib import Path

from tools.check_skill_knowledge_xids import check_skill_knowledge_xids
from xrefkit import import_skill as convert_module


def test_convert_external_skill_copies_referenced_files_to_knowledge() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        source = Path(tmp) / "external_skill"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text(
            "# External Skill\n\n"
            "Use [Policy](policy.md) and [Examples](refs/examples.txt).\n",
            encoding="utf-8",
        )
        (source / "policy.md").write_text("# Policy\n\nExternal policy body.\n", encoding="utf-8")
        (source / "refs").mkdir()
        (source / "refs" / "examples.txt").write_text("Example body.\n", encoding="utf-8")

        result = convert_module.convert_skill(
            source_dir=source,
            repo_root=root,
            skill_id="external.sample",
        )

        assert result.ok
        skill_doc = root / "skills_private" / "external.sample" / "SKILL.md"
        meta_doc = root / "skills_private" / "external.sample" / "meta.md"
        policy_doc = root / "knowledge" / "imported_skills" / "external.sample" / "policy.md"
        examples_doc = root / "knowledge" / "imported_skills" / "external.sample" / "refs" / "examples.md"

        assert skill_doc.exists()
        assert meta_doc.exists()
        assert policy_doc.exists()
        assert examples_doc.exists()

        skill_text = skill_doc.read_text(encoding="utf-8")
        policy_text = policy_doc.read_text(encoding="utf-8")
        examples_text = examples_doc.read_text(encoding="utf-8")
        meta_text = meta_doc.read_text(encoding="utf-8")

        assert re.search(r"knowledge/imported_skills/external\.sample/policy\.md#xid-[A-F0-9]{12}", skill_text)
        assert re.search(r"knowledge/imported_skills/external\.sample/refs/examples\.md#xid-[A-F0-9]{12}", skill_text)
        assert "<!-- xid:" in policy_text
        assert "<!-- xid:" in examples_text
        assert "imported_from: `policy.md`" in policy_text
        assert "imported_from: `refs/examples.txt`" in examples_text
        assert "- knowledge_slots:" in meta_text
        assert "bind=" in meta_text

        check = check_skill_knowledge_xids(root=root, scope="all", targets=["skills_private/external.sample"])
        assert check.ok, [finding.to_dict() for finding in check.errors]


def test_convert_external_skill_dry_run_does_not_write_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        source = Path(tmp) / "external_skill"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("# External Skill\n\nSee [Policy](policy.md).\n", encoding="utf-8")
        (source / "policy.md").write_text("# Policy\n\nExternal policy body.\n", encoding="utf-8")

        result = convert_module.convert_skill(
            source_dir=source,
            repo_root=root,
            skill_id="external.sample",
            dry_run=True,
        )

        assert result.ok
        assert result.dry_run
        assert result.changed_files
        assert not (root / "skills_private").exists()
        assert not (root / "knowledge").exists()


def test_convert_external_skill_tree_processes_skills_and_shared_knowledge() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        source = Path(tmp) / "external"
        (source / "skills" / "alpha").mkdir(parents=True)
        (source / "skills" / "beta").mkdir(parents=True)
        (source / "knowledge").mkdir()
        (source / "skills" / "alpha" / "SKILL.md").write_text(
            "# Alpha\n\nUse [Shared](../../knowledge/shared.md).\n",
            encoding="utf-8",
        )
        (source / "skills" / "beta" / "README.md").write_text(
            "# Beta\n\nUse [Shared](../../knowledge/shared.md).\n",
            encoding="utf-8",
        )
        (source / "knowledge" / "shared.md").write_text("# Shared\n\nShared body.\n", encoding="utf-8")

        result = convert_module.convert_skill_tree(
            source_root=source,
            repo_root=root,
            skill_id_prefix="external",
        )

        assert result.ok
        assert len(result.converted_skills) == 2

        alpha_doc = root / "skills_private" / "external.alpha" / "SKILL.md"
        beta_doc = root / "skills_private" / "external.beta" / "SKILL.md"
        shared_doc = root / "knowledge" / "imported_skills" / "external" / "shared.md"

        assert alpha_doc.exists()
        assert beta_doc.exists()
        assert shared_doc.exists()

        alpha_text = alpha_doc.read_text(encoding="utf-8")
        beta_text = beta_doc.read_text(encoding="utf-8")
        shared_text = shared_doc.read_text(encoding="utf-8")
        shared_xid = re.search(r"<!-- xid: ([A-F0-9]{12}) -->", shared_text)
        assert shared_xid is not None
        assert f"knowledge/imported_skills/external/shared.md#xid-{shared_xid.group(1)}" in alpha_text
        assert f"knowledge/imported_skills/external/shared.md#xid-{shared_xid.group(1)}" in beta_text
        assert "imported_from: `knowledge/shared.md`" in shared_text

        check = check_skill_knowledge_xids(
            root=root,
            scope="all",
            targets=["skills_private/external.alpha", "skills_private/external.beta"],
        )
        assert check.ok, [finding.to_dict() for finding in check.errors]


def test_convert_external_skill_tree_imports_lowercase_skill_doc_and_mixed_xid_refs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        source = Path(tmp) / "external"
        skill = source / "skills" / "mixed"
        skill.mkdir(parents=True)
        (source / "knowledge").mkdir()
        (skill / "refs").mkdir()
        (skill / "skill.md").write_text(
            "# Mixed Skill\n\n"
            "Use [Local XID](refs/local-xid.md), [Local Missing](refs/local-missing.md), "
            "and [Shared Knowledge](../../knowledge/shared.md).\n",
            encoding="utf-8",
        )
        (skill / "refs" / "local-xid.md").write_text(
            "<!-- xid: ABCDEF123456 -->\n"
            '<a id="xid-ABCDEF123456"></a>\n\n'
            "# Local XID\n\nAlready identified.\n",
            encoding="utf-8",
        )
        (skill / "refs" / "local-missing.md").write_text(
            "# Local Missing\n\nNeeds an XID.\n",
            encoding="utf-8",
        )
        (source / "knowledge" / "shared.md").write_text(
            "<!-- xid: FACE1234BEEF -->\n"
            '<a id="xid-FACE1234BEEF"></a>\n\n'
            "# Shared Knowledge\n\nAlready shared.\n",
            encoding="utf-8",
        )

        result = convert_module.convert_skill_tree(
            source_root=source,
            repo_root=root,
            skill_id_prefix="external",
        )

        assert result.ok
        assert len(result.converted_skills) == 1

        skill_doc = root / "skills_private" / "external.mixed" / "SKILL.md"
        meta_doc = root / "skills_private" / "external.mixed" / "meta.md"
        local_xid_doc = root / "knowledge" / "imported_skills" / "external" / "skills" / "mixed" / "refs" / "local-xid.md"
        local_missing_doc = root / "knowledge" / "imported_skills" / "external" / "skills" / "mixed" / "refs" / "local-missing.md"
        shared_doc = root / "knowledge" / "imported_skills" / "external" / "shared.md"

        skill_text = skill_doc.read_text(encoding="utf-8")
        meta_text = meta_doc.read_text(encoding="utf-8")
        local_xid_text = local_xid_doc.read_text(encoding="utf-8")
        local_missing_text = local_missing_doc.read_text(encoding="utf-8")
        shared_text = shared_doc.read_text(encoding="utf-8")

        assert "#xid-ABCDEF123456" in skill_text
        assert "#xid-FACE1234BEEF" in skill_text
        assert re.search(r"local-missing\.md#xid-[A-F0-9]{12}", skill_text)
        assert "<!-- xid: ABCDEF123456 -->" in local_xid_text
        assert "<!-- xid: FACE1234BEEF -->" in shared_text
        assert re.search(r"<!-- xid: [A-F0-9]{12} -->", local_missing_text)
        assert "bind=ABCDEF123456" in meta_text
        assert "bind=FACE1234BEEF" in meta_text

        check = check_skill_knowledge_xids(
            root=root,
            scope="all",
            targets=["skills_private/external.mixed"],
        )
        assert check.ok, [finding.to_dict() for finding in check.errors]
