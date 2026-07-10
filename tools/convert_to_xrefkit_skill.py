#!/usr/bin/env python3
# xid: D8B4A2F7C931

"""Convert an external file-based Skill into XRefKit Skill + Knowledge files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from xrefkit.xref import _extract_xid, _gen_xid, _replace_or_insert_xid_block


MARKDOWN_LINK_RE = re.compile(r"(?P<prefix>!?)\[(?P<label>[^\]]*)\]\((?P<url>[^)\s]+)(?P<rest>[^)]*)\)")
KNOWLEDGE_SUFFIXES = {".md", ".mdx", ".txt"}


@dataclass(frozen=True)
class ImportedKnowledge:
    source_path: str
    target_path: str
    xid: str
    title: str


@dataclass(frozen=True)
class ConversionResult:
    ok: bool
    skill_id: str
    skill_dir: str
    skill_doc: str
    meta_doc: str
    imported_knowledge: list[ImportedKnowledge]
    changed_files: list[str]
    warnings: list[str]
    dry_run: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "skill_id": self.skill_id,
            "skill_dir": self.skill_dir,
            "skill_doc": self.skill_doc,
            "meta_doc": self.meta_doc,
            "imported_knowledge": [item.__dict__ for item in self.imported_knowledge],
            "changed_files": self.changed_files,
            "warnings": self.warnings,
            "dry_run": self.dry_run,
        }


@dataclass(frozen=True)
class BatchConversionResult:
    ok: bool
    source_root: str
    converted_skills: list[ConversionResult]
    changed_files: list[str]
    warnings: list[str]
    dry_run: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "source_root": self.source_root,
            "converted_skills": [item.to_dict() for item in self.converted_skills],
            "changed_files": self.changed_files,
            "warnings": self.warnings,
            "dry_run": self.dry_run,
        }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str, *, dry_run: bool) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    return True


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-")
    return slug.lower() or "imported_skill"


def _title_from_text(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def _ensure_markdown_xid(text: str, known_xids: set[str]) -> tuple[str, str]:
    xid = _extract_xid(text)
    if xid and re.fullmatch(r"[A-F0-9]{12}", xid):
        known_xids.add(xid)
        return text, xid
    xid = _gen_xid()
    while xid in known_xids:
        xid = _gen_xid()
    known_xids.add(xid)
    return _replace_or_insert_xid_block(text, xid), xid


def _repo_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _relative_markdown_url(from_path: Path, to_path: Path) -> str:
    return Path(__import__("os").path.relpath(to_path, start=from_path.parent)).as_posix()


def _find_skill_doc(source_dir: Path, explicit: str | None) -> Path:
    if explicit:
        path = source_dir / explicit
        if not path.is_file():
            raise FileNotFoundError(f"skill doc not found: {path}")
        return path
    for name in ("SKILL.md", "skill.md", "README.md", "readme.md"):
        path = source_dir / name
        if path.is_file():
            return path
    raise FileNotFoundError("could not find SKILL.md or README.md in source skill directory")


def _resolve_source_link(source_doc: Path, url: str, source_root: Path) -> Path | None:
    if "://" in url or url.startswith("#"):
        return None
    path_part = url.split("#", 1)[0]
    if not path_part:
        return None
    candidate = (source_doc.parent / path_part).resolve()
    try:
        candidate.relative_to(source_root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    if candidate.suffix.lower() not in KNOWLEDGE_SUFFIXES:
        return None
    return candidate


def _knowledge_target_path(source_path: Path, source_root: Path, knowledge_dir: Path) -> Path:
    rel = source_path.relative_to(source_root)
    parts = rel.parts
    if len(parts) > 1 and parts[0].lower() == "knowledge":
        rel = Path(*parts[1:])
    suffix = ".md" if source_path.suffix.lower() == ".txt" else source_path.suffix
    return knowledge_dir / rel.with_suffix(suffix)


def _knowledge_text(source_path: Path, source_root: Path, skill_id: str, known_xids: set[str]) -> tuple[str, str, str]:
    text = _read_text(source_path)
    title = _title_from_text(text, source_path.stem.replace("_", " ").replace("-", " ").title())
    if source_path.suffix.lower() == ".txt":
        rel = source_path.relative_to(source_root).as_posix()
        text = f"# {title}\n\n{text.rstrip()}\n\n## Source\n\n- imported_from: `{rel}`\n"
    elif "## Source" not in text:
        rel = source_path.relative_to(source_root).as_posix()
        text = text.rstrip() + f"\n\n## Source\n\n- imported_from: `{rel}`\n"
    text, xid = _ensure_markdown_xid(text, known_xids)
    if f"- imported_by_skill: `{skill_id}`" not in text:
        text = text.rstrip() + f"\n- imported_by_skill: `{skill_id}`\n"
    return text, xid, title


def _existing_knowledge_text(target_path: Path, known_xids: set[str]) -> tuple[str, str, str] | None:
    if not target_path.exists():
        return None
    text = _read_text(target_path)
    xid = _extract_xid(text)
    if not xid or not re.fullmatch(r"[A-F0-9]{12}", xid):
        return None
    known_xids.add(xid)
    title = _title_from_text(text, target_path.stem.replace("_", " ").replace("-", " ").title())
    return text, xid, title


def _meta_text(*, skill_id: str, skill_doc_xid: str, knowledge: list[ImportedKnowledge], known_xids: set[str]) -> tuple[str, str]:
    lines = [
        f"# Skill Meta: {skill_id}",
        "",
        f"- skill_id: `{skill_id}`",
        "- maturity: `draft`",
        "- skill_doc: `./SKILL.md`",
        "- summary: imported external Skill normalized into XRefKit split form",
        "- use_when: imported Skill behavior is selected by explicit human routing or later catalog registration",
        "- input: external Skill inputs as described in SKILL.md",
        "- output: external Skill outputs as described in SKILL.md",
        "- capability_layering: `required`",
        "- workflow_protocol: `required`",
        "- capability: imported_skill_execution",
        "- tuning: external_skill",
        "- responsibility: execute imported external Skill behavior after XRefKit review",
    ]
    if knowledge:
        lines.append("- knowledge_slots:")
        for item in knowledge:
            safe_name = _slug(item.title).replace(".", "_").replace("-", "_")
            lines.append(f"  - name={safe_name}; bind={item.xid}")
    lines.extend(
        [
            "- observation_refs:",
            "  - `conversion: external skill import`",
            "",
            "## Conversion Notes",
            "",
            f"- skill_doc_xid: `{skill_doc_xid}`",
            "- source: external Skill converted by `convert_to_xrefkit_skill.py`",
        ]
    )
    text = "\n".join(lines) + "\n"
    return _ensure_markdown_xid(text, known_xids)


def convert_skill(
    *,
    source_dir: Path,
    repo_root: Path,
    skill_id: str,
    target_skill_dir: Path | None = None,
    target_knowledge_dir: Path | None = None,
    source_skill_doc: str | None = None,
    source_root: Path | None = None,
    dry_run: bool = False,
) -> ConversionResult:
    source_dir = source_dir.resolve()
    source_root = (source_root or source_dir).resolve()
    repo_root = repo_root.resolve()
    if not source_dir.is_dir():
        raise FileNotFoundError(f"source skill directory not found: {source_dir}")
    source_dir.relative_to(source_root)

    skill_dir = (target_skill_dir or (repo_root / "skills_private" / _slug(skill_id))).resolve()
    knowledge_dir = (target_knowledge_dir or (repo_root / "knowledge" / "imported_skills" / _slug(skill_id))).resolve()
    source_doc = _find_skill_doc(source_dir, source_skill_doc)

    known_xids: set[str] = set()
    changed_files: list[str] = []
    warnings: list[str] = []
    imported: list[ImportedKnowledge] = []
    source_to_import: dict[Path, ImportedKnowledge] = {}

    skill_text = _read_text(source_doc)
    skill_text, skill_xid = _ensure_markdown_xid(skill_text, known_xids)

    def replace_link(match: re.Match[str]) -> str:
        if match.group("prefix") == "!":
            return match.group(0)
        url = match.group("url")
        target = _resolve_source_link(source_doc, url, source_root)
        if target is None or target.resolve() == source_doc.resolve():
            return match.group(0)
        if target not in source_to_import:
            target_path = _knowledge_target_path(target, source_root, knowledge_dir)
            existing = _existing_knowledge_text(target_path, known_xids)
            if existing is None:
                knowledge_text, xid, title = _knowledge_text(target, source_root, skill_id, known_xids)
            else:
                knowledge_text, xid, title = existing
            if _write_text(target_path, knowledge_text, dry_run=dry_run):
                changed_files.append(_repo_rel(target_path, repo_root))
            source_to_import[target] = ImportedKnowledge(
                source_path=target.relative_to(source_root).as_posix(),
                target_path=_repo_rel(target_path, repo_root),
                xid=xid,
                title=title,
            )
            imported.append(source_to_import[target])
        item = source_to_import[target]
        new_url = _relative_markdown_url(skill_dir / "SKILL.md", repo_root / item.target_path) + f"#xid-{item.xid}"
        return f"[{match.group('label')}]({new_url}{match.group('rest')})"

    normalized_skill_text = MARKDOWN_LINK_RE.sub(replace_link, skill_text)
    if "## XRefKit Imported Knowledge" not in normalized_skill_text:
        normalized_skill_text = normalized_skill_text.rstrip() + "\n\n## XRefKit Imported Knowledge\n\n"
        if imported:
            for item in imported:
                url = _relative_markdown_url(skill_dir / "SKILL.md", repo_root / item.target_path)
                normalized_skill_text += f"- [{item.title}]({url}#xid-{item.xid})\n"
        else:
            normalized_skill_text += "- none\n"

    skill_doc_path = skill_dir / "SKILL.md"
    if _write_text(skill_doc_path, normalized_skill_text, dry_run=dry_run):
        changed_files.append(_repo_rel(skill_doc_path, repo_root))

    meta, _meta_xid = _meta_text(skill_id=skill_id, skill_doc_xid=skill_xid, knowledge=imported, known_xids=known_xids)
    meta_path = skill_dir / "meta.md"
    if _write_text(meta_path, meta, dry_run=dry_run):
        changed_files.append(_repo_rel(meta_path, repo_root))

    return ConversionResult(
        ok=True,
        skill_id=skill_id,
        skill_dir=_repo_rel(skill_dir, repo_root),
        skill_doc=_repo_rel(skill_doc_path, repo_root),
        meta_doc=_repo_rel(meta_path, repo_root),
        imported_knowledge=imported,
        changed_files=sorted(dict.fromkeys(changed_files)),
        warnings=warnings,
        dry_run=dry_run,
    )


def _discover_skill_dirs(source_root: Path) -> list[Path]:
    skills_root = source_root / "skills"
    if not skills_root.is_dir():
        raise FileNotFoundError(f"batch source root must contain skills/: {source_root}")
    skill_dirs: list[Path] = []
    for path in sorted(skills_root.iterdir()):
        if not path.is_dir():
            continue
        if any((path / name).is_file() for name in ("SKILL.md", "skill.md", "README.md", "readme.md")):
            skill_dirs.append(path)
    return skill_dirs


def convert_skill_tree(
    *,
    source_root: Path,
    repo_root: Path,
    skill_id_prefix: str | None = None,
    target_skill_root: Path | None = None,
    target_knowledge_dir: Path | None = None,
    dry_run: bool = False,
) -> BatchConversionResult:
    source_root = source_root.resolve()
    repo_root = repo_root.resolve()
    batch_id = _slug(skill_id_prefix or source_root.name)
    target_skill_root = (target_skill_root or (repo_root / "skills_private")).resolve()
    target_knowledge_dir = (target_knowledge_dir or (repo_root / "knowledge" / "imported_skills" / batch_id)).resolve()
    results: list[ConversionResult] = []
    warnings: list[str] = []

    for skill_dir in _discover_skill_dirs(source_root):
        local_name = _slug(skill_dir.name)
        skill_id = f"{batch_id}.{local_name}" if skill_id_prefix else local_name
        result = convert_skill(
            source_dir=skill_dir,
            source_root=source_root,
            repo_root=repo_root,
            skill_id=skill_id,
            target_skill_dir=target_skill_root / skill_id,
            target_knowledge_dir=target_knowledge_dir,
            dry_run=dry_run,
        )
        results.append(result)
        warnings.extend(result.warnings)

    changed_files = sorted(dict.fromkeys(path for result in results for path in result.changed_files))
    return BatchConversionResult(
        ok=all(result.ok for result in results),
        source_root=source_root.as_posix(),
        converted_skills=results,
        changed_files=changed_files,
        warnings=warnings,
        dry_run=dry_run,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert an external Skill directory into XRefKit Skill + Knowledge files.")
    parser.add_argument("source_dir", help="External Skill directory")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="XRefKit repository root")
    parser.add_argument("--skill-id", help="Target XRefKit skill id")
    parser.add_argument("--batch", action="store_true", help="Treat source_dir as a root containing skills/ and knowledge/")
    parser.add_argument("--skill-id-prefix", default=None, help="Prefix for generated skill ids in --batch mode")
    parser.add_argument("--source-skill-doc", default=None, help="Source skill document path relative to source_dir")
    parser.add_argument("--target-skill-dir", default=None, help="Target Skill directory; defaults to skills_private/<skill-id>")
    parser.add_argument("--target-skill-root", default=None, help="Batch target Skill root; defaults to skills_private/")
    parser.add_argument("--target-knowledge-dir", default=None, help="Target Knowledge directory; defaults to knowledge/imported_skills/<skill-id>")
    parser.add_argument("--dry-run", action="store_true", help="Show planned output without writing files")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(args.repo_root)
    if args.batch:
        result = convert_skill_tree(
            source_root=Path(args.source_dir),
            repo_root=repo_root,
            skill_id_prefix=args.skill_id_prefix,
            target_skill_root=Path(args.target_skill_root) if args.target_skill_root else None,
            target_knowledge_dir=Path(args.target_knowledge_dir) if args.target_knowledge_dir else None,
            dry_run=bool(args.dry_run),
        )
    else:
        if not args.skill_id:
            raise SystemExit("--skill-id is required unless --batch is used")
        result = convert_skill(
            source_dir=Path(args.source_dir),
            repo_root=repo_root,
            skill_id=args.skill_id,
            target_skill_dir=Path(args.target_skill_dir) if args.target_skill_dir else None,
            target_knowledge_dir=Path(args.target_knowledge_dir) if args.target_knowledge_dir else None,
            source_skill_doc=args.source_skill_doc,
            dry_run=bool(args.dry_run),
        )
    payload = result.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"ok: {payload['ok']}")
        if isinstance(result, BatchConversionResult):
            for item in result.converted_skills:
                print(f"skill: {item.skill_doc}")
            for path in result.changed_files:
                if path.startswith("knowledge/"):
                    print(f"knowledge: {path}")
        else:
            print(f"skill: {result.skill_doc}")
            print(f"meta: {result.meta_doc}")
            for item in result.imported_knowledge:
                print(f"knowledge: {item.target_path}#xid-{item.xid}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
