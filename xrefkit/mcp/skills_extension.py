"""SEP-2640 bootstrap Skills; native procedure access retains its existing gates.

The published file space is generated and finite. Resource URIs are dictionary
keys, never filesystem paths. Native sources are used only for fingerprints.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

import yaml

from .catalog import XRefCatalog
from .schemas import SkillCatalogEntry

EXTENSION_ID = "io.modelcontextprotocol/skills"


@dataclass(frozen=True)
class PublishedSkill:
    uri: str
    frontmatter: dict[str, Any]
    text: str

    def entry(self) -> dict[str, Any]:
        raw = self.text.encode("utf-8")
        return {
            "uri": self.uri,
            "frontmatter": self.frontmatter,
            "resources": [{
                "uri": self.uri,
                "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "size": len(raw),
            }],
        }


def _public(entry: SkillCatalogEntry) -> bool:
    zone = entry.zone_metadata
    path_parts = PurePosixPath(entry.path.replace("\\", "/")).parts
    return not (
        "skills_private" in path_parts
        or zone.get("hidden")
        or zone.get("local_only")
        or zone.get("catalog") is False
        or zone.get("distribution") is False
        or zone.get("boundary") == "private"
        or zone.get("identity_conflict")
        or entry.maturity in {"draft", "deprecated"}
    )


def _source_hash(entry: SkillCatalogEntry, repo_root: Path) -> str:
    if entry.definition_format == "skill_definition_v1":
        root = Path(entry.source_root) if entry.source_root else repo_root
        relative = Path(entry.path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe catalog source")
        path = root
        for part in relative.parts:
            path = path / part
            if path.is_symlink():
                raise ValueError("symlink catalog source")
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("catalog source escapes its root")
        content = path.read_bytes()
    else:
        # Legacy get_skill serves these catalog-cached bodies, not live files.
        content = json.dumps(
            [entry.meta_content, entry.skill_content], ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _project(entry: SkillCatalogEntry, source_hash: str) -> PublishedSkill:
    suffix = hashlib.sha256(entry.skill_id.encode("utf-8")).hexdigest()[:16]
    prefix = re.sub(r"[^a-z0-9]+", "-", entry.skill_id.lower()).strip("-")
    name = (prefix[:45].rstrip("-") or "skill") + "-" + suffix
    uri = f"skill://xrefkit/{name}/SKILL.md"
    frontmatter = {
        "name": name,
        "description": (entry.summary.strip() or f"Enter the {entry.skill_id} XRefKit workflow")[:1024],
        "metadata": {
            "xrefkit-skill-id": entry.skill_id,
            "xrefkit-adapter": "governed-bootstrap-v1",
            "xrefkit-source-format": entry.definition_format,
            "xrefkit-source-sha256": source_hash,
            "xrefkit-maturity": entry.maturity,
            "xrefkit-package-id": entry.package_id or "repository",
        },
    }
    skill_id = json.dumps(entry.skill_id, ensure_ascii=False)
    text = "---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n"
    text += (
        "# Enter the XRefKit governed workflow\n\n"
        "This is a bootstrap adapter, not the native Skill procedure. Its only "
        "published file is this SKILL.md; native supporting files are not part "
        "of this adapter's resource manifest.\n\n"
        f"Canonical Skill ID: {skill_id}.\n\n"
        "1. Use get_startup_context on this same originating MCP server and apply "
        "its startup contract before loading the canonical procedure.\n"
        f"2. Use get_skill_requirements with skill_id={skill_id} to obtain the "
        "runtime requirements. Preserve readiness and human decision boundaries.\n"
        "3. Follow the returned runtime envelope to create a Skill Run with "
        "instruction-derived runtime fields. Host-side execution requires the "
        "user's explicit approval for this remote Skill; this resource grants "
        "no tool or filesystem permissions.\n"
        f"4. Bind the returned run identity using bind_skill_run with skill_id={skill_id}, "
        "and follow its recording instructions. Never replace a different active "
        "run binding to make this adapter execute.\n"
        f"5. Load get_skill with skill_id={skill_id} from the same originating "
        "server. Resolve needed XIDs through get_document_by_xid and execute only "
        "within the established task, runtime and host authorization.\n\n"
        "Reading this resource is inspection only: it does not activate a native "
        "Skill, create a run, unlock tools, approve code execution or confer higher "
        "authority. Keep the originating server identity visible. Canonical "
        "procedure and knowledge responses remain separately governed MCP tool "
        "content; this adapter's digest does not independently verify those "
        "responses or establish trust in the server.\n"
    )
    return PublishedSkill(uri, frontmatter, text)


class SkillsExtension:
    def __init__(self, catalog: XRefCatalog):
        self.catalog = catalog

    def snapshot(self) -> dict[str, PublishedSkill]:
        entries = list(self.catalog.skills)
        # A canonical ID colliding with another entry's alias is ambiguous too.
        identities = Counter(
            identity
            for entry in entries
            for identity in set([entry.skill_id, *entry.legacy_skill_ids])
        )
        published: dict[str, PublishedSkill] = {}
        conflicts: set[str] = set()
        for entry in entries:
            if not _public(entry) or identities[entry.skill_id] != 1:
                continue
            try:
                source_hash = _source_hash(entry, self.catalog.repo_root)
            except (OSError, ValueError):
                # Unavailable or unsafe sources cannot have a valid manifest.
                continue
            skill = _project(entry, source_hash)
            if skill.uri in published:
                conflicts.add(skill.uri)
            published[skill.uri] = skill
        return {uri: published[uri] for uri in sorted(published) if uri not in conflicts}

    def list_skills(self, cursor: str | None = None) -> dict[str, Any]:
        if cursor is not None:
            raise ValueError("This complete Skill listing has no continuation cursor")
        return {"resultType": "complete", "skills": [s.entry() for s in self.snapshot().values()]}

    def get_skill(self, uri: str) -> dict[str, Any]:
        return {"resultType": "complete", "skill": self._get(uri).entry()}

    def read_resource(self, uri: str) -> dict[str, Any]:
        skill = self._get(uri)
        return {"contents": [{"uri": skill.uri, "mimeType": "text/markdown", "text": skill.text}]}

    def list_resources(self) -> dict[str, Any]:
        return {"resources": [{"uri": s.uri, "name": s.frontmatter["name"], "mimeType": "text/markdown"}
                              for s in self.snapshot().values()]}

    def _get(self, uri: str) -> PublishedSkill:
        skill = self.snapshot().get(uri)
        if skill is None:
            raise ValueError("No bootstrap Skill resource is served at the requested URI")
        return skill
