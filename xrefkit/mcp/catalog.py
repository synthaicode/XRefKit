from __future__ import annotations

import base64
import io
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .contracts import builtin_tool_contracts
from .ownership import Ownership, load_ownership, validate_ownership
from .repository import (
    first_heading,
    first_paragraph,
    first_xid,
    file_last_modified,
    markdown_xid_link_targets,
    markdown_xid_only_text,
    markdown_xid_links,
    parse_meta_bullets,
    read_text,
    relative_to_repo,
    repository_identity,
    scalar_list,
    stable_hash,
)
from .schemas import (
    ClientObligation,
    ClientToolDistribution,
    ClientToolFile,
    ClientToolManifestEntry,
    ClientToolPipPackage,
    ClosureContract,
    KnowledgeCatalogEntry,
    SkillCatalogEntry,
    SkillRankResult,
    RuntimeRoleContract,
    StartupContext,
    StartupReference,
    ToolContract,
    XRefDocument,
)
from .startup_contract_pack import (
    EMBEDDED_BASED_ON_HASHES,
    EMBEDDED_STARTUP_SOURCE_PATHS,
    STARTUP_CONTRACT_PACK_XID,
    normalize_pack_body,
    normalized_startup_contract_pack_body,
    parse_based_on_hashes,
    parse_pack_version,
)


TOKEN_RE = re.compile(r"[A-Za-z0-9_+#.-]+")
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z0-9_.]+)", re.MULTILINE)
CLIENT_TOOL_PACKAGE_ID = "xrefkit-client-python-tools"
CLIENT_TOOL_PACKAGE_VERSION = "0.1.0"
XREFKIT_RUNTIME_PACKAGE_ID = "xrefkit"
XREFKIT_RUNTIME_VERSION_RE = re.compile(r"__version__\s*=\s*[\"']([^\"']+)[\"']")
CACHE_MAX_VERSION_PAYLOAD_RATIO = 0.5
XID_DOCUMENT_SUFFIXES = {".md", ".yaml", ".yml"}
STARTUP_REFERENCE_DEFINITIONS = [
    (
        "0B5C58B5E5B2",
        "base_control",
    ),
    (
        "5A1C8E4D2F90",
        "base_control",
    ),
    (
        "6C0B62D6366A",
        "xref_routing",
    ),
    (
        "8A666C1FD121",
        "base_control",
    ),
    (
        "A7F3C92D4E11",
        "base_control",
    ),
    (
        "4A423E72D2ED",
        "base_control",
    ),
]
STOP_TOKENS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "by",
    "code",
    "for",
    "in",
    "is",
    "of",
    "or",
    "review",
    "skill",
    "the",
    "to",
    "user",
    "with",
}

ROUTING_SYNONYMS = {
    "試験計画": ("test", "planning", "plan", "test_flow"),
    "テスト計画": ("test", "planning", "plan", "test_flow"),
    "試験設計": ("test", "design", "test_flow"),
    "テスト設計": ("test", "design", "test_flow"),
    "試験項目": ("test", "item", "case"),
    "テスト項目": ("test", "item", "case"),
    "試験データ": ("test", "data"),
    "テストデータ": ("test", "data"),
    "試験環境": ("test", "environment"),
    "テスト環境": ("test", "environment"),
    "試験ツール": ("test", "tool"),
    "テストツール": ("test", "tool"),
    "テスト用ツール": ("test", "tool", "local", "domain"),
    "試験用ツール": ("test", "tool", "local", "domain"),
    "テスト用スクリプト": ("test", "script", "helper", "automation", "test_flow"),
    "試験用スクリプト": ("test", "script", "helper", "automation", "test_flow"),
    "スクリプト": ("script", "helper", "automation"),
    "カタログ化": ("catalog", "cataloging", "test_tool_catalog_preparation"),
    "カタログ": ("catalog", "test_tool_catalog_preparation"),
    "用意": ("preparation", "setup"),
    "準備": ("preparation", "setup", "implementation"),
    "実施前": ("pre", "execution", "preparation"),
    "実行前": ("pre", "execution", "preparation"),
    "実行": ("execution", "run"),
    "簡易": ("simplify", "helper", "script"),
    "簡易化": ("simplify", "helper", "script"),
    "証跡": ("evidence", "capture"),
    "根拠": ("basis", "evidence"),
    "トレーサビリティ": ("traceability", "xddp"),
}

ROUTING_CATEGORY_TERMS = {
    "activity": {
        "analysis",
        "catalog",
        "cataloging",
        "design",
        "implementation",
        "execution",
        "planning",
        "preparation",
        "review",
        "run",
        "simplify",
    },
    "artifact": {
        "case",
        "catalog",
        "data",
        "environment",
        "helper",
        "item",
        "plan",
        "script",
        "test",
        "tool",
    },
    "domain": {
        "c#",
        "csharp",
        "database",
        "db",
        "dotnet",
        "release",
        "security",
        "test",
    },
    "phase": {
        "before",
        "execution",
        "implementation",
        "pre",
        "preparation",
        "release",
        "setup",
    },
    "evidence_trace": {
        "basis",
        "evidence",
        "trace",
        "traceability",
        "xddp",
    },
    "tool_runtime": {
        "automation",
        "ci",
        "xrefkit",
        "helper",
        "mcp",
        "script",
        "tool",
    },
}

ROUTING_CATEGORY_WEIGHTS = {
    "activity": 0.5,
    "artifact": 0.7,
    "domain": 0.3,
    "phase": 0.3,
    "evidence_trace": 0.25,
    "tool_runtime": 0.25,
}


