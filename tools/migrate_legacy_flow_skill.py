from __future__ import annotations

import argparse
from pathlib import Path


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_meta_lines(text: str) -> dict[str, object]:
    data: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if line.startswith("- ") and ":" in stripped[2:]:
            key, value = stripped[2:].split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value:
                data[key] = value.strip("`")
            else:
                data[key] = []
            continue
        if current_key and stripped.startswith("- "):
            value = stripped[2:].strip().strip("`")
            current = data.get(current_key)
            if not isinstance(current, list):
                current = []
                data[current_key] = current
            current.append(value)
    return data


def _heading_exists(text: str, heading: str) -> bool:
    return any(line.strip().lower() == f"## {heading}".lower() for line in text.splitlines())


def _infer_skill_id(source_dir: Path, parsed_meta: dict[str, object]) -> str:
    value = parsed_meta.get("skill_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return source_dir.name.replace(" ", "_").replace("-", "_").lower()


def _detect_source_inventory(source_dir: Path) -> list[str]:
    items: list[str] = []
    for path in sorted(source_dir.rglob("*")):
        if path.is_file():
            items.append(str(path.relative_to(source_dir)))
    return items


def _detect_migration_gaps(skill_text: str, parsed_meta: dict[str, object], inventory: list[str]) -> list[str]:
    gaps: list[str] = []
    if "meta.md" not in inventory:
        gaps.append("missing_runtime_fields")
    else:
        if "maturity" not in parsed_meta and "status" not in parsed_meta:
            gaps.append("missing_runtime_fields")
        if "execution_mode" not in parsed_meta:
            gaps.append("missing_runtime_fields")
        if "guard_policy" not in parsed_meta:
            gaps.append("missing_runtime_fields")
    if not _heading_exists(skill_text, "Purpose"):
        gaps.append("missing_goal")
    if "Required Knowledge" not in skill_text and "knowledge/" not in skill_text:
        gaps.append("missing_domain_sources")
    if "flows" not in "\n".join(inventory).lower() and not any(name.endswith(".yaml") for name in inventory):
        gaps.append("missing_workflow_control")
    if "knowledge/" not in skill_text and "Required Knowledge" not in skill_text:
        gaps.append("mixed_procedure_and_facts")
    return sorted(set(gaps))


def _build_mapping_table(inventory: list[str]) -> list[str]:
    rows: list[str] = []
    for item in inventory:
        lower = item.lower()
        if lower.endswith("skill.md"):
            rows.append(f"- `{item}` -> `skills/<skill_id>/SKILL.md`")
        elif lower.endswith("meta.md"):
            rows.append(f"- `{item}` -> `skills/<skill_id>/meta.md` (scaffold reference only)")
        elif lower.endswith(".yaml") or lower.endswith(".yml"):
            rows.append(f"- `{item}` -> `flows/` candidate")
        elif lower.endswith(".md"):
            rows.append(f"- `{item}` -> `docs/` or `knowledge/` candidate")
        else:
            rows.append(f"- `{item}` -> `sources/` or manual review")
    return rows


def _build_meta_scaffold(skill_id: str, parsed_meta: dict[str, object]) -> str:
    summary = parsed_meta.get("summary") if isinstance(parsed_meta.get("summary"), str) else "migrated legacy Flow / Skill scaffold"
    use_when = parsed_meta.get("use_when") if isinstance(parsed_meta.get("use_when"), str) else "legacy Flow / Skill must be migrated into current XRefKit structure"
    input_text = parsed_meta.get("input") if isinstance(parsed_meta.get("input"), str) else "legacy Flow / Skill source artifact"
    output_text = parsed_meta.get("output") if isinstance(parsed_meta.get("output"), str) else "trial-first migrated scaffold and migration report"
    return "\n".join(
        [
            f"# Skill Meta: {skill_id}",
            "",
            f"- skill_id: `{skill_id}`",
            f"- summary: {summary}",
            f"- use_when: {use_when}",
            f"- input: {input_text}",
            f"- output: {output_text}",
            "- maturity: `trial`",
            "- execution_mode: `local_default`",
            "- guard_policy: `required`",
            "- skill_doc: `./SKILL.md`",
            "- observation_refs:",
            "  - `../../work/sessions/<migration-session>.md`",
            "",
        ]
    )


def _build_report(
    *,
    source_dir: Path,
    skill_id: str,
    inventory: list[str],
    mapping_table: list[str],
    migration_gaps: list[str],
    meta_scaffold_path: str,
) -> str:
    lines = [
        "# Legacy Flow Skill Migration Report",
        "",
        f"- source_artifact: `{source_dir}`",
        f"- target_skill_id: `{skill_id}`",
        "- migration_status: `scaffold_ready`" if meta_scaffold_path else "- migration_status: `inventory_only`",
        "",
        "## Source Inventory",
        "",
    ]
    lines.extend(f"- `{item}`" for item in inventory)
    lines.extend(["", "## Mapping Table", ""])
    lines.extend(mapping_table)
    lines.extend(["", "## Meta Scaffold", ""])
    lines.append(f"- meta_scaffold_path: `{meta_scaffold_path}`" if meta_scaffold_path else "- meta_scaffold_path:")
    lines.extend(["", "## Migration Gaps", ""])
    lines.extend(f"- `{gap}`" for gap in migration_gaps)
    lines.extend(["", "## Next Step", ""])
    next_step = "split facts from procedure and review unresolved migration gaps"
    lines.append(f"- next_migration_step: {next_step}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a trial-first migration scaffold for a legacy Flow / Skill.")
    parser.add_argument("--source-dir", required=True, help="Path to the legacy Flow / Skill folder.")
    parser.add_argument("--out-dir", default=None, help="Optional output directory for migration report and meta scaffold.")
    parser.add_argument("--target-skill-id", default=None, help="Optional explicit target skill id.")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"fail: source_dir_not_found {source_dir}")
        return 1

    skill_path = source_dir / "SKILL.md"
    if not skill_path.exists():
        print(f"fail: missing_SKILL_md {skill_path}")
        return 1

    meta_path = source_dir / "meta.md"
    parsed_meta: dict[str, object] = {}
    if meta_path.exists():
        parsed_meta = _parse_meta_lines(_read_text(meta_path))

    skill_text = _read_text(skill_path)
    inventory = _detect_source_inventory(source_dir)
    skill_id = args.target_skill_id or _infer_skill_id(source_dir, parsed_meta)
    mapping_table = _build_mapping_table(inventory)
    migration_gaps = _detect_migration_gaps(skill_text, parsed_meta, inventory)
    meta_scaffold = _build_meta_scaffold(skill_id, parsed_meta)

    meta_scaffold_path = ""
    report_path = ""
    if args.out_dir:
        out_dir = Path(args.out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        meta_out = out_dir / "meta.scaffold.md"
        report_out = out_dir / "migration_report.md"
        meta_out.write_text(meta_scaffold, encoding="utf-8")
        report_out.write_text(
            _build_report(
                source_dir=source_dir,
                skill_id=skill_id,
                inventory=inventory,
                mapping_table=mapping_table,
                migration_gaps=migration_gaps,
                meta_scaffold_path=str(meta_out),
            ),
            encoding="utf-8",
        )
        meta_scaffold_path = str(meta_out)
        report_path = str(report_out)

    print(f"ok: source_dir={source_dir}")
    print(f"  target_skill_id: {skill_id}")
    print(f"  inventory_count: {len(inventory)}")
    print(f"  migration_gaps: {', '.join(migration_gaps) if migration_gaps else 'none'}")
    if report_path:
        print(f"  migration_report: {report_path}")
    if meta_scaffold_path:
        print(f"  meta_scaffold: {meta_scaffold_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
