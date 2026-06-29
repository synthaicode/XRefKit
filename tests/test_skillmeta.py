import tempfile
import unittest
from pathlib import Path

from fm.skillmeta import (
    GUARD_CAPABILITY_REF,
    GUARD_KNOWLEDGE_REF,
    REQUIRED_OS_CONTRACT,
    SKILL_RUNTIME_CAPABILITY_REF,
    build_skill_merge_plan,
    validate_skill_meta,
)


class SkillMetaTests(unittest.TestCase):
    def _os_contract_block(self) -> str:
        lines = ["- os_contract:\n"]
        for key, value in REQUIRED_OS_CONTRACT.items():
            lines.append(f"  - {key}: `{value}`\n")
        return "".join(lines)

    def test_validate_skill_meta_accepts_required_guard_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "meta.md"
            meta.write_text(
                "# Skill Meta: sample\n\n"
                "- skill_id: `sample_skill`\n"
                "- summary: sample summary\n"
                "- use_when: sample use\n"
                "- input: sample input\n"
                "- output: sample output\n"
                "- maturity: `stable`\n"
                "- execution_mode: `subagent_preferred`\n"
                "- guard_policy: `required`\n"
                "- capability_layering: `required`\n"
                "- workflow_protocol: `required`\n"
                "- tuning: sample specialization\n"
                "- role_responsibilities:\n"
                "  - executor: sample execution responsibility\n"
                "  - quality_reviewer: sample quality responsibility\n"
                "  - handoff_owner: sample handoff responsibility\n"
                f"{self._os_contract_block()}"
                "- constraints: keep observed boundary explicit\n"
                "- skill_doc: `./SKILL.md`\n"
                "- capability_refs:\n"
                f"  - `{SKILL_RUNTIME_CAPABILITY_REF}`\n"
                f"  - `{GUARD_CAPABILITY_REF}`\n"
                "- knowledge_refs:\n"
                f"  - `{GUARD_KNOWLEDGE_REF}`\n"
                "- observation_refs:\n"
                "  - `../../work/sessions/sample.md`\n",
                encoding="utf-8",
            )

            result = validate_skill_meta(meta)

            self.assertTrue(result.ok)
            self.assertEqual([], result.errors)

    def test_validate_skill_meta_rejects_missing_os_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "meta.md"
            meta.write_text(
                "# Skill Meta: sample\n\n"
                "- skill_id: `sample_skill`\n"
                "- summary: sample summary\n"
                "- use_when: sample use\n"
                "- input: sample input\n"
                "- output: sample output\n"
                "- maturity: `stable`\n"
                "- execution_mode: `subagent_preferred`\n"
                "- guard_policy: `required`\n"
                "- capability_layering: `required`\n"
                "- workflow_protocol: `required`\n"
                "- tuning: sample specialization\n"
                "- role_responsibilities:\n"
                "  - executor: sample execution responsibility\n"
                "  - quality_reviewer: sample quality responsibility\n"
                "  - handoff_owner: sample handoff responsibility\n"
                "- constraints: keep observed boundary explicit\n"
                "- skill_doc: `./SKILL.md`\n"
                "- capability_refs:\n"
                f"  - `{SKILL_RUNTIME_CAPABILITY_REF}`\n"
                f"  - `{GUARD_CAPABILITY_REF}`\n"
                "- knowledge_refs:\n"
                f"  - `{GUARD_KNOWLEDGE_REF}`\n"
                "- observation_refs:\n"
                "  - `../../work/sessions/sample.md`\n",
                encoding="utf-8",
            )

            result = validate_skill_meta(meta)

            self.assertFalse(result.ok)
            self.assertIn("os_contract.version must be 1", result.errors)

    def test_validate_skill_meta_rejects_review_skill_with_local_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "meta.md"
            meta.write_text(
                "# Skill Meta: review\n\n"
                "- skill_id: `quality_review`\n"
                "- summary: review the output carefully\n"
                "- use_when: review is needed\n"
                "- input: review target\n"
                "- output: review result\n"
                "- maturity: `stable`\n"
                "- execution_mode: `local_default`\n"
                "- guard_policy: `closed_world`\n"
                "- capability_layering: `required`\n"
                "- workflow_protocol: `required`\n"
                "- tuning: review specialization\n"
                "- role_responsibilities:\n"
                "  - executor: review execution responsibility\n"
                "  - quality_reviewer: review quality responsibility\n"
                "  - handoff_owner: review handoff responsibility\n"
                f"{self._os_contract_block()}"
                "- constraints: explicit closed-world execution\n"
                "- skill_doc: `./SKILL.md`\n"
                "- capability_refs:\n"
                f"  - `{SKILL_RUNTIME_CAPABILITY_REF}`\n"
                "- observation_refs:\n"
                "  - `../../work/sessions/review.md`\n",
                encoding="utf-8",
            )

            result = validate_skill_meta(meta)

            self.assertFalse(result.ok)
            self.assertIn(
                "review-oriented skills must use subagent_preferred or subagent_required",
                result.errors,
            )

    def test_validate_skill_meta_accepts_draft_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "meta.md"
            meta.write_text(
                "# Skill Meta: draft\n\n"
                "- skill_id: `draft_skill`\n"
                "- summary: draft summary\n"
                "- use_when: early hypothesis\n"
                "- input: rough input hypothesis\n"
                "- output: rough output hypothesis\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
                encoding="utf-8",
            )

            result = validate_skill_meta(meta)

            self.assertTrue(result.ok)
            self.assertEqual("draft", result.maturity)
            self.assertEqual("draft", result.checked_level)

    def test_validate_skill_meta_rejects_trial_without_observation_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "meta.md"
            meta.write_text(
                "# Skill Meta: trial\n\n"
                "- skill_id: `trial_skill`\n"
                "- summary: trial summary\n"
                "- use_when: observed use\n"
                "- input: observed input\n"
                "- output: observed output\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `trial`\n",
                encoding="utf-8",
            )

            result = validate_skill_meta(meta)

            self.assertFalse(result.ok)
            self.assertIn(
                "trial-or-higher skills must include at least one observation_refs entry",
                result.errors,
            )

    def test_validate_skill_meta_rejects_governed_without_governance_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / "meta.md"
            meta.write_text(
                "# Skill Meta: governed\n\n"
                "- skill_id: `governed_skill`\n"
                "- summary: governed summary\n"
                "- use_when: governed use\n"
                "- input: governed input\n"
                "- output: governed output\n"
                "- maturity: `governed`\n"
                "- execution_mode: `subagent_preferred`\n"
                "- guard_policy: `required`\n"
                "- capability_layering: `required`\n"
                "- workflow_protocol: `required`\n"
                "- tuning: governed specialization\n"
                "- role_responsibilities:\n"
                "  - executor: governed execution responsibility\n"
                "  - quality_reviewer: governed quality responsibility\n"
                "  - handoff_owner: governed handoff responsibility\n"
                f"{self._os_contract_block()}"
                "- constraints: keep governed boundary explicit\n"
                "- skill_doc: `./SKILL.md`\n"
                "- capability_refs:\n"
                f"  - `{SKILL_RUNTIME_CAPABILITY_REF}`\n"
                f"  - `{GUARD_CAPABILITY_REF}`\n"
                "- knowledge_refs:\n"
                f"  - `{GUARD_KNOWLEDGE_REF}`\n"
                "- observation_refs:\n"
                "  - `../../work/sessions/governed.md`\n",
                encoding="utf-8",
            )

            result = validate_skill_meta(meta)

            self.assertFalse(result.ok)
            self.assertIn("governed skills must include at least one governance_refs entry", result.errors)

    def test_skill_merge_plan_adopts_distinct_legacy_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "work" / "imports" / "legacy"
            source.mkdir(parents=True)
            (source / "meta.md").write_text(
                "# Legacy Meta\n\n"
                "- skill_id: `legacy_skill`\n"
                "- summary: old skill\n"
                "- use_when: old use\n"
                "- input: old input\n"
                "- output: old output\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
                encoding="utf-8",
            )
            (source / "SKILL.md").write_text(
                "<!-- xid: LEGACY123456 -->\n<a id=\"xid-LEGACY123456\"></a>\n\n# Legacy\n",
                encoding="utf-8",
            )

            plan = build_skill_merge_plan(root=root, source=source)

            self.assertEqual("adopt", plan["classification"]["proposed"])
            self.assertEqual("legacy_skill", plan["identity"]["source_skill_id"])
            self.assertIn("LEGACY123456", plan["identity"]["source_xids"])

    def test_skill_merge_plan_merges_exact_skill_id_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "skills" / "legacy" / "meta.md"
            current.parent.mkdir(parents=True)
            current.write_text(
                "# Current Meta\n\n"
                "- skill_id: `legacy_skill`\n"
                "- summary: current skill\n"
                "- use_when: current use\n"
                "- input: current input\n"
                "- output: current output\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
                encoding="utf-8",
            )
            (current.parent / "SKILL.md").write_text("# Current\n", encoding="utf-8")
            source = root / "work" / "imports" / "legacy"
            source.mkdir(parents=True)
            (source / "meta.md").write_text(current.read_text(encoding="utf-8"), encoding="utf-8")
            (source / "SKILL.md").write_text("# Legacy\n", encoding="utf-8")

            plan = build_skill_merge_plan(root=root, source=source)

            self.assertEqual("merge", plan["classification"]["proposed"])
            self.assertEqual("exact_skill_id", plan["identity"]["candidate_targets"][0]["reasons"][0])

    def test_skill_merge_plan_does_not_match_referenced_xids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "skills" / "current" / "meta.md"
            current.parent.mkdir(parents=True)
            current.write_text(
                "# Current Meta\n\n"
                "- skill_id: `current_skill`\n"
                "- summary: current skill\n"
                "- use_when: current use\n"
                "- input: current input\n"
                "- output: current output\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
                encoding="utf-8",
            )
            (current.parent / "SKILL.md").write_text(
                "<!-- xid: CURRENTOWN123 -->\n# Current\n\nSee [Shared](../../docs/shared.md#xid-SHAREDREF123).\n",
                encoding="utf-8",
            )
            source = root / "work" / "imports" / "legacy"
            source.mkdir(parents=True)
            (source / "meta.md").write_text(
                "# Legacy Meta\n\n"
                "- skill_id: `legacy_skill`\n"
                "- summary: legacy skill\n"
                "- use_when: legacy use\n"
                "- input: legacy input\n"
                "- output: legacy output\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
                encoding="utf-8",
            )
            (source / "SKILL.md").write_text(
                "<!-- xid: LEGACYOWN123 -->\n# Legacy\n\nSee [Shared](../../docs/shared.md#xid-SHAREDREF123).\n",
                encoding="utf-8",
            )

            plan = build_skill_merge_plan(root=root, source=source)

            self.assertEqual("adopt", plan["classification"]["proposed"])
            self.assertEqual([], plan["identity"]["candidate_targets"])
            self.assertIn("LEGACYOWN123", plan["identity"]["source_xids"])
            self.assertIn("SHAREDREF123", plan["identity"]["referenced_xids"])

    def test_skill_merge_plan_splits_os_core_rule_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "work" / "imports" / "legacy"
            source.mkdir(parents=True)
            (source / "meta.md").write_text(
                "# Legacy Meta\n\n"
                "- skill_id: `mixed_skill`\n"
                "- summary: mixed skill\n"
                "- use_when: mixed use\n"
                "- input: mixed input\n"
                "- output: mixed output\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
                encoding="utf-8",
            )
            (source / "SKILL.md").write_text(
                "# Mixed\n\n## Domain Facts\n\nBusiness facts.\n\nStartup Xref Routing Policy\n",
                encoding="utf-8",
            )

            plan = build_skill_merge_plan(root=root, source=source)

            self.assertEqual("split", plan["classification"]["proposed"])
            self.assertIn("possible_os_core_rule_copy", plan["classification"]["reasons"])

    def test_skill_merge_plan_archives_non_skill_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "work" / "imports" / "not_skill"
            source.mkdir(parents=True)
            (source / "notes.txt").write_text("not a skill", encoding="utf-8")

            plan = build_skill_merge_plan(root=root, source=source)

            self.assertEqual("archive", plan["classification"]["proposed"])


if __name__ == "__main__":
    unittest.main()
