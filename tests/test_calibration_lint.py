from __future__ import annotations

from pathlib import Path

from xrefkit.skillmeta import validate_skill_meta


def test_generic_calibration_wording_is_candidate_only_warning(tmp_path: Path) -> None:
    skill = tmp_path / "skills/sample"
    skill.mkdir(parents=True)
    (skill / "meta.md").write_text(
        """# Skill Meta: sample

- skill_id: `sample`
- summary: sample
- use_when: sample task
- input: input
- output: output
- skill_doc: `SKILL.md`
- maturity: `draft`
""",
        encoding="utf-8",
    )
    (skill / "SKILL.md").write_text(
        "# Sample\n\n- Downgrade unsupported conclusions to unknown.\n",
        encoding="utf-8",
    )

    result = validate_skill_meta(skill / "meta.md", check_level="draft")

    assert result.ok is True
    assert any("generic calibration wording candidate" in item for item in result.warnings)


def test_skill_template_does_not_embed_generic_calibration_placeholder() -> None:
    root = Path(__file__).resolve().parents[1]
    template = (
        root / "skills/os/skill_flow_authoring/references/skill_body_template.md"
    ).read_text(encoding="utf-8")

    assert "downgrade unsupported inference" not in template