@dataclass(frozen=True)
class XRefCatalog:
    repo_root: Path
    repository_fingerprint: str
    fingerprint_basis: str
    tools: list[ToolContract]
    ownership: Ownership | None = None
    domain_knowledge_roots: tuple[Path, ...] = ()

    @classmethod
    def build(
        cls,
        repo_root: str | Path,
        domain_knowledge_roots: list[str | Path] | tuple[str | Path, ...] | None = None,
    ) -> "XRefCatalog":
        root = Path(repo_root).resolve()
        if not root.exists():
            raise FileNotFoundError(root)
        external_roots = tuple(
            _resolve_domain_knowledge_root(path) for path in (domain_knowledge_roots or [])
        )
        fingerprint, fingerprint_basis = repository_identity(root)
        ownership = load_ownership(root)
        if ownership is not None:
            errors = validate_ownership(root, ownership)
            if errors:
                raise ValueError("invalid ownership.yaml: " + "; ".join(errors))
        return cls(
            repo_root=root,
            repository_fingerprint=fingerprint,
            fingerprint_basis=fingerprint_basis,
            tools=builtin_tool_contracts(),
            ownership=ownership,
            domain_knowledge_roots=external_roots,
        )

    # knowledge, skills, and catalog_version are rebuilt from the live
    # repository on every access so every content-bearing response shares one
    # freshness model with get_document_by_xid (live reads). A frozen
    # build-time snapshot previously let expand_knowledge return a stale
    # content_hash next to a live body on a long-running server, silently
    # breaking the client cache protocol, and hid knowledge/Skill files added
    # or removed after startup.
    @property
    def knowledge(self) -> list[KnowledgeCatalogEntry]:
        return [entry for entry, _text in self._scan_knowledge()]

    @property
    def skills(self) -> list[SkillCatalogEntry]:
        return _build_skills(self.repo_root, self.ownership)

    @property
    def catalog_version(self) -> str:
        version_basis = "\n".join(
            [entry.content_hash for entry in self.knowledge]
            + [entry.skill_id + entry.summary for entry in self.skills]
            + [tool.tool_id + tool.version for tool in self.tools]
            + ([self.ownership.content_hash] if self.ownership else [])
        )
        return stable_hash(version_basis)[:16]

    def _scan_knowledge(self) -> list[tuple[KnowledgeCatalogEntry, str]]:
        """One consistent read per file: entry hash and body come from the
        same text, so they can never disagree."""
        entries: list[tuple[KnowledgeCatalogEntry, str]] = []
        for path in _content_files(self.repo_root, self.ownership, "knowledge", "*.md"):
            text = read_text(path)
            entries.append((_knowledge_entry(self.repo_root, self.ownership, path, text), text))
        for root in self.domain_knowledge_roots:
            for path in _external_knowledge_files(root):
                text = read_text(path)
                if not first_xid(text):
                    continue
                entries.append((_external_knowledge_entry(root, path, text), text))
        return entries

    def get_repository_identity(self) -> dict[str, str]:
        return {
            "repository_fingerprint": self.repository_fingerprint,
            "fingerprint_algorithm": "sha256",
            "fingerprint_basis": self.fingerprint_basis,
            "fingerprint_scope": (
                "shared_across_clones"
                if self.fingerprint_basis == "git_root_commits"
                else "local_path_only"
            ),
            "cache_namespace": self.repository_fingerprint,
        }

    def list_knowledge_catalog(self, limit: int | None = None) -> list[dict]:
        return [entry.to_dict() for entry in self.knowledge[: limit or None]]

    def search_knowledge_catalog(self, query: str, limit: int = 10) -> list[dict]:
        return [entry.to_dict() for entry in _rank_entries(query, self.knowledge)[:limit]]

    def expand_knowledge(self, xid: str) -> dict:
        entry, content = self._knowledge_by_xid(xid)
        return {"entry": entry.to_dict(), "content": content}

    def build_knowledge_context(self, query: str, limit: int = 5) -> dict:
        scanned = self._scan_knowledge()
        ranked = _rank_entries(query, [entry for entry, _text in scanned])[:limit]
        by_xid = {entry.xid: (entry, text) for entry, text in scanned}
        expanded: list[dict] = []
        missing: list[dict] = []
        seen: set[str] = set()
        for entry in ranked:
            for candidate_xid in [entry.xid, *entry.requires_knowledge]:
                if candidate_xid in seen:
                    continue
                seen.add(candidate_xid)
                candidate = by_xid.get(candidate_xid)
                if not candidate:
                    missing.append(
                        {
                            "xid": candidate_xid,
                            "reason": "referenced knowledge was not found in the catalog",
                        }
                    )
                    continue
                candidate_entry, candidate_text = candidate
                expanded.append(
                    {"entry": candidate_entry.to_dict(), "content": candidate_text}
                )
        return {"entries": expanded, "missing": missing}

    def list_skills(
        self,
        limit: int | None = None,
        include_content: bool = False,
    ) -> list[dict]:
        # Metadata-only by default: full procedure bodies are lazy-loaded
        # governance content (get_skill), not routing metadata. The old
        # include_content=True default let one ungated call return every
        # SKILL.md body, bypassing both the startup ordering and the
        # body_mode=lazy context policy.
        entries = self.skills[: limit or None]
        # Keep the routing surface small. The selected Skill response from
        # get_skill/get_skill_requirements carries required_tools when the
        # client is ready to execute it.
        results = [entry.to_dict(include_tools=False) for entry in entries]
        duplicate_ids = _duplicate_skill_ids(self.skills)
        for result in results:
            if result["skill_id"] in duplicate_ids:
                result.setdefault("zone_metadata", {})["identity_conflict"] = True
                result["zone_metadata"]["conflict_key"] = result["skill_id"]
                result["zone_metadata"]["conflict_paths"] = duplicate_ids[result["skill_id"]]
        if not include_content:
            for entry, result in zip(entries, results, strict=True):
                result["meta_content"] = None
                result["skill_content"] = None
                result["document_versions"] = _skill_document_versions(
                    entry,
                    self.repo_root,
                    self.repository_fingerprint,
                )
        return results

    def get_skill(
        self,
        skill_id: str,
        known_document_versions: dict[str, str] | None = None,
    ) -> dict:
        entry = self._skill_by_id(skill_id)
        result = entry.to_dict()
        result["client_tool_download"] = _client_tool_download_policy(entry)
        result["content_resolution"] = _mcp_content_resolution_policy()
        if known_document_versions is None:
            return result

        documents: list[dict] = []
        for relative_path in [entry.meta_path, entry.path]:
            path = self.repo_root / relative_path
            text = read_text(path)
            document = _xref_document(path, self.repo_root, text)
            documents.append(
                _conditional_document_response(
                    document,
                    known_document_versions.get(document.xid),
                    self.repository_fingerprint,
                )
            )
        result["meta_content"] = None
        result["skill_content"] = None
        result["documents"] = documents
        return result

    def get_skill_requirements(self, skill_id: str) -> dict:
        entry = self._skill_by_id(skill_id)
        return {
            "skill_id": entry.skill_id,
            "required_knowledge": entry.required_knowledge,
            "required_tools": entry.required_tools,
            "client_tool_download": _client_tool_download_policy(entry),
            "content_resolution": _mcp_content_resolution_policy(),
            "closure_contract": entry.closure_contract.to_dict(),
            "meta_path": entry.meta_path,
            "meta_links": entry.meta_links,
            "skill_doc": entry.path,
            "skill_links": entry.skill_links,
            "missing": entry.missing,
        }

    def resolve_skill_knowledge(self, skill_id: str) -> dict:
        """Resolve a Skill's declared ``knowledge_slots`` against the base+local
        unified catalog (design 082 Decision 3 / 084 M5).

        Each slot declares a need — a ``query`` or a pinned ``bind`` XID — plus
        acceptance metadata (``min``, ``domain``, ``required``). Selection is
        dynamic (ranked over the merged base+local knowledge roots); the slot
        definition stays in the Skill meta. Returns ranked candidates and
        per-slot satisfaction so planning/routing can gate on required slots.
        Empty ``slots`` for a Skill that has not declared any yet.
        """
        entry = self._skill_by_id(skill_id)
        knowledge = self.knowledge
        by_xid = {item.xid: item for item in knowledge}
        resolved: list[dict] = []
        for slot in entry.knowledge_slots:
            name = slot.get("slot") or slot.get("name")
            bind = slot.get("bind")
            domain = slot.get("domain")
            min_count = _slot_int(slot.get("min"), 0)
            required = _slot_bool(slot.get("required"))
            if bind:
                match = by_xid.get(str(bind))
                query = None
                candidates = [match.to_dict()] if match else []
            else:
                query = str(slot.get("query") or name or "")
                ranked = _rank_entries(query, knowledge)
                if domain:
                    ranked = [item for item in ranked if item.domain == domain]
                candidates = [item.to_dict() for item in ranked[: _slot_int(slot.get("limit"), 5)]]
            satisfied = len(candidates) >= max(min_count, 1) if required else True
            resolved.append(
                {
                    "slot": name,
                    "query": query,
                    "bind": str(bind) if bind else None,
                    "domain": domain,
                    "min": min_count,
                    "required": required,
                    "candidates": candidates,
                    "satisfied": satisfied,
                }
            )
        return {
            "skill_id": entry.skill_id,
            "slots": resolved,
            "unsatisfied_required": [
                slot["slot"]
                for slot in resolved
                if slot["required"] and not slot["satisfied"]
            ],
        }

    def rank_skills_for_purpose(self, purpose: str, limit: int = 5) -> list[dict]:
        query_tokens = _tokens(purpose)
        query_categories = _routing_categories(query_tokens)
        results: list[SkillRankResult] = []
        available_tools = {tool.tool_id: tool.version for tool in self.tools}
        for skill in self.skills:
            facets: list[str] = []
            score = 0.0
            for label, values, weight in [
                ("skill_id", [skill.skill_id], 0.15),
                ("intent", skill.intent, 0.25),
                ("target", skill.target_artifacts, 0.25),
                ("applies_when", skill.applies_when, 0.2),
                ("summary", [skill.summary], 0.2),
                ("inputs", skill.inputs, 0.1),
                ("outputs", skill.outputs, 0.15),
                (
                    "knowledge_slots",
                    [_knowledge_slot_text(slot) for slot in skill.knowledge_slots],
                    0.1,
                ),
                # Skill-centric consolidation (084 M4): the triad is the routing
                # vocabulary. Empty for un-migrated skills, so this is additive.
                ("capability", [skill.capability], 0.2),
                ("tuning", [skill.tuning], 0.2),
                ("responsibility", [skill.responsibility], 0.2),
            ]:
                matched = _matched_values(query_tokens, values)
                if matched:
                    facets.extend(f"{label}={value}" for value in matched[:3])
                    score += weight
                    score += min(0.1, 0.02 * _overlap_count(query_tokens, matched))
            matched_categories = _matched_routing_categories(skill, query_categories)
            for category, matches in matched_categories.items():
                category_weight = ROUTING_CATEGORY_WEIGHTS.get(category, 0.0)
                score += category_weight
                score += min(0.15, 0.03 * len(matches))
                facets.extend(f"{category}={value}" for value in matches[:3])
            if skill.skill_id in query_tokens:
                score += 0.6
                facets.append(f"skill_id_alias={skill.skill_id}")
            if (
                "activity" in matched_categories
                and "artifact" in matched_categories
                and _has_required_category_coverage(query_categories, matched_categories)
            ):
                score += 1.0
            blocked = _matched_values(query_tokens, skill.not_for, use_stop_words=True)
            if blocked:
                facets.extend(f"not_for={value}" for value in blocked[:3])
                score *= 0.75
            score *= _category_coverage_multiplier(query_categories, matched_categories)
            if "roslyn" in query_tokens and "roslyn" in _tokens(
                " ".join([skill.skill_id, skill.summary, *skill.applies_when])
            ):
                score += 0.15
            missing_tools = [
                item.get("tool_id", "")
                for item in skill.required_tools
                if item.get("tool_id") and item.get("tool_id") not in available_tools
            ]
            # Declared preconditions travel with the ranking so the client can
            # filter to Skills runnable in the current state (084 M4). Empty
            # until metas adopt preconditions; tool-availability stays the only
            # server-known readiness signal.
            readiness = {
                "runnable": not missing_tools,
                "missing_tool_contracts": missing_tools,
                "declared_preconditions": skill.preconditions,
            }
            if score <= 0:
                continue
            results.append(
                SkillRankResult(
                    skill_id=skill.skill_id,
                    summary=skill.summary,
                    maturity=skill.maturity,
                    matched_facets=facets,
                    matched_categories=matched_categories,
                    closure_preview=skill.closure_contract,
                    required_knowledge=skill.required_knowledge,
                    execution_readiness=readiness,
                    score=round(score, 4),
                )
            )
        results.sort(key=lambda item: item.score, reverse=True)
        return [item.to_dict() for item in results[:limit]]

    def list_tool_contracts(self) -> list[dict]:
        return [contract.to_dict() for contract in self.tools]

    def get_client_tool_manifest(self) -> dict:
        return _client_tool_distribution(self.repo_root).to_dict()

    def get_client_tool_file(self, path: str) -> dict:
        normalized = path.replace("\\", "/")
        for tool_file in _client_tool_files(self.repo_root):
            if tool_file.path == normalized:
                return tool_file.to_dict()
        raise KeyError(f"client tool file not found: {path}")

    def get_client_tool_bundle(self) -> dict:
        return {
            "distribution": _client_tool_distribution(self.repo_root).to_dict(),
            "files": [file.to_dict() for file in _client_tool_files(self.repo_root)],
        }

    def get_client_tool_pip_package(self) -> dict:
        return _client_tool_pip_package(self.repo_root).to_dict()

    def check_client_tool_versions(self, installed: dict[str, str] | None = None) -> dict:
        installed = installed or {}
        expected = {
            CLIENT_TOOL_PACKAGE_ID: CLIENT_TOOL_PACKAGE_VERSION,
            "xrefkit-client-tools": CLIENT_TOOL_PACKAGE_VERSION,
        }
        results: list[dict[str, str | bool]] = []
        overall_ok = True
        for package_id, version in expected.items():
            actual = installed.get(package_id)
            ok = actual == version
            if not ok:
                overall_ok = False
            status = "ok" if ok else "missing" if actual is None else "mismatch"
            results.append(
                {
                    "package_id": package_id,
                    "expected_version": version,
                    "installed_version": actual or "",
                    "status": status,
                    "ok": ok,
                }
            )
        return {
            "ok": overall_ok,
            "expected": expected,
            "results": results,
            "instructions": [
                "Client should call this after selecting a Skill that declares client-side required_tools.",
                "If ok is false, install the package returned by get_client_tool_pip_package before executing that Skill's client-side tools.",
            ],
        }

    def get_xrefkit_runtime_manifest(self) -> dict:
        return _xrefkit_runtime_distribution(self.repo_root).to_dict()

    def get_xrefkit_runtime_file(self, path: str) -> dict:
        normalized = path.replace("\\", "/")
        for file in _xrefkit_runtime_files(self.repo_root):
            if file.path == normalized:
                return file.to_dict()
        raise KeyError(f"xrefkit runtime file not found: {path}")

    def get_xrefkit_runtime_bundle(self) -> dict:
        return {
            "distribution": _xrefkit_runtime_distribution(self.repo_root).to_dict(),
            "files": [file.to_dict() for file in _xrefkit_runtime_files(self.repo_root)],
        }

    def get_xrefkit_runtime_pip_package(self) -> dict:
        return _xrefkit_runtime_pip_package(self.repo_root).to_dict()

    def check_xrefkit_runtime_version(self, installed: dict[str, str] | None = None) -> dict:
        installed = installed or {}
        expected = {XREFKIT_RUNTIME_PACKAGE_ID: _xrefkit_runtime_version(self.repo_root)}
        results: list[dict[str, str | bool]] = []
        overall_ok = True
        for package_id, version in expected.items():
            actual = installed.get(package_id)
            ok = actual == version
            if not ok:
                overall_ok = False
            status = "ok" if ok else "missing" if actual is None else "mismatch"
            results.append(
                {
                    "package_id": package_id,
                    "expected_version": version,
                    "installed_version": actual or "",
                    "status": status,
                    "ok": ok,
                }
            )
        return {
            "ok": overall_ok,
            "expected": expected,
            "results": results,
            "instructions": [
                "Unlike client-side per-Skill tools, fetch and materialize the xrefkit "
                "runtime right after get_startup_context, before any Skill "
                "routing, since Skill execution requires python -m xrefkit skill run "
                "immediately.",
                "If ok is false, install the package returned by "
                "get_xrefkit_runtime_pip_package, or materialize files from "
                "get_xrefkit_runtime_bundle at the xrefkit/ path in the client repository "
                "root, before running python -m xrefkit.",
            ],
        }

    def get_document_by_xid(
        self,
        xid: str,
        known_version: str | None = None,
    ) -> dict:
        matches = _managed_markdown_matches_by_xid(self.repo_root, self.ownership, xid)
        matches.extend(_external_markdown_matches_by_xid(self.domain_knowledge_roots, xid))
        if len(matches) > 1:
            return {
                "ok": False,
                "error": "xid_conflict",
                "xid": xid,
                "message": "multiple catalog-visible documents declare this XID; refusing path-order selection",
                "matches": [
                    _document_conflict_match(self.repo_root, self.ownership, path, text)
                    for path, text in matches
                ],
            }
        if len(matches) == 1:
            path, text = matches[0]
            return _conditional_document_response(
                _xref_document_for_catalog(self.repo_root, self.domain_knowledge_roots, path, text),
                known_version,
                self.repository_fingerprint,
            )
        embedded = _embedded_startup_document(xid)
        if embedded is not None:
            return _conditional_document_response(
                embedded,
                known_version,
                self.repository_fingerprint,
            )
        raise KeyError(f"document xid not found: {xid}")

    def get_startup_context(
        self,
        known_document_versions: dict[str, str] | None = None,
    ) -> dict:
        known_document_versions = known_document_versions or {}
        references: list[StartupReference] = []
        missing: list[dict[str, str]] = []
        managed_documents = _managed_markdown_by_xid(self.repo_root, self.ownership)
        for expected_xid, layer in STARTUP_REFERENCE_DEFINITIONS:
            resolved = managed_documents.get(expected_xid)
            embedded = False
            if resolved is None:
                embedded_document = _embedded_startup_document(expected_xid)
                if embedded_document is None:
                    missing.append(
                        {
                            "xid": expected_xid,
                            "reason": "startup reference XID not found",
                        }
                    )
                    continue
                embedded = True
                text = embedded_document.content
            else:
                path, text = resolved
            rel_path = (
                f"xrefkit/resources/base/startup_sources/{EMBEDDED_STARTUP_SOURCE_PATHS[expected_xid]}"
                if embedded
                else relative_to_repo(path, self.repo_root)
            )
            document = (
                _embedded_startup_document(expected_xid)
                if embedded
                else _xref_document(path, self.repo_root, text)
            )
            known_version = known_document_versions.get(expected_xid)
            not_modified = known_version == document.content_hash
            cache_status = (
                "not_modified"
                if not_modified
                else "modified"
                if known_version
                else "bypassed"
            )
            references.append(
                StartupReference(
                    xid=expected_xid,
                    title=first_heading(text, Path(rel_path).stem),
                    layer=layer,  # type: ignore[arg-type]
                    required_at_init=True,
                    summary=first_paragraph(text),
                    content=None,
                    links=markdown_xid_link_targets(text),
                    content_hash=document.content_hash,
                    cache_status=cache_status,
                    content_omitted=True,
                    included_in_startup_contract_pack=True,
                    cache_policy={"cache_recommended": False, "reason": "startup body represented by startup_contract_pack"},
                    repository_fingerprint=self.repository_fingerprint,
                )
            )
        pack_resolved = managed_documents.get(STARTUP_CONTRACT_PACK_XID)
        pack_document_text = pack_resolved[1] if pack_resolved else None
        startup_contract_pack = _startup_contract_pack(references, pack_document_text)
        client_instructions = _client_instructions()
        if startup_contract_pack["stale"]:
            stale_xids = [
                str(item["xid"]) for item in startup_contract_pack["stale_sources"]
            ]
            client_instructions = [
                *client_instructions,
                "startup_contract_pack is STALE: the source documents "
                f"{', '.join(stale_xids)} changed after the pack was authored "
                "(based_on_hashes no longer match source_hashes). Treat the "
                "pack wording as potentially outdated for those areas, resolve "
                "the live sources with get_document_by_xid, and escalate to "
                "the repository maintainers to regenerate the pack.",
            ]
        return StartupContext(
            catalog_version=self.catalog_version,
            repository_identity=self.get_repository_identity(),
            access_policy={
                "mode": "mcp_only",
                "source_of_truth": "xrefkit.mcp",
                "applies_to": [
                    "startup references",
                    "XID-linked Markdown documents",
                    "Skill meta and procedure content",
                    "workflow definitions",
                    "knowledge catalog entries",
                    "tool contracts",
                    "closure contracts",
                    "unknown protocol",
                    "AI Decision Trace Protocol",
                ],
                "forbidden_client_shortcuts": [
                    "Do not read XRefKit governance Markdown directly from the client filesystem when this MCP server is configured.",
                    "Do not resolve transferred Markdown links by filesystem path.",
                    "Do not open local Skill files to bypass get_skill.",
                    "Do not interpret path-like response fields such as meta_path, skill_doc, path, or path#xid text as client filesystem fetch instructions.",
                    "Do not treat a local checkout as authoritative unless the user explicitly disables MCP-only mode.",
                ],
                "required_tools": {
                    "cache_identity": "get_repository_identity",
                    "startup": "get_startup_context",
                    "xid_link_resolution": "get_document_by_xid",
                    "skill_content": "get_skill",
                    "decision_trace_runtime": "get_xrefkit_runtime_bundle",
                },
            },
            context_injection_policy=_context_injection_policy(),
            session_context_deduplication=_session_context_deduplication(),
            core_runtime_distribution=_xrefkit_runtime_distribution(self.repo_root).to_dict(),
            repository_zones=_repository_zones(self.ownership),
            client_instructions=client_instructions,
            client_obligations=_client_obligations(),
            link_resolution={
                "link_field": "links",
                "xid_field": "xid",
                "resolver_tool": "get_document_by_xid",
                "resolver_argument": "xid",
                "version_field": "content_hash",
                "conditional_argument": "known_version",
                "path_handling": "server_side_identity_or_diagnostic_only",
                "client_filesystem_resolution": "forbidden",
                "example_call": "get_document_by_xid({\"xid\": \"8A666C1FD121\"})",
            },
            load_order=[reference.xid for reference in references],
            startup_contract_pack=startup_contract_pack,
            prompt_flow_protocol=_prompt_flow_protocol(),
            references=references,
            semantic_routing_references=_semantic_routing_references(),
            missing=missing,
        ).to_dict()

    def _knowledge_by_xid(self, xid: str) -> tuple[KnowledgeCatalogEntry, str]:
        matches: list[tuple[KnowledgeCatalogEntry, str]] = []
        for entry, text in self._scan_knowledge():
            if entry.xid == xid:
                matches.append((entry, text))
        if len(matches) > 1:
            raise ValueError(
                "knowledge xid conflict: "
                f"{xid} appears in multiple catalog-visible knowledge entries"
            )
        if len(matches) == 1:
            return matches[0]
        raise KeyError(f"knowledge xid not found: {xid}")

    def _skill_by_id(self, skill_id: str) -> SkillCatalogEntry:
        matches = [entry for entry in self.skills if entry.skill_id == skill_id]
        if len(matches) > 1:
            paths = [entry.meta_path for entry in matches]
            raise ValueError(
                "skill identity conflict: "
                f"{skill_id} appears in multiple catalog-visible entries: {paths}"
            )
        if len(matches) == 1:
            return matches[0]
        raise KeyError(f"skill not found: {skill_id}")


