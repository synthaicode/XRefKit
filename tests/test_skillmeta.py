import tempfile
import unittest
from pathlib import Path

from fm.skillmeta import (
    GUARD_CAPABILITY_REF,
    GUARD_KNOWLEDGE_REF,
    REQUIRED_OS_CONTRACT,
    SKILL_RUNTIME_CAPABILITY_REF,
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


if __name__ == "__main__":
    unittest.main()
