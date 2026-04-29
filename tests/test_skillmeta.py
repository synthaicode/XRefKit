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
                "- execution_mode: `subagent_preferred`\n"
                "- guard_policy: `required`\n"
                f"{self._os_contract_block()}"
                "- skill_doc: `./SKILL.md`\n"
                "- capability_refs:\n"
                f"  - `{SKILL_RUNTIME_CAPABILITY_REF}`\n"
                f"  - `{GUARD_CAPABILITY_REF}`\n"
                "- knowledge_refs:\n"
                f"  - `{GUARD_KNOWLEDGE_REF}`\n",
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
                "- execution_mode: `subagent_preferred`\n"
                "- guard_policy: `required`\n"
                "- skill_doc: `./SKILL.md`\n"
                "- capability_refs:\n"
                f"  - `{SKILL_RUNTIME_CAPABILITY_REF}`\n"
                f"  - `{GUARD_CAPABILITY_REF}`\n"
                "- knowledge_refs:\n"
                f"  - `{GUARD_KNOWLEDGE_REF}`\n",
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
                "- execution_mode: `local_default`\n"
                "- guard_policy: `closed_world`\n"
                f"{self._os_contract_block()}"
                "- constraints: explicit closed-world execution\n"
                "- skill_doc: `./SKILL.md`\n"
                "- capability_refs:\n"
                f"  - `{SKILL_RUNTIME_CAPABILITY_REF}`\n",
                encoding="utf-8",
            )

            result = validate_skill_meta(meta)

            self.assertFalse(result.ok)
            self.assertIn(
                "review-oriented skills must use subagent_preferred or subagent_required",
                result.errors,
            )


if __name__ == "__main__":
    unittest.main()