def _client_instructions() -> list[str]:
    return [
        "A client may call get_repository_identity as a content-free cache namespace preflight; get_startup_context remains the first governance-content load.",
        "Fetch core_runtime_distribution (get_xrefkit_runtime_bundle or get_xrefkit_runtime_pip_package) immediately after this call, unconditionally. Unlike client_tool_download, this is not gated behind Skill selection: Skill execution requires python -m xrefkit skill run right after a Skill is chosen.",
        "Materialize and apply startup references in load_order before routing task-specific work. Applying a reference means enforcing its operational contract in the client runtime; it does not require injecting the full document body into the model prompt unless context_injection_policy requires it.",
        "MCP-only mode is active: treat this MCP response as the source of truth for XRefKit governance content.",
        "Do not read XRefKit governance Markdown from the client filesystem while MCP-only mode is active.",
        "Do not assume referenced Markdown files exist on the client filesystem.",
        "Treat path-like metadata such as meta_path, skill_doc, path, or path#xid text as server-side identity or diagnostic metadata only; do not open it through the client filesystem for governance content.",
        "Do not automatically load all links from startup references; use links only when the current task actually needs them.",
        "When transferred Markdown content includes links entries, resolve a needed link by calling get_document_by_xid with the link xid.",
        "Use the returned document content as the authoritative text for that XID.",
        "If one user prompt spans multiple runs, initialize one Prompt Flow from prompt_flow_protocol before Skill routing and preserve its correlation fields through reconciliation and closure.",
        "At startup, record the XIDs used for client-side routing, policy, or context-injection decisions in a client-side audit log.",
        "For Skill entries, use skill_content as the procedure body and resolve skill_links through get_document_by_xid when needed.",
        "After python -m xrefkit skill run returns run_id and run_log, call bind_skill_run with run_id and skill_id, then execute the returned client_record_command with <run-log> replaced by run_log before task-specific XID access.",
        "AI Decision Trace Protocol is standard for every Skill Run and instruction-backed workflow run: use the client-side xrefkit runtime's trace checkpoint/event/impact/return operations, keep work provisional until human evaluation, and do not treat MCP server-side audit records as a substitute for the decision-trace ledger.",
        "MCP xid.resolved audit events prove server resolution only. After a body is actually injected into model context, record knowledge load with xrefkit skill knowledge --action load; after it supports a judgment or artifact, record --action apply.",
        "Keep client-side XID document cache entries only when cache_policy.cache_recommended is true.",
        "Fetch client-side tool manifests or packages only after a selected Skill declares client-side required_tools.",
        "Send cached content_hash values as known_version or known_document_versions; when cache_status is not_modified, use the locally hash-validated body instead of downloading it again.",
    ]


def _content_files(
    root: Path,
    ownership: Ownership | None,
    family: str,
    pattern: str,
) -> list[Path]:
    paths: list[Path] = []
    base = root / family
    if base.exists():
        paths.extend(
            path
            for path in sorted(base.glob(f"**/{pattern}"))
            if _catalog_enabled(root, ownership, path)
        )
    packs_root = root / "packs"
    if ownership is not None and packs_root.exists():
        paths.extend(
            path
            for path in sorted(packs_root.glob(f"*/{family}/**/{pattern}"))
            if _catalog_enabled(root, ownership, path)
        )
        paths.extend(
            path
            for path in sorted(packs_root.glob(f"local/*/{family}/**/{pattern}"))
            if _catalog_enabled(root, ownership, path)
        )
    return sorted(set(paths))


def _catalog_enabled(root: Path, ownership: Ownership | None, path: Path) -> bool:
    if ownership is None:
        return True
    return ownership.catalog_enabled(relative_to_repo(path, root))


def _zone_metadata(ownership: Ownership | None, rel_path: str) -> dict[str, object]:
    if ownership is None:
        return {
            "ownership_enabled": False,
            "zone": None,
            "owner": None,
            "pack_id": None,
            "local_only": False,
            "catalog": True,
            "distribution": True,
            "shadowing": False,
        }
    metadata = ownership.metadata_for(rel_path)
    metadata["ownership_enabled"] = True
    return metadata


def _knowledge_entry(
    root: Path,
    ownership: Ownership | None,
    path: Path,
    text: str,
) -> KnowledgeCatalogEntry:
    xid = first_xid(text)
    missing: list[str] = []
    if not xid:
        xid = f"path:{relative_to_repo(path, root)}"
        missing.append("xid")
    rel = relative_to_repo(path, root)
    parts = Path(rel).parts
    domain = parts[1] if len(parts) > 2 else "knowledge"
    links = markdown_xid_links(text)
    return KnowledgeCatalogEntry(
        xid=xid,
        version=1,
        content_hash=stable_hash(text),
        revised_at=file_last_modified(path),
        title=first_heading(text, path.stem),
        domain=domain,
        summary=first_paragraph(text),
        applies_when=[],
        requires_knowledge=links,
        related_skills=[],
        related_capabilities=[],
        path=rel,
        missing=missing,
        zone_metadata=_zone_metadata(ownership, rel),
    )


