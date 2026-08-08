from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_brownfield_file_editing_protocol_is_in_canonical_and_packaged_skill() -> None:
    canonical = (ROOT / "skills" / "brownfield-workflow" / "SKILL.md").read_text(encoding="utf-8")
    packaged = (
        ROOT / "packages" / "xrefkit-skills-brownfield" / "src" / "xrefkit_skills_brownfield"
        / "skills" / "brownfield_workflow" / "entry.md"
    ).read_text(encoding="utf-8")

    for keyword in (
        "encoding",
        "BOM",
        "newline",
        "Unicode",
        "strict",
        "after_bytes",
        "mojibake",
        "concurrency",
        "revision token",
        "compare-and-swap",
        "abort",
        "atomically",
        "specification",
        "semantic",
        "authoritative",
        "hypothesis",
        "semantic_alignment",
        "Historical conflict investigation",
        "bounded",
        "Git",
        "uncommitted",
        "newest",
        "Uncommitted-file policy",
        "pre_existing_human_or_unknown",
        "ai_owned_current_work",
        "mixed_or_overlapping",
        "untracked",
        "stash",
        "New-file extension conformity",
        "peer",
        "companion files",
        "extension-specific",
        "cluster",
        "majority",
        "same directory",
        "confidence",
        "weak margin",
        "repository-wide fallback",
    ):
        assert keyword in canonical
        assert keyword in packaged