def _external_knowledge_entry(root: Path, path: Path, text: str) -> KnowledgeCatalogEntry:
    xid = first_xid(text)
    if not xid:
        raise ValueError(f"external domain knowledge must declare an XID: {path}")
    rel = _external_relative_path(root, path)
    parts = Path(rel).parts
    domain = parts[0] if len(parts) > 1 else "external_domain_knowledge"
    logical_path = f"external-domain-knowledge/{stable_hash(str(root))[:12]}/{rel}"
    return KnowledgeCatalogEntry(
        xid=xid,
        version=1,
        content_hash=stable_hash(text),
        revised_at=file_last_modified(path),
        title=first_heading(text, path.stem),
        domain=domain,
        summary=first_paragraph(text),
        applies_when=[],
        requires_knowledge=markdown_xid_links(text),
        related_skills=[],
        related_capabilities=[],
        path=logical_path,
        missing=[],
        zone_metadata={
            "ownership_enabled": False,
            "zone": "external_domain_knowledge",
            "owner": None,
            "pack_id": None,
            "local_only": False,
            "catalog": True,
            "distribution": True,
            "shadowing": False,
        },
    )


def _resolve_domain_knowledge_root(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise NotADirectoryError(root)
    return root


def _external_knowledge_files(root: Path) -> list[Path]:
    return sorted(path for path in root.glob("**/*.md") if path.is_file())


def _external_relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _managed_markdown_files(root: Path, ownership: Ownership | None = None) -> list[Path]:
    files: list[Path] = []
    for dirname in ["agent", "docs", "knowledge", "skills"]:
        base = root / dirname
        if base.exists():
            files.extend(
                path
                for path in sorted(base.glob("**/*"))
                if path.is_file()
                and path.suffix.lower() in XID_DOCUMENT_SUFFIXES
                and _catalog_enabled(root, ownership, path)
            )
    packs_root = root / "packs"
    if ownership is not None and packs_root.exists():
        files.extend(
            path
            for path in sorted(packs_root.glob("*/**/*"))
            if path.is_file()
            and path.suffix.lower() in XID_DOCUMENT_SUFFIXES
            and _catalog_enabled(root, ownership, path)
        )
    return files


def _managed_markdown_by_xid(root: Path, ownership: Ownership | None = None) -> dict[str, tuple[Path, str]]:
    documents: dict[str, tuple[Path, str]] = {}
    for path in _managed_markdown_files(root, ownership):
        text = read_text(path)
        xid = first_xid(text)
        if xid:
            previous = documents.get(xid)
            if previous is not None:
                raise ValueError(
                    f"duplicate catalog-visible XID {xid}: "
                    f"{relative_to_repo(previous[0], root)} and {relative_to_repo(path, root)}"
                )
            documents[xid] = (path, text)
    return documents


def _embedded_startup_document(xid: str) -> XRefDocument | None:
    filename = EMBEDDED_STARTUP_SOURCE_PATHS.get(xid)
    if filename is None:
        return None
    path = Path(__file__).resolve().parent.parent / "resources" / "base" / "startup_sources" / filename
    if not path.is_file():
        return None
    text = read_text(path)
    content = markdown_xid_only_text(text)
    return XRefDocument(
        xid=xid,
        title=first_heading(text, path.stem),
        path=f"xrefkit/resources/base/startup_sources/{filename}",
        summary=first_paragraph(text),
        content=content,
        links=markdown_xid_link_targets(text),
        content_hash=stable_hash(content),
    )


def _managed_markdown_matches_by_xid(
    root: Path,
    ownership: Ownership | None,
    xid: str,
) -> list[tuple[Path, str]]:
    matches: list[tuple[Path, str]] = []
    for path in _managed_markdown_files(root, ownership):
        text = read_text(path)
        if first_xid(text) == xid:
            matches.append((path, text))
    return matches


def _external_markdown_matches_by_xid(
    roots: tuple[Path, ...],
    xid: str,
) -> list[tuple[Path, str]]:
    matches: list[tuple[Path, str]] = []
    for root in roots:
        for path in _external_knowledge_files(root):
            text = read_text(path)
            if first_xid(text) == xid:
                matches.append((path, text))
    return matches


def _duplicate_skill_ids(entries: list[SkillCatalogEntry]) -> dict[str, list[str]]:
    by_id: dict[str, list[str]] = {}
    for entry in entries:
        by_id.setdefault(entry.skill_id, []).append(entry.meta_path)
    return {skill_id: paths for skill_id, paths in by_id.items() if len(paths) > 1}


def _xref_document(path: Path, root: Path, text: str) -> XRefDocument:
    xid = first_xid(text)
    if not xid:
        xid = f"path:{relative_to_repo(path, root)}"
    content = markdown_xid_only_text(text)
    return XRefDocument(
        xid=xid,
        title=first_heading(text, path.stem),
        path=relative_to_repo(path, root),
        summary=first_paragraph(text),
        content=content,
        links=markdown_xid_link_targets(text),
        content_hash=stable_hash(content),
    )


def _external_xref_document(path: Path, text: str) -> XRefDocument:
    xid = first_xid(text)
    if not xid:
        raise ValueError(f"external domain knowledge must declare an XID: {path}")
    content = markdown_xid_only_text(text)
    return XRefDocument(
        xid=xid,
        title=first_heading(text, path.stem),
        path=f"external-domain-knowledge/{xid}.md",
        summary=first_paragraph(text),
        content=content,
        links=markdown_xid_link_targets(text),
        content_hash=stable_hash(content),
    )


def _path_in_roots(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        return True
    return False


def _xref_document_for_catalog(
    repo_root: Path,
    external_roots: tuple[Path, ...],
    path: Path,
    text: str,
) -> XRefDocument:
    if _path_in_roots(path, external_roots):
        return _external_xref_document(path, text)
    return _xref_document(path, repo_root, text)


def _document_conflict_match(
    repo_root: Path,
    ownership: Ownership | None,
    path: Path,
    text: str,
) -> dict[str, object]:
    try:
        rel = relative_to_repo(path, repo_root)
    except ValueError:
        return {
            "source": "external_domain_knowledge",
            "content_hash": _external_xref_document(path, text).content_hash,
            "zone_metadata": {
                "ownership_enabled": False,
                "zone": "external_domain_knowledge",
                "owner": None,
                "pack_id": None,
                "local_only": False,
                "catalog": True,
                "distribution": True,
                "shadowing": False,
            },
        }
    return {
        "source": "repository",
        "path": rel,
        "content_hash": _xref_document(path, repo_root, text).content_hash,
        "zone_metadata": _zone_metadata(ownership, rel),
    }


def _conditional_document_response(
    document: XRefDocument,
    known_version: str | None,
    repository_fingerprint: str,
) -> dict:
    cache_policy = _document_cache_policy(document, repository_fingerprint)
    if (
        known_version == document.content_hash
        and cache_policy["cache_recommended"]
    ):
        return {
            "xid": document.xid,
            "title": document.title,
            "content_hash": document.content_hash,
            "repository_fingerprint": repository_fingerprint,
            "cache_status": "not_modified",
            "content_omitted": True,
        }

    result = document.to_dict()
    result.update(
        {
            "repository_fingerprint": repository_fingerprint,
            "cache_status": (
                "bypassed"
                if known_version == document.content_hash
                else "modified"
                if known_version
                else "miss"
            ),
            "content_omitted": False,
            "cache_policy": cache_policy,
        }
    )
    return result


def _document_cache_policy(
    document: XRefDocument,
    repository_fingerprint: str,
) -> dict:
    full_document = document.to_dict()
    full_document["repository_fingerprint"] = repository_fingerprint
    version_request = {
        "xid": document.xid,
        "known_version": document.content_hash,
    }
    not_modified_response = {
        "xid": document.xid,
        "title": document.title,
        "content_hash": document.content_hash,
        "repository_fingerprint": repository_fingerprint,
        "cache_status": "not_modified",
        "content_omitted": True,
    }
    version_payload_bytes = _json_size(version_request) + _json_size(
        not_modified_response
    )
    document_payload_bytes = _json_size(full_document)
    ratio = (
        version_payload_bytes / document_payload_bytes
        if document_payload_bytes
        else 1.0
    )
    return {
        "cache_recommended": (
            not document.xid.startswith("path:")
            and ratio < CACHE_MAX_VERSION_PAYLOAD_RATIO
        ),
        "version_payload_bytes": version_payload_bytes,
        "document_payload_bytes": document_payload_bytes,
        "version_to_document_ratio": round(ratio, 6),
        "maximum_ratio": CACHE_MAX_VERSION_PAYLOAD_RATIO,
        "measurement_scope": "application_json_without_mcp_envelope",
    }


def _json_size(value: object) -> int:
    return len(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )


def _skill_document_versions(
    entry: SkillCatalogEntry,
    root: Path,
    repository_fingerprint: str,
) -> list[dict]:
    versions: list[dict] = []
    for relative_path, text in [
        (entry.meta_path, entry.meta_content),
        (entry.path, entry.skill_content),
    ]:
        document = _xref_document(root / relative_path, root, text)
        versions.append(
            {
                "xid": document.xid,
                "path": document.path,
                "content_hash": document.content_hash,
                "repository_fingerprint": repository_fingerprint,
                "cache_policy": _document_cache_policy(
                    document,
                    repository_fingerprint,
                ),
            }
        )
    return versions


def _startup_contract_pack(
    references: list[StartupReference],
    pack_document_text: str | None,
) -> dict[str, object]:
    source_xids = [reference.xid for reference in references]
    expected_xids = [xid for xid, _layer in STARTUP_REFERENCE_DEFINITIONS]
    if source_xids != expected_xids:
        missing = [xid for xid in expected_xids if xid not in source_xids]
        extra = [xid for xid in source_xids if xid not in expected_xids]
        raise ValueError(
            "startup contract pack source XIDs do not match required startup order: "
            f"missing={missing}, extra={extra}"
        )
    source_hashes: dict[str, str] = {}
    for reference in references:
        if not reference.content_hash:
            raise ValueError(f"startup reference missing content_hash: {reference.xid}")
        source_hashes[reference.xid] = reference.content_hash

    # The pack is a hand-compressed derivation of the source documents, so
    # it can drift when a source changes. Authoritative body: the pack
    # document in the served repository (authored and reviewed next to its
    # sources); fallback: the body embedded in this package. Either way the
    # based_on hashes recorded at authoring time are compared against the
    # live source hashes and any mismatch is reported as staleness instead
    # of being silently served.
    if pack_document_text is not None:
        body = normalize_pack_body(markdown_xid_only_text(pack_document_text))
        based_on_hashes = parse_based_on_hashes(pack_document_text)
        pack_version = parse_pack_version(pack_document_text) or 1
        pack_source = "repository_document"
        pack_doc_xid: str | None = STARTUP_CONTRACT_PACK_XID
    else:
        body = normalized_startup_contract_pack_body()
        based_on_hashes = dict(EMBEDDED_BASED_ON_HASHES)
        pack_version = 1
        pack_source = "embedded_fallback"
        pack_doc_xid = None

    stale_sources: list[dict[str, str | None]] = []
    for xid in source_xids:
        based_on = based_on_hashes.get(xid)
        if based_on != source_hashes[xid]:
            stale_sources.append(
                {
                    "xid": xid,
                    "based_on_hash": based_on,
                    "live_hash": source_hashes[xid],
                }
            )
    return {
        "mode": "required_startup_contract_pack",
        "pack_version": pack_version,
        "pack_source": pack_source,
        "pack_doc_xid": pack_doc_xid,
        "source_xids": source_xids,
        "source_hashes": source_hashes,
        "based_on_hashes": based_on_hashes,
        "stale": bool(stale_sources),
        "stale_sources": stale_sources,
        "pack_hash": stable_hash(body),
        "body": body,
    }


def _build_skill_entry(root: Path, ownership: Ownership | None, meta_path: Path) -> SkillCatalogEntry:
    text = read_text(meta_path)
    meta = parse_meta_bullets(text)
    skill_id = str(meta.get("skill_id") or meta_path.parent.name)
    skill_doc_value = str(meta.get("skill_doc") or "./SKILL.md")
    skill_doc = (meta_path.parent / skill_doc_value).resolve()
    skill_text = read_text(skill_doc) if skill_doc.exists() else ""
    missing = _missing_skill_fields(meta, skill_doc.exists())
    knowledge_refs = scalar_list(meta, "knowledge_refs")
    knowledge_slots = _parse_knowledge_slots(meta)
    closure = ClosureContract(
        closure_conditions=scalar_list(meta, "closure")
        or _section_bullets(skill_text, "Closure"),
        exit_enum=["completed", "blocked", "needs_input"],
        handoff_policy=str(meta.get("constraints") or "explicit handoff required"),
        worklist_policy=str(
            _nested_value(meta, "os_contract", "worklist_policy") or "required"
        ),
    )
    rel_meta = relative_to_repo(meta_path, root)
    return SkillCatalogEntry(
        skill_id=skill_id,
        title=first_heading(skill_text or text, skill_id),
        summary=str(meta.get("summary") or first_paragraph(skill_text)),
        maturity=str(meta.get("maturity") or "unknown"),
        intent=_derive_intent(meta),
        target_artifacts=_derive_target_artifacts(meta),
        applies_when=scalar_list(meta, "applies_when")
        or scalar_list(meta, "use_when"),
        not_for=scalar_list(meta, "not_for")
        or _split_constraints(str(meta.get("constraints") or "")),
        required_knowledge=(
            [_knowledge_req(item) for item in knowledge_refs]
            + [_bind_knowledge_req(slot) for slot in knowledge_slots if slot.get("bind")]
        ),
        required_tools=[_required_tool(item) for item in scalar_list(meta, "required_tools")],
        inputs=scalar_list(meta, "input"),
        outputs=scalar_list(meta, "output"),
        closure_contract=closure,
        meta_content=text,
        meta_links=markdown_xid_link_targets(text),
        skill_content=skill_text,
        skill_links=markdown_xid_link_targets(skill_text),
        path=relative_to_repo(skill_doc, root) if skill_doc.exists() else "",
        meta_path=rel_meta,
        context_size=_skill_context_size(
            text,
            skill_text,
            scalar_list(meta, "output"),
            closure,
        ),
        # Skill-centric consolidation (083/084): surface the triad and declared
        # needs as an additive superset. `responsibility` is the new explicit
        # field that replaces role_responsibilities.executor (which was always a
        # responsibility, not a role). Empty where a meta has not adopted the new
        # fields yet; the legacy nested bullets stay opaque in meta_content.
        capability=str(meta.get("capability") or ""),
        tuning=str(meta.get("tuning") or ""),
        responsibility=str(meta.get("responsibility") or ""),
        preconditions=scalar_list(meta, "preconditions"),
        knowledge_slots=knowledge_slots,
        missing=missing,
        zone_metadata=_zone_metadata(ownership, rel_meta),
    )


def _slot_int(value: object, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _slot_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _parse_slot_spec(spec: str) -> dict:
    """Parse a compact meta slot spec that the bullet parser can carry.

    Interim markdown form (until the meta schema settles in the XRefKit-side
    migration): `name=<slot>; query=<text>; domain=<d>; min=<n>; required;
    bind=<xid>`. Fields are `;`-separated `key=value` pairs (a bare token means
    `token=true`), so a `query` may contain spaces. `name` normalizes to `slot`.
    """
    slot: dict = {}
    for field_text in spec.split(";"):
        field_text = field_text.strip()
        if not field_text:
            continue
        if "=" in field_text:
            key, _, val = field_text.partition("=")
            key, val = key.strip(), val.strip()
        else:
            key, val = field_text, "true"
        slot[key] = val
    if "name" in slot and "slot" not in slot:
        slot["slot"] = slot.pop("name")
    return slot


def _parse_knowledge_slots(meta: dict) -> list[dict]:
    """Normalize declared knowledge slots (design 082 Decision 3).

    Slots are the meta-declared knowledge needs that replace static
    knowledge_refs; each is resolved at runtime against the base+local catalog.
    Tolerant during the transition: returns [] when a meta has not adopted
    knowledge_slots yet, parses compact string specs, and passes mapping entries
    through unchanged.
    """
    value = meta.get("knowledge_slots")
    if not isinstance(value, list):
        return []
    slots: list[dict] = []
    for item in value:
        if isinstance(item, dict):
            slots.append(dict(item))
        elif isinstance(item, str) and item.strip():
            slots.append(_parse_slot_spec(item))
    return slots


def _build_skills(root: Path, ownership: Ownership | None = None) -> list[SkillCatalogEntry]:
    entries: list[SkillCatalogEntry] = []
    for meta_path in _content_files(root, ownership, "skills", "meta.md"):
        entries.append(_build_skill_entry(root, ownership, meta_path))
    return entries


def _client_tool_distribution(root: Path) -> ClientToolDistribution:
    package_versions = {
        CLIENT_TOOL_PACKAGE_ID: CLIENT_TOOL_PACKAGE_VERSION,
        "xrefkit-client-tools": CLIENT_TOOL_PACKAGE_VERSION,
    }
    return ClientToolDistribution(
        package_id=CLIENT_TOOL_PACKAGE_ID,
        version=CLIENT_TOOL_PACKAGE_VERSION,
        execution_location="client",
        server_executes_tools=False,
        install_layout="write each file to the same relative path under the client-side target repository root",
        required_package_ids=sorted(package_versions),
        package_versions=package_versions,
        file_hash_algorithm="sha256",
        version_check_tool="check_client_tool_versions",
        materialization={
            "source": "xrefkit.mcp",
            "file_tool": "get_client_tool_file",
            "bundle_tool": "get_client_tool_bundle",
            "pip_package_tool": "get_client_tool_pip_package",
            "run_location": "client",
            "preserve_relative_paths": True,
        },
        update_policy={
            "check_on_startup": True,
            "install_when_missing": True,
            "update_when_version_mismatch": True,
            "server_executes_tools": False,
        },
        files=[
            ClientToolManifestEntry(
                path=file.path,
                kind=file.kind,
                content_hash=file.content_hash,
                size_bytes=file.size_bytes,
                run_hint=file.run_hint,
                resolver_tool="get_client_tool_file",
                resolver_argument="path",
            )
            for file in _client_tool_files(root)
        ],
        instructions=[
            "The MCP server only distributes these files; it must not execute them.",
            "Install files at their returned relative paths, typically under tools/ in the client-side repository.",
            "Run Python tools on the client side with the client repository root as the working directory.",
            "Some tools expect sibling tools modules, so preserve the returned directory layout.",
            "Some tools call external programs such as git, dotnet, npm, or project-specific commands; satisfy those prerequisites on the client side before execution.",
            "structure_graph is an analysis/build-side tool, not a baseline "
            "client dependency: the client consumes its output as findings "
            "knowledge, not the tool. If a specific Skill needs structure_graph "
            "client-side, that Skill declares and provisions it (Skill-scoped, "
            "prompt-supplemented); XRefKit.StructureGraph is not a global client "
            "requirement.",
            "This distribution also includes Skill-embedded scripts under skills/**/*.py that a Skill's SKILL.md instructs running directly by relative path (e.g. skills/<id>/scripts/*.py). get_client_tool_pip_package's tools/-only package does not include these; use get_client_tool_file or get_client_tool_bundle for them.",
        ],
    )


def _xrefkit_runtime_version(root: Path) -> str:
    runtime_root = _runtime_source_root(root)
    init_path = runtime_root / "__init__.py"
    if not init_path.exists():
        return "0.0.0"
    match = XREFKIT_RUNTIME_VERSION_RE.search(read_text(init_path))
    return match.group(1) if match else "0.0.0"


def _xrefkit_runtime_distribution(root: Path) -> ClientToolDistribution:
    version = _xrefkit_runtime_version(root)
    package_versions = {XREFKIT_RUNTIME_PACKAGE_ID: version}
    return ClientToolDistribution(
        package_id=XREFKIT_RUNTIME_PACKAGE_ID,
        version=version,
        execution_location="client",
        server_executes_tools=False,
        install_layout="write each file to the same relative path under the client-side target repository root",
        required_package_ids=sorted(package_versions),
        package_versions=package_versions,
        file_hash_algorithm="sha256",
        version_check_tool="check_xrefkit_runtime_version",
        materialization={
            "source": "xrefkit.mcp",
            "file_tool": "get_xrefkit_runtime_file",
            "bundle_tool": "get_xrefkit_runtime_bundle",
            "pip_package_tool": "get_xrefkit_runtime_pip_package",
            "run_location": "client",
            "preserve_relative_paths": True,
        },
        update_policy={
            "check_on_startup": True,
            "install_when_missing": True,
            "update_when_version_mismatch": True,
            "server_executes_tools": False,
            "gated_by_skill_selection": False,
            "fetch_timing": "immediately_after_get_startup_context",
        },
        files=[
            ClientToolManifestEntry(
                path=file.path,
                kind=file.kind,
                content_hash=file.content_hash,
                size_bytes=file.size_bytes,
                run_hint=file.run_hint,
                resolver_tool="get_xrefkit_runtime_file",
                resolver_argument="path",
            )
            for file in _xrefkit_runtime_files(root)
        ],
        instructions=[
            "The MCP server only distributes these files; it must not execute them.",
            "Unlike client_tool_download (tools/), this runtime is not gated "
            "behind Skill selection: fetch it right after get_startup_context, "
            "because Skill execution requires python -m xrefkit skill run "
            "immediately once a Skill is selected.",
            "Install files at their returned relative paths, at xrefkit/ in the "
            "client-side repository root.",
            "Run python -m xrefkit on the client side with the client repository "
            "root as the working directory.",
            "This package depends on PyYAML; install it (get_xrefkit_runtime_pip_package "
            "does this automatically) or ensure PyYAML is already available "
            "before running python -m xrefkit.",
        ],
    )


def _xrefkit_runtime_files(root: Path) -> list[ClientToolFile]:
    runtime_root = _runtime_source_root(root)
    if not runtime_root.exists():
        return []
    distributable_suffixes = {".py", ".json", ".yaml", ".yml", ".md"}
    paths = sorted(
        path
        for path in runtime_root.glob("**/*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix.lower() in distributable_suffixes
    )

    result: list[ClientToolFile] = []
    for path in paths:
        rel = "xrefkit/" + path.relative_to(runtime_root).as_posix()
        text = read_text(path)
        kind = _client_tool_kind(path)
        result.append(
            ClientToolFile(
                path=rel,
                kind=kind,
                content=text,
                content_hash=stable_hash(text),
                size_bytes=len(text.encode("utf-8")),
                run_hint="python -m xrefkit" if kind == "python" else None,
                imports=_python_imports(text) if kind == "python" else [],
                links=markdown_xid_link_targets(text),
            )
        )
    return result


def _runtime_source_root(root: Path) -> Path:
    """Select repository runtime when present, otherwise this MCP package."""
    repository_runtime = root / "xrefkit"
    if (repository_runtime / "__init__.py").is_file():
        return repository_runtime
    return Path(__file__).resolve().parent.parent


def _xrefkit_runtime_pip_package(root: Path) -> ClientToolPipPackage:
    files = _xrefkit_runtime_files(root)
    version = _xrefkit_runtime_version(root)
    package_root = f"{XREFKIT_RUNTIME_PACKAGE_ID}-{version}"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        _zip_writestr(
            archive,
            f"{package_root}/pyproject.toml",
            _xrefkit_runtime_pyproject(version),
        )
        _zip_writestr(
            archive,
            f"{package_root}/README.md",
            _xrefkit_runtime_readme(),
        )
        for file in files:
            _zip_writestr(archive, f"{package_root}/{file.path}", file.content)
    content = buffer.getvalue()
    encoded = base64.b64encode(content).decode("ascii")
    return ClientToolPipPackage(
        filename=f"{package_root}.zip",
        package_id=XREFKIT_RUNTIME_PACKAGE_ID,
        version=version,
        package_format="zip-sdist",
        install_command=f"python -m pip install {package_root}.zip",
        content_base64=encoded,
        content_hash=hashlib_sha256_bytes(content),
        size_bytes=len(content),
        warnings=[
            "This package installs a top-level xrefkit package; install it in a "
            "project virtual environment to avoid conflicts with any "
            "unrelated package named xrefkit.",
            "The MCP server only distributes the package; python -m xrefkit "
            "execution is client-side.",
        ],
    )


def _xrefkit_runtime_pyproject(version: str) -> str:
    return f"""[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "{XREFKIT_RUNTIME_PACKAGE_ID}"
version = "{version}"
description = "Portable XRefKit runtime distributed from XRefKit MCP"
readme = "README.md"
requires-python = ">=3.11"
dependencies = ["PyYAML>=6.0.2,<7", "pydantic>=2.0,<3"]

[tool.setuptools.packages.find]
include = ["xrefkit*"]

[tool.setuptools.package-data]
xrefkit = ["resources/**/*"]
"""


def _xrefkit_runtime_readme() -> str:
    return """# XRefKit Runtime

This package is generated by XRefKit MCP and installs the `xrefkit` package that
implements XRefKit's Skill-execution runtime (`python -m xrefkit skill run`,
`workitem`, `artifact`, `concern`, `phase`, `verify`, `close`) for client-side
execution.

The MCP server does not execute `xrefkit`. Run it in the client-side target
repository:

```powershell
python -m xrefkit skill run --meta <path-to-meta.md> --task "<task>" --json
```
"""


def _client_obligations() -> list[ClientObligation]:
    return [
        ClientObligation(
            id="startup.first_call",
            level="must",
            applies_when="xrefkit.mcp_configured",
            statement="Call get_startup_context before task-specific routing.",
            enforcement_owner="server",
            verification=(
                "get_document_by_xid, get_skill, get_skill_requirements, "
                "expand_knowledge, get_knowledge_summary, "
                "build_knowledge_context, and list_skills with "
                "include_content=true reject the call for any MCP session "
                "that has not first called get_startup_context"
            ),
        ),
        ClientObligation(
            id="prompt_flow.initialize_and_reconcile",
            level="must",
            applies_when="one user prompt spans a generic workflow and one or more Skill Runs",
            statement=(
                "Initialize one Prompt Flow with flow_id and root_run_id, preserve parent_run_id, "
                "work_item_id, and node_id for child runs, and reconcile child closure before parent closure. "
                "Use explicit status projection only after deterministic correlation and terminal-status checks; "
                "do not execute work or recovery through reconciliation."
            ),
            enforcement_owner="client",
            verification=(
                "Prompt Flow run records contain the correlation fields, child_run.started and flow.reconciled "
                "events, and parent closure is attempted only after every work item is done or escalated"
            ),
        ),
        ClientObligation(
            id="tools.no_download_before_skill_selection",
            level="must",
            applies_when="client considers fetching client-side tool distribution",
            statement=(
                "Do not fetch client-tool manifests, files, bundles, or pip "
                "packages before selecting a Skill via get_skill or "
                "get_skill_requirements."
            ),
            enforcement_owner="server",
            verification=(
                "get_client_tool_manifest, get_client_tool_file, "
                "get_client_tool_bundle, and get_client_tool_pip_package reject "
                "the call for any MCP session that has not first called "
                "get_skill or get_skill_requirements"
            ),
        ),
        ClientObligation(
            id="core_runtime.fetch_immediately",
            level="must",
            applies_when="xrefkit.mcp_configured",
            statement=(
                "Fetch and materialize the xrefkit runtime from "
                "core_runtime_distribution right after get_startup_context, "
                "unconditionally, rather than deferring it the way per-Skill "
                "client-tool distribution is deferred. Skill execution "
                "requires python -m xrefkit skill run immediately once a Skill is "
                "selected, so the runtime must already be available by then."
            ),
            enforcement_owner="client",
            verification=(
                "python -m xrefkit succeeds in the client-side target repository, "
                "or xrefkit/ files materialized from get_xrefkit_runtime_bundle are "
                "present, before the client's first get_skill call in the "
                "session"
            ),
        ),
        ClientObligation(
            id="content.mcp_only",
            level="must",
            applies_when="access_policy.mode == mcp_only",
            statement="Do not read XRefKit governance Markdown from a local filesystem checkout.",
            enforcement_owner="client",
            verification="XID-linked governance content is obtained through get_document_by_xid or get_skill",
        ),
        ClientObligation(
            id="links.resolve_by_xid",
            level="must",
            applies_when="transferred content contains links entries",
            statement="Resolve needed Markdown links by XID through get_document_by_xid.",
            enforcement_owner="client",
            verification="link resolver uses resolver_tool and resolver_argument from link metadata",
        ),
        ClientObligation(
            id="startup.log_decision_xids",
            level="must",
            applies_when="startup context is materialized by the client",
            statement="Record the startup XIDs used for client-side routing, policy, or context-injection decisions in a client-side audit log.",
            enforcement_owner="client",
            verification="client startup audit log contains repository_fingerprint, load_order_xids, startup_contract_pack_source_xids, reference_xids, and client_decision_xids",
        ),
        ClientObligation(
            id="tools.materialize_from_mcp",
            level="must",
            applies_when="client executes XRefKit-distributed tools",
            statement="Fetch, materialize or install, and version-check client-side tools from XRefKit MCP before execution.",
            enforcement_owner="client",
            verification="check_client_tool_versions passes for the installed client-tool package versions",
        ),
        ClientObligation(
            id="tools.client_side_execution",
            level="must",
            applies_when="client runs XRefKit-distributed tools",
            statement="Run distributed tools only in the client execution environment; the MCP server does not execute them.",
            enforcement_owner="client",
            verification="tool execution occurs outside the XRefKit MCP server process",
        ),
        ClientObligation(
            id="context.no_duplicate_xid_body_per_session",
            level="must",
            applies_when="assembling model context",
            statement="Within a single client session, the client MUST NOT inject more than one full document body for the same repository_fingerprint, xid, and content_hash into the active model context. If the same XID version is needed again, the client MUST reference the existing session context entry by XID and content_hash instead of repeating the body.",
            enforcement_owner="client",
            verification="Prompt assembly maintains a session-visible XID index and records injected_xids, reused_xids, content_hash values, visibility status, and reuse reasons for each model turn.",
        ),
    ]


def _prompt_flow_protocol() -> dict[str, object]:
    return {
        "version": "1",
        "activation": "one user prompt spans a generic workflow and one or more Skill Runs",
        "initialization": {
            "owner": "main_ai_orchestrator",
            "fields": ["flow_id", "root_run_id"],
            "rule": "create one Prompt Flow root for the prompt and preserve its identity across related runs",
        },
        "child_delegation": {
            "owner": "main_ai_orchestrator",
            "required_fields": ["flow_id", "root_run_id", "parent_run_id", "work_item_id", "node_id"],
            "rule": "launch a child Skill only for a declared parent work item",
        },
        "reconciliation": {
            "default": "report_only",
            "projection_operation": "xrefkit workflow reconcile --apply-child-status",
            "allowed_child_statuses": ["done", "escalated"],
            "preconditions": [
                "flow_id matches",
                "parent_run_id matches",
                "work_item_id exists",
                "child Closure Gate is terminal",
            ],
            "does_not_do": ["execute_work", "execute_recovery", "perform_quality_review", "close_parent"],
        },
        "uncertainty": {
            "when": ["semantic routing is uncertain", "work-item mapping is uncertain", "correlation is invalid"],
            "action": "do_not_project_status_and_request_human_confirmation",
        },
        "completion": {
            "parent_work_item_statuses": ["done", "escalated"],
            "required_gates": ["verify", "close"],
        },
        "audit_events": ["child_run.started", "flow.child_status_applied", "flow.reconciled"],
    }


def _semantic_routing_references() -> list[dict[str, object]]:
    return [
        {
            "id": "skills",
            "purpose": "semantic Skill routing from user intent before procedure load",
            "summary_tool": "list_skills",
            "summary_arguments": {"include_content": False},
            "rank_tool": "rank_skills_for_purpose",
            "materialize_tool": "get_skill",
            "materialize_argument": "skill_id",
            "body_mode": "lazy",
        },
        {
            "id": "knowledge",
            "purpose": "domain-knowledge search after a task or Skill needs evidence",
            "summary_tool": "search_knowledge_catalog",
            "summary_arguments": {"limit": 10},
            "materialize_tool": "expand_knowledge",
            "materialize_argument": "xid",
            "body_mode": "lazy",
        },
        {
            "id": "tool_contracts",
            "purpose": "tool capability lookup when a task needs exact tool boundaries",
            "summary_tool": "list_tool_contracts",
            "body_mode": "metadata_only",
        },
    ]


def _client_tool_download_policy(entry: SkillCatalogEntry) -> dict[str, object]:
    required_client_tools = [
        item
        for item in entry.required_tools
        if item.get("execution_location") == "client" or item.get("name")
    ]
    return {
        "required": bool(required_client_tools),
        "required_client_tools": required_client_tools,
        "download_when": "after this Skill is selected for use and before executing its client-side required_tools",
        "do_not_download_at_startup": True,
        "manifest_tool": "get_client_tool_manifest",
        "package_tool": "get_client_tool_pip_package",
        "file_tool": "get_client_tool_file",
        "bundle_tool": "get_client_tool_bundle",
        "version_check_tool": "check_client_tool_versions",
    }


def _skill_context_size(
    meta_content: str,
    skill_content: str,
    outputs: list[str],
    closure: ClosureContract,
) -> dict[str, object]:
    meta_size = _text_size(meta_content)
    skill_size = _text_size(skill_content)
    read_size = _sum_text_sizes([meta_size, skill_size])
    write_contract_size = _text_size(
        "\n".join(
            [
                *outputs,
                *closure.closure_conditions,
                *closure.exit_enum,
                closure.handoff_policy,
                closure.worklist_policy,
            ]
        )
    )
    return {
        "unit": "estimated_tokens",
        "estimator": "ceil(characters / 4)",
        "model_tokenizer": None,
        "read": read_size,
        "write_contract": write_contract_size,
        "write_contract_note": "Declared output and closure contract size only; actual generated output tokens are runtime-dependent.",
        "meta": meta_size,
        "skill": skill_size,
        "total": read_size,
    }


def _text_size(value: str) -> dict[str, int]:
    characters = len(value)
    return {
        "bytes_utf8": len(value.encode("utf-8")),
        "characters": characters,
        "estimated_tokens": (characters + 3) // 4,
    }


def _sum_text_sizes(sizes: list[dict[str, int]]) -> dict[str, int]:
    return {
        "bytes_utf8": sum(size["bytes_utf8"] for size in sizes),
        "characters": sum(size["characters"] for size in sizes),
        "estimated_tokens": sum(size["estimated_tokens"] for size in sizes),
    }


def _workflow_protocol() -> dict[str, object]:
    return {
        "source": "xrefkit.mcp",
        "decision_trace_protocol": {
            "status": "standard",
            "contract_xid": "22164A51A745",
            "guide_xid": "88830262A85D",
            "execution_location": "client_side_xrefkit_runtime",
            "required_for": ["skill_run", "instruction_backed_workflow_run"],
            "human_gate": "adoption_rejection_readoption_return_execution",
            "default_state_until_human_evaluation": "provisional",
        },
        "routing": {
            "selection_basis": [
                "user intent",
                "startup load_order",
                "workflow catalog",
                "Skill catalog",
                "XID-linked evidence resolved through get_document_by_xid",
            ],
            "workflow_selection": "deterministic catalog metadata once selected; semantic selection may be performed by the client before execution",
            "skill_selection": "route by catalog metadata, then fetch selected Skill through get_skill",
        },
        "phase_order": [
            "startup",
            "planning",
            "execution",
            "check",
            "quality",
            "closure",
            "handoff",
        ],
        "role_ownership": {
            "executor": "Skill-specific execution role",
            "checker": "protocol-owned deterministic run-record verification",
            "quality_reviewer": "protocol-owned quality review role separate from executor",
            "handoff_owner": "protocol-owned handoff role",
        },
        "deterministic_checks": [
            "load_order is returned by get_startup_context",
            "XID links are resolved only through get_document_by_xid",
            "check phase is advanced by deterministic xrefkit skill verify semantics",
            "content identity is content_hash; no duplicate document version field is emitted",
        ],
        "non_deterministic_decisions": [
            "semantic workflow or Skill routing from user intent",
            "quality judgment after deterministic checks pass",
            "task-specific evidence sufficiency judgment",
        ],
    }


def _context_injection_policy() -> dict[str, object]:
    return {
        "model_context_format": "plain_text",
        "model_context_source": "startup_contract_pack.body",
        "do_not_inject_raw_startup_json": True,
        "default_document_body_mode": "lazy",
        "default_nonstartup_document_body_mode": "lazy",
        "startup_reference_prompt_mode": "required_startup_contract_pack",
        "startup_contract_pack_visible_by_default": True,
        "startup_reference_body_visible_by_default": False,
        "materialize_does_not_imply_prompt_injection": True,
        "body_injection_unit": "xid_document",
        "body_visible_by_default": False,
        "metadata_visible_by_default": [
            "xid",
            "title",
            "summary",
            "layer",
            "required_at_init",
            "content_hash",
            "links",
            "cache_status",
            "client_cache_status",
        ],
        "inject_body_when": [
            "the active task explicitly requires that XID",
            "the selected workflow or Skill declares that XID as required evidence",
            "the model requests a linked XID that is needed to resolve a concrete uncertainty",
            "a closure, safety, or verification check depends on the exact wording of that XID",
            "the user explicitly asks to inspect, quote, edit, or verify that document",
        ],
        "do_not_inject_body_when": [
            "the XID is only present as a related link",
            "the summary is sufficient for routing",
            "the document is cached only for future resolution",
            "the document belongs to a lower-layer context that is not active for the current task",
        ],
    }


def _session_context_deduplication() -> dict[str, object]:
    return {
        "scope": "single_client_session",
        "dedupe_key": [
            "repository_fingerprint",
            "xid",
            "content_hash",
        ],
        "active_model_context_cardinality": "at_most_one_body_per_dedupe_key",
        "materialize_does_not_imply_duplicate_injection": True,
        "on_repeated_xid_same_hash": "reference_existing_session_context_entry",
        "on_repeated_xid_different_hash": "treat_as_version_change_and_replace_or_escalate",
        "reinject_body_only_when": [
            "the previous body is no longer visible in the active model context",
            "the content_hash changed and the new version is selected",
            "the client intentionally rebuilds the active context after compaction",
        ],
        "trace_required": True,
    }


def _repository_zones(ownership: Ownership | None) -> dict[str, object]:
    if ownership is None:
        return {
            "ownership_enabled": False,
            "ownership_hash": None,
            "zone_ids": [],
            "local_packs_declared": False,
            "catalog_roots_are_zone_aware": False,
        }
    zone_ids = [zone.id for zone in ownership.zones]
    return {
        "ownership_enabled": True,
        "ownership_hash": ownership.content_hash,
        "zone_ids": zone_ids,
        "local_packs_declared": any(zone.id == "local-packs" for zone in ownership.zones),
        "catalog_roots_are_zone_aware": True,
    }


def _client_tool_files(root: Path) -> list[ClientToolFile]:
    ownership = load_ownership(root)
    if ownership is not None:
        errors = validate_ownership(root, ownership)
        if errors:
            raise ValueError("invalid ownership.yaml: " + "; ".join(errors))
    tools_root = root / "tools"
    paths: list[Path] = []
    support_paths: list[Path] = []
    if tools_root.exists():
        paths.extend(sorted(tools_root.glob("**/*.py")))
        support_paths.extend(
            path
            for path in sorted((tools_root / "profiles").glob("**/*"))
            if path.is_file()
        )
        readme = tools_root / "README.md"
        if readme.exists():
            support_paths.append(readme)

    # Some Skills embed their own client-side scripts directly under
    # skills/<id>/... (e.g. scripts/, references/) instead of tools/, and
    # their SKILL.md procedures instruct running them by relative path.
    # Without this, a remote client with no local checkout has no way to
    # obtain those scripts even though tools/ distribution is otherwise
    # unconditionally available once any Skill is selected.
    skills_root = root / "skills"
    if skills_root.exists():
        paths.extend(
            sorted(
                path
                for path in skills_root.glob("**/*.py")
                if "__pycache__" not in path.parts
            )
        )
    packs_root = root / "packs"
    if ownership is not None and packs_root.exists():
        paths.extend(
            sorted(
                path
                for path in packs_root.glob("*/skills/**/*.py")
                if "__pycache__" not in path.parts
                and ownership.distribution_enabled(relative_to_repo(path, root))
            )
        )
        paths.extend(
            sorted(
                path
                for path in packs_root.glob("local/*/skills/**/*.py")
                if "__pycache__" not in path.parts
                and ownership.distribution_enabled(relative_to_repo(path, root))
            )
        )

    result: list[ClientToolFile] = []
    for path in [*paths, *support_paths]:
        rel = relative_to_repo(path, root)
        text = read_text(path)
        kind = _client_tool_kind(path)
        result.append(
            ClientToolFile(
                path=rel,
                kind=kind,
                content=text,
                content_hash=stable_hash(text),
                size_bytes=len(text.encode("utf-8")),
                run_hint=f"python {rel}" if kind == "python" else None,
                imports=_python_imports(text) if kind == "python" else [],
                links=markdown_xid_link_targets(text),
            )
        )
    return result


def _client_tool_pip_package(root: Path) -> ClientToolPipPackage:
    # Scoped to tools/ only: these are the files declared installable via
    # [tool.setuptools.packages.find]. Skill-embedded scripts under skills/
    # are invoked by relative file path per their SKILL.md, not imported as
    # a package, and skills/ has no __init__.py chain making it one; bundling
    # them here would silently vanish on `pip install` since setuptools would
    # never install undiscovered loose files into site-packages. They remain
    # available via get_client_tool_file/get_client_tool_bundle instead.
    files = [file for file in _client_tool_files(root) if file.path.startswith("tools/")]
    package_root = f"xrefkit-client-tools-{CLIENT_TOOL_PACKAGE_VERSION}"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        _zip_writestr(
            archive,
            f"{package_root}/pyproject.toml",
            _client_tools_pyproject(files),
        )
        _zip_writestr(
            archive,
            f"{package_root}/README.md",
            _client_tools_readme(),
        )
        _zip_writestr(
            archive,
            f"{package_root}/tools/__init__.py",
            '"""Client-side XRefKit deterministic tools."""\n',
        )
        for file in files:
            _zip_writestr(archive, f"{package_root}/{file.path}", file.content)
    content = buffer.getvalue()
    encoded = base64.b64encode(content).decode("ascii")
    return ClientToolPipPackage(
        filename=f"xrefkit-client-tools-{CLIENT_TOOL_PACKAGE_VERSION}.zip",
        package_id="xrefkit-client-tools",
        version=CLIENT_TOOL_PACKAGE_VERSION,
        package_format="zip-sdist",
        install_command=f"python -m pip install xrefkit-client-tools-{CLIENT_TOOL_PACKAGE_VERSION}.zip",
        content_base64=encoded,
        content_hash=hashlib_sha256_bytes(content),
        size_bytes=len(content),
        warnings=[
            "This package installs a top-level tools package to preserve existing XRefKit imports such as tools.error_policy_locator.",
            "Install in a project virtual environment to avoid conflicts with any unrelated package named tools.",
            "The package contains Python tools only; C# tools/structure_graph "
            "is not bundled. Install it as the NuGet dotnet tool "
            "XRefKit.StructureGraph (command dotnet-xrefkit-graph), build it "
            "from source, or receive precomputed graph JSON; see "
            "docs/guides/078_structure_graph_build_guide.md (resolve via "
            "get_document_by_xid with xid 8B3E5D0A94C7).",
            "The MCP server only distributes the package; tool execution is client-side.",
            "Skill-embedded scripts under skills/**/*.py are not included in this "
            "package. Fetch them with get_client_tool_file or "
            "get_client_tool_bundle and run them by their returned relative "
            "path instead.",
        ],
    )


def _client_tools_pyproject(files: list[ClientToolFile]) -> str:
    scripts: list[str] = []
    for file in files:
        if file.kind != "python" or "def main" not in file.content:
            continue
        module = file.path.removesuffix(".py").replace("/", ".")
        script_name = "xrefkit-" + Path(file.path).stem.replace("_", "-")
        scripts.append(f'{script_name} = "{module}:main"')
    scripts_block = "\n".join(sorted(scripts))
    return f"""[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "xrefkit-client-tools"
version = "{CLIENT_TOOL_PACKAGE_VERSION}"
description = "Client-side deterministic Python tools distributed from XRefKit MCP"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []

[tool.setuptools.packages.find]
include = ["tools*"]

[project.scripts]
{scripts_block}
"""


def _client_tools_readme() -> str:
    return """# XRefKit Client Tools

This package is generated by XRefKit MCP and installs the Python files from
`tools/` for client-side execution.

The MCP server does not execute these tools. Run them in the client-side target
repository where the analyzed source files exist.

Examples:

```powershell
python -m tools.cs_scope_probe --target .
xrefkit-cs-scope-probe --target .
```

Some tools require external programs such as git, dotnet, npm, or precomputed
`tools/structure_graph` output.
"""


def _zip_writestr(archive: zipfile.ZipFile, name: str, content: str) -> None:
    # Fixed timestamp keeps rebuilt package bytes identical for identical
    # inputs, so a sha256 handed out earlier (for example in an MCP response
    # pointing at the HTTP /dist endpoint) still matches the artifact built
    # at download time.
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, content)


def hashlib_sha256_bytes(content: bytes) -> str:
    import hashlib

    return hashlib.sha256(content).hexdigest()


def _client_tool_kind(path: Path) -> str:
    if path.suffix == ".py":
        return "python"
    if path.name.lower() == "readme.md":
        return "documentation"
    return "support"


def _python_imports(text: str) -> list[str]:
    imports: list[str] = []
    for match in IMPORT_RE.finditer(text):
        module = match.group(1)
        if module not in imports:
            imports.append(module)
    return imports


def _runtime_role_contract() -> RuntimeRoleContract:
    return RuntimeRoleContract(
        roles={
            "executor": "advances the execution phase and performs assigned work items",
            "checker": "advances deterministic check/progression verification and must differ from executor",
            "quality_reviewer": "advances quality acceptance for standard/heavy work and must differ from executor",
            "handoff_owner": "advances explicit handoff phase and unresolved-item transfer",
        },
        phases=["startup", "planning", "execution", "check", "quality", "closure", "handoff"],
        statuses=["pending", "in_progress", "done", "blocked", "unknown", "escalated"],
        invariants=[
            "Skill execution starts through xrefkit skill run before opening SKILL.md",
            "execution/check/quality roles are separated from the executor role",
            "check is deterministic progression verification via xrefkit skill verify",
            "quality is a separate acceptance axis for standard/heavy work",
            "unknowns must resolve before closure; risks must resolve or escalate",
            "closure requires work items plus output and evidence artifacts",
            "workflow steps transition through gates, not through bare model judgment",
        ],
        required_commands=[
            "python -m xrefkit skill run --meta <path-to-meta.md> --task \"<task>\" --json",
            "python -m xrefkit skill workitem --log <run-log> --item <id> --status <status> --role <assigned-role>",
            "python -m xrefkit skill artifact --log <run-log> --artifact <id> --kind <kind> --target <target> --status <status> --role <assigned-role>",
            "python -m xrefkit skill concern --log <run-log> --concern <id> --kind <unknown|risk|judgment> --status <status> --role <assigned-role>",
            "python -m xrefkit skill verify --log <run-log>",
            "python -m xrefkit skill close --log <run-log>",
        ],
        source_xids=["B7A2C94F0E61", "4C7E9A2B1D63"],
    )


def _missing_skill_fields(meta: dict[str, object], has_skill_doc: bool) -> list[str]:
    required = [
        "skill_id",
        "summary",
        "maturity",
        "input",
        "output",
    ]
    missing = [field for field in required if not meta.get(field)]
    for field in ["intent", "target_artifacts", "applies_when", "not_for", "required_tools"]:
        if not meta.get(field):
            missing.append(field)
    if not has_skill_doc:
        missing.append("skill_doc")
    return missing


def _derive_intent(meta: dict[str, object]) -> list[str]:
    explicit = scalar_list(meta, "intent")
    if explicit:
        return explicit
    tags = scalar_list(meta, "tags")
    use_when = str(meta.get("use_when") or "")
    values = [tag for tag in tags if tag in {"review", "design", "routing", "quality"}]
    if "review" in use_when.lower() and "review" not in values:
        values.append("review")
    if "route" in use_when.lower() and "routing" not in values:
        values.append("routing")
    return values


def _derive_target_artifacts(meta: dict[str, object]) -> list[str]:
    explicit = scalar_list(meta, "target_artifacts")
    if explicit:
        return explicit
    haystack = " ".join(
        [str(meta.get("use_when") or ""), str(meta.get("input") or ""), *scalar_list(meta, "tags")]
    ).lower()
    targets: list[str] = []
    for needle, target in [
        ("c#", "csharp_source"),
        ("dotnet", "dotnet_source"),
        ("ddl", "ddl"),
        ("api", "api_contract"),
        ("screen", "ui_spec"),
        ("design", "design_artifact"),
        ("code", "source_code"),
    ]:
        if needle in haystack and target not in targets:
            targets.append(target)
    return targets


def _split_constraints(value: str) -> list[str]:
    if not value:
        return []
    pieces = re.split(r";|,|—|--", value)
    return [piece.strip() for piece in pieces if piece.strip()]


def _knowledge_req(ref: str) -> dict[str, object]:
    xid_match = re.search(r"#xid-([A-Za-z0-9]+)", ref)
    return {
        "xid": xid_match.group(1) if xid_match else ref,
        "version": 1,
        "required_when": "declared by Skill meta knowledge_refs",
        "detail_policy": "expand_on_demand",
    }


def _bind_knowledge_req(slot: dict) -> dict[str, object]:
    # A pinned (bind) knowledge_slot is a required-knowledge XID; query slots are
    # resolved dynamically via resolve_skill_knowledge instead.
    return {
        "xid": str(slot.get("bind")),
        "version": 1,
        "required_when": "declared by Skill meta knowledge_slot bind",
        "detail_policy": "expand_on_demand",
    }


def _required_tool(name: str) -> dict[str, object]:
    if name.startswith("xref."):
        return {
            "tool_id": name,
            "required_when": "declared by Skill meta required_tools",
        }
    return {
        "name": name,
        "execution_location": "client",
        "required_when": "declared by Skill meta required_tools",
    }


def _section_bullets(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    result: list[str] = []
    for line in lines:
        if line.startswith("## "):
            in_section = line.strip("# ").strip().lower() == heading.lower()
            continue
        if in_section and line.startswith("- "):
            result.append(line[2:].strip())
    return result


def _nested_value(meta: dict[str, object], _parent: str, _key: str) -> str | None:
    # Current XRefKit meta files use prose-like nested bullets. They are kept
    # opaque by the lightweight parser, so return None until a structured field
    # exists in the source repository.
    return None


def _yaml_top_scalars(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.splitlines():
        if raw.startswith(" ") or not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.+?)\s*$", raw)
        if match and not match.group(2).startswith("["):
            result[match.group(1)] = match.group(2).strip().strip('"')
    return result


def _yaml_nested_scalar(text: str, parent: str, key: str) -> str | None:
    in_parent = False
    for raw in text.splitlines():
        if re.match(rf"^{re.escape(parent)}:\s*$", raw):
            in_parent = True
            continue
        if in_parent and raw and not raw.startswith(" "):
            return None
        if in_parent:
            match = re.match(rf"^\s+{re.escape(key)}:\s*(.+?)\s*$", raw)
            if match:
                return match.group(1).strip().strip('"')
    return None


def _yaml_top_list(text: str, key: str) -> list[str]:
    in_list = False
    result: list[str] = []
    for raw in text.splitlines():
        if re.match(rf"^{re.escape(key)}:\s*$", raw):
            in_list = True
            continue
        if in_list and raw and not raw.startswith(" "):
            break
        if in_list:
            match = re.match(r"^\s+-\s+(.+?)\s*$", raw)
            if match:
                result.append(match.group(1).strip().strip('"'))
    return result


def _yaml_map_keys(text: str, key: str) -> list[str]:
    in_map = False
    result: list[str] = []
    for raw in text.splitlines():
        if re.match(rf"^{re.escape(key)}:\s*$", raw):
            in_map = True
            continue
        if in_map and raw and not raw.startswith(" "):
            break
        if in_map:
            match = re.match(r"^\s{2}([A-Za-z0-9_]+):\s*$", raw)
            if match:
                result.append(match.group(1))
    return result


def _yaml_values_for_key(text: str, key: str) -> list[str]:
    values: list[str] = []
    for raw in text.splitlines():
        match = re.match(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", raw)
        if match:
            values.append(match.group(1).strip().strip('"'))
    return list(dict.fromkeys(values))


def _rank_entries(query: str, entries: list[KnowledgeCatalogEntry]) -> list[KnowledgeCatalogEntry]:
    query_tokens = _tokens(query)
    return sorted(
        entries,
        key=lambda entry: (
            len(query_tokens & _tokens(" ".join([entry.title, entry.summary, entry.domain]))),
            entry.title,
        ),
        reverse=True,
    )


def _tokens(value: str) -> set[str]:
    normalized = (
        value.lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("c#", "csharp")
        .replace(".net", "dotnet")
        .replace("non-roslyn", "roslyn")
    )
    tokens = {match.group(0).lower() for match in TOKEN_RE.finditer(normalized)}
    for alias, expanded in ROUTING_SYNONYMS.items():
        if alias.lower() in normalized:
            tokens.update(expanded)
    if "roslyn" in tokens:
        tokens.add("diagnostics")
    if "csharp" in tokens:
        tokens.add("c#")
    if "script" in tokens:
        tokens.add("automation")
    if "tool" in tokens:
        tokens.add("tooling")
    if "traceability" in tokens:
        tokens.add("trace")
    return tokens


def _knowledge_slot_text(slot: dict) -> str:
    return " ".join(str(value) for value in slot.values() if value is not None)


def _routing_categories(tokens: set[str]) -> dict[str, set[str]]:
    effective_tokens = tokens - STOP_TOKENS
    categories: dict[str, set[str]] = {}
    for category, terms in ROUTING_CATEGORY_TERMS.items():
        matched = effective_tokens & terms
        if matched:
            categories[category] = matched
    return categories


def _skill_values_by_category(skill: SkillCatalogEntry) -> dict[str, list[str]]:
    closure_values = [
        *skill.closure_contract.closure_conditions,
        skill.closure_contract.handoff_policy,
        skill.closure_contract.worklist_policy,
    ]
    knowledge_slot_values = [_knowledge_slot_text(slot) for slot in skill.knowledge_slots]
    tool_values = [
        " ".join(str(value) for value in tool.values() if value is not None)
        for tool in skill.required_tools
    ]
    return {
        "activity": [
            skill.skill_id,
            skill.summary,
            skill.capability,
            skill.tuning,
            skill.responsibility,
            *skill.intent,
            *skill.applies_when,
        ],
        "artifact": [
            skill.skill_id,
            skill.summary,
            *skill.target_artifacts,
            *skill.inputs,
            *skill.outputs,
        ],
        "domain": [
            skill.skill_id,
            skill.summary,
            skill.tuning,
            skill.responsibility,
            *skill.inputs,
            *skill.outputs,
            *knowledge_slot_values,
        ],
        "phase": [
            skill.summary,
            *skill.applies_when,
            *skill.inputs,
            *skill.outputs,
            *closure_values,
        ],
        "evidence_trace": [
            skill.summary,
            *skill.inputs,
            *skill.outputs,
            *closure_values,
            *knowledge_slot_values,
        ],
        "tool_runtime": [
            skill.skill_id,
            skill.summary,
            *skill.inputs,
            *skill.outputs,
            *tool_values,
            *knowledge_slot_values,
        ],
    }


def _mcp_content_resolution_policy() -> dict[str, str]:
    return {
        "mode": "mcp_only",
        "xid_document_tool": "get_document_by_xid",
        "skill_body_tool": "get_skill",
        "path_like_fields": "server_side_identity_or_diagnostic_only",
        "client_filesystem_resolution": "forbidden",
    }


def _matched_routing_categories(
    skill: SkillCatalogEntry, query_categories: dict[str, set[str]]
) -> dict[str, list[str]]:
    values_by_category = _skill_values_by_category(skill)
    matched_categories: dict[str, list[str]] = {}
    for category, query_terms in query_categories.items():
        values = values_by_category.get(category, [])
        matches: list[str] = []
        for value in values:
            value_tokens = _tokens(value) - STOP_TOKENS
            matched_terms = sorted(query_terms & value_tokens)
            if matched_terms:
                matches.append(f"{value} [{', '.join(matched_terms)}]")
        if matches:
            matched_categories[category] = matches[:5]
    return matched_categories


def _has_required_category_coverage(
    query_categories: dict[str, set[str]], matched_categories: dict[str, list[str]]
) -> bool:
    for category in ["domain", "tool_runtime", "evidence_trace"]:
        if category in query_categories and category not in matched_categories:
            return False
    return True


def _category_coverage_multiplier(
    query_categories: dict[str, set[str]], matched_categories: dict[str, list[str]]
) -> float:
    multiplier = 1.0
    for category, penalty in [
        ("domain", 0.55),
        ("tool_runtime", 0.45),
        ("evidence_trace", 0.7),
    ]:
        if category in query_categories and category not in matched_categories:
            multiplier *= penalty
    return multiplier


def _matched_values(
    query_tokens: set[str], values: list[str], use_stop_words: bool = False
) -> list[str]:
    matched: list[str] = []
    for value in values:
        value_tokens = _tokens(value)
        if use_stop_words:
            value_tokens = value_tokens - STOP_TOKENS
            effective_query = query_tokens - STOP_TOKENS
        else:
            effective_query = query_tokens
        if effective_query & value_tokens:
            matched.append(value)
    return matched


def _overlap_count(query_tokens: set[str], values: list[str]) -> int:
    value_tokens = set().union(*(_tokens(value) for value in values)) if values else set()
    return len((query_tokens - STOP_TOKENS) & (value_tokens - STOP_TOKENS))
