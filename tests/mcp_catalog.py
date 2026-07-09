from __future__ import annotations

import tempfile
import unittest
import base64
import hashlib
import io
import zipfile
from pathlib import Path

from xrefkit.mcp.catalog import (
    CACHE_MAX_VERSION_PAYLOAD_RATIO,
    XRefCatalog,
    _conditional_document_response,
    _document_cache_policy,
)
from xrefkit.mcp.schemas import ToolContract, XRefDocument


REPOSITORY_FINGERPRINT = "a" * 32


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        write(
            self.repo / "knowledge" / "organization" / "rules.md",
            """<!-- xid: ABC123 -->
<a id="xid-ABC123"></a>

# Context Rules

Use this when external input is loaded.
""",
        )
        write(
            self.repo / "skills" / "sample" / "meta.md",
            """<!-- xid: SKILLMETA -->
# Skill Meta: sample_review

- skill_id: `sample_review`
- summary: review sample source
- use_when: user asks to review sample code
- intent:
  - review explicit sample source behavior
- applies_when:
  - sample source needs catalog-driven review
- target_artifacts:
  - sample source findings
- not_for:
  - formatting-only edits
- required_tools:
  - xrefkit skill run
  - xrefkit skill verify
- input: source path
- output: findings
- maturity: `trial`
- constraints: do not format code
- tags: `review`, `quality`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/quality/sample.md#xid-CAP1`
- knowledge_refs:
  - `../../knowledge/organization/rules.md#xid-ABC123`
""",
        )
        write(
            self.repo / "skills" / "sample" / "SKILL.md",
            """<!-- xid: SKILLDOC -->
# Skill: sample_review

Use [Context Rules](../../knowledge/organization/rules.md#xid-ABC123).

## Closure

- return findings
""",
        )
        for rel_path, xid, title in [
            ("agent/000_agent_entry.md", "0B5C58B5E5B2", "Agent Entry"),
            ("docs/core/models/017_base_and_xref_layering.md", "5A1C8E4D2F90", "Base Control and Xref Routing Layers"),
            ("docs/core/contracts/011_startup_xref_routing.md", "6C0B62D6366A", "Startup Xref Routing Policy"),
            ("docs/core/contracts/016_uncertainty_protocol.md", "8A666C1FD121", "Uncertainty Protocol"),
            ("docs/core/contracts/053_context_direction_security_guard.md", "A7F3C92D4E11", "Context Direction Security Guard"),
            ("docs/core/contracts/015_shared_memory_operations.md", "4A423E72D2ED", "Shared Memory Operations"),
        ]:
            detail = "\n".join(
                "Detailed startup governance content used to exercise conditional retrieval."
                for _ in range(20)
            )
            write(
                self.repo / rel_path,
                f"""<!-- xid: {xid} -->
<a id="xid-{xid}"></a>

# {title}

Required startup reference. See [Uncertainty](016_uncertainty_protocol.md#xid-8A666C1FD121).

{detail}
""",
            )
        write(
            self.repo / "flows" / "sample_workflow.yaml",
            """flow_id: FLOW-SAMPLE
name: sample_workflow
doc_xid: FLOWDOC
phase: normal
owner:
  primary: sample_group
runs_after:
  - FLOW-UPSTREAM
runs_before:
  - FLOW-DOWNSTREAM
entry: draft
steps:
  draft:
    capability: CAP-SAMPLE-001
    on:
      Go: COMPLETE
      _invalid_or_absent: ABORT
""",
        )
        write(
            self.repo / "tools" / "sample_tool.py",
            """from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ok", action="store_true")
    return 0 if parser.parse_args().ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
""",
        )
        write(
            self.repo / "tools" / "profiles" / "sample.editorconfig",
            "root = true\n",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_builds_read_only_catalog(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        self.assertTrue(catalog.catalog_version)
        self.assertEqual(len(catalog.knowledge), 1)
        self.assertEqual(len(catalog.skills), 1)
        self.assertEqual(
            catalog.skills[0].intent,
            ["review explicit sample source behavior"],
        )
        self.assertEqual(
            catalog.skills[0].applies_when,
            ["sample source needs catalog-driven review"],
        )
        self.assertEqual(catalog.skills[0].target_artifacts, ["sample source findings"])
        self.assertEqual(catalog.skills[0].not_for, ["formatting-only edits"])
        self.assertEqual(
            catalog.skills[0].required_tools,
            [
                {
                    "name": "xrefkit skill run",
                    "execution_location": "client",
                    "required_when": "declared by Skill meta required_tools",
                },
                {
                    "name": "xrefkit skill verify",
                    "execution_location": "client",
                    "required_when": "declared by Skill meta required_tools",
                },
            ],
        )
        self.assertTrue(all(tool.side_effects == "none" for tool in catalog.tools))
        self.assertTrue(
            all(tool.to_dict()["input_json_schema"]["type"] == "object" for tool in catalog.tools)
        )
        self.assertIn("Skill: sample_review", catalog.skills[0].skill_content)
        self.assertEqual(catalog.skills[0].skill_links[0]["xid"], "ABC123")
        self.assertEqual(catalog.skills[0].skill_links[0]["resolver_tool"], "get_document_by_xid")
        self.assertEqual(catalog.skills[0].context_size["unit"], "estimated_tokens")
        self.assertGreater(catalog.skills[0].context_size["meta"]["estimated_tokens"], 0)
        self.assertGreater(catalog.skills[0].context_size["skill"]["estimated_tokens"], 0)
        self.assertEqual(
            catalog.skills[0].context_size["total"]["estimated_tokens"],
            catalog.skills[0].context_size["meta"]["estimated_tokens"]
            + catalog.skills[0].context_size["skill"]["estimated_tokens"],
        )
        self.assertEqual(
            catalog.skills[0].context_size["read"],
            catalog.skills[0].context_size["total"],
        )
        self.assertGreater(
            catalog.skills[0].context_size["write_contract"]["estimated_tokens"],
            0,
        )
        self.assertIn("runtime-dependent", catalog.skills[0].context_size["write_contract_note"])
        self.assertEqual(
            catalog.get_repository_identity()["cache_namespace"],
            catalog.repository_fingerprint,
        )

    def test_pack_roots_require_ownership_metadata(self) -> None:
        write(
            self.repo / "packs" / "business-intake" / "knowledge" / "pack-rule.md",
            """<!-- xid: PACKRULE123 -->
<a id="xid-PACKRULE123"></a>

# Pack Rule

Pack-local rule.
""",
        )
        write(
            self.repo / "packs" / "business-intake" / "skills" / "pack_sample" / "meta.md",
            """# Skill Meta: pack_sample

- skill_id: `pack_sample`
- summary: pack sample
- skill_doc: `./SKILL.md`
- maturity: `trial`
""",
        )
        write(
            self.repo / "packs" / "business-intake" / "skills" / "pack_sample" / "SKILL.md",
            "# Pack Sample\n",
        )
        without_ownership = XRefCatalog.build(self.repo)

        self.assertNotIn("PACKRULE123", [entry.xid for entry in without_ownership.knowledge])
        self.assertNotIn("pack_sample", [entry.skill_id for entry in without_ownership.skills])

        write(
            self.repo / "ownership.yaml",
            """zones:
  - id: shared-packs
    owner: pack
    paths:
      - packs/*/
    catalog: true
    distribution: true
    base_sync: true
    shadowing: true
""",
        )

        with_ownership = XRefCatalog.build(self.repo)
        pack_knowledge = next(entry for entry in with_ownership.knowledge if entry.xid == "PACKRULE123")
        pack_skill = next(entry for entry in with_ownership.skills if entry.skill_id == "pack_sample")

        self.assertEqual("shared-packs", pack_knowledge.zone_metadata["zone"])
        self.assertEqual("business-intake", pack_skill.zone_metadata["pack_id"])
        self.assertTrue(with_ownership.get_startup_context()["repository_zones"]["ownership_enabled"])

    def test_get_document_by_xid_fails_closed_on_duplicate_xid(self) -> None:
        write(
            self.repo / "ownership.yaml",
            """zones:
  - id: shared-packs
    owner: pack
    paths:
      - packs/*/
    catalog: true
    distribution: true
    base_sync: true
    shadowing: true
""",
        )
        write(
            self.repo / "packs" / "business" / "knowledge" / "duplicate.md",
            """<!-- xid: ABC123 -->
<a id="xid-ABC123"></a>

# Duplicate

Duplicate body.
""",
        )
        catalog = XRefCatalog.build(self.repo)

        result = catalog.get_document_by_xid("ABC123")

        self.assertFalse(result["ok"])
        self.assertEqual("xid_conflict", result["error"])
        self.assertEqual(2, len(result["matches"]))
        self.assertEqual(
            sorted(["knowledge/organization/rules.md", "packs/business/knowledge/duplicate.md"]),
            sorted(match["path"] for match in result["matches"]),
        )

    def test_get_skill_fails_closed_on_duplicate_skill_id(self) -> None:
        write(
            self.repo / "ownership.yaml",
            """zones:
  - id: shared-packs
    owner: pack
    paths:
      - packs/*/
    catalog: true
    distribution: true
    base_sync: true
    shadowing: true
""",
        )
        write(
            self.repo / "packs" / "business" / "skills" / "sample_duplicate" / "meta.md",
            """# Skill Meta: sample duplicate

- skill_id: `sample_review`
- summary: duplicate sample
- skill_doc: `./SKILL.md`
- maturity: `trial`
""",
        )
        write(
            self.repo / "packs" / "business" / "skills" / "sample_duplicate" / "SKILL.md",
            "# Duplicate Skill\n",
        )
        catalog = XRefCatalog.build(self.repo)

        listed = [entry for entry in catalog.list_skills() if entry["skill_id"] == "sample_review"]

        self.assertEqual(2, len(listed))
        self.assertTrue(all(entry["zone_metadata"]["identity_conflict"] for entry in listed))
        with self.assertRaises(ValueError):
            catalog.get_skill("sample_review")

    def test_pack_skill_scripts_are_distributed_but_local_pack_scripts_are_not(self) -> None:
        write(
            self.repo / "ownership.yaml",
            """zones:
  - id: local-packs
    owner: local
    paths:
      - packs/local/
    catalog: true
    distribution: false
    base_sync: false
    shadowing: true
  - id: shared-packs
    owner: pack
    paths:
      - packs/*/
    catalog: true
    distribution: true
    base_sync: true
    shadowing: true
""",
        )
        write(
            self.repo / "packs" / "business" / "skills" / "pack_sample" / "scripts" / "shared_tool.py",
            "print('shared')\n",
        )
        write(
            self.repo / "packs" / "local" / "acme" / "skills" / "local_sample" / "scripts" / "local_tool.py",
            "print('local')\n",
        )
        catalog = XRefCatalog.build(self.repo)

        paths = [file["path"] for file in catalog.get_client_tool_bundle()["files"]]

        self.assertIn("packs/business/skills/pack_sample/scripts/shared_tool.py", paths)
        self.assertNotIn("packs/local/acme/skills/local_sample/scripts/local_tool.py", paths)

    def test_rank_skills_includes_pack_skill_when_ownership_exists(self) -> None:
        write(
            self.repo / "ownership.yaml",
            """zones:
  - id: shared-packs
    owner: pack
    paths:
      - packs/*/
    catalog: true
    distribution: true
    base_sync: true
    shadowing: true
""",
        )
        write(
            self.repo / "packs" / "business" / "skills" / "layout_zone" / "meta.md",
            """# Skill Meta: layout_zone

- skill_id: `layout_zone`
- summary: migrate repository layout zones and ownership packs
- applies_when:
  - repository layout zone migration
- skill_doc: `./SKILL.md`
- maturity: `trial`
""",
        )
        write(
            self.repo / "packs" / "business" / "skills" / "layout_zone" / "SKILL.md",
            "# Layout Zone\n",
        )
        catalog = XRefCatalog.build(self.repo)

        ranked = catalog.rank_skills_for_purpose("repository layout zone migration", limit=3)

        self.assertIn("layout_zone", [entry["skill_id"] for entry in ranked])

    def test_expands_knowledge_by_xid(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        expanded = catalog.expand_knowledge("ABC123")

        self.assertEqual(expanded["entry"]["title"], "Context Rules")
        self.assertIn("external input", expanded["content"])

    def test_external_domain_knowledge_root_is_available_by_xid_without_path_leak(self) -> None:
        external_root = self.repo.parent / "domain-store"
        write(
            external_root / "billing" / "api-naming.md",
            """<!-- xid: EXTDOMAIN01 -->
<a id="xid-EXTDOMAIN01"></a>

# Billing API Naming

Use invoice command names for billing operations.
""",
        )
        catalog = XRefCatalog.build(self.repo, [external_root])

        listed = catalog.list_knowledge_catalog()
        external_entry = next(entry for entry in listed if entry["xid"] == "EXTDOMAIN01")
        expanded = catalog.expand_knowledge("EXTDOMAIN01")
        document = catalog.get_document_by_xid("EXTDOMAIN01")

        self.assertEqual(external_entry["domain"], "billing")
        self.assertEqual(external_entry["zone_metadata"]["zone"], "external_domain_knowledge")
        self.assertNotIn("path", external_entry)
        self.assertNotIn(str(external_root), repr(listed))
        self.assertIn("invoice command names", expanded["content"])
        self.assertNotIn("path", expanded["entry"])
        self.assertNotIn(str(external_root), repr(expanded))
        self.assertIn("# Billing API Naming", document["content"])
        self.assertNotIn("path", document)
        self.assertNotIn(str(external_root), repr(document))

    def test_external_domain_knowledge_xid_conflict_fails_closed_without_external_path(self) -> None:
        external_root = self.repo.parent / "domain-store"
        write(
            external_root / "duplicate.md",
            """<!-- xid: ABC123 -->
<a id="xid-ABC123"></a>

# External Duplicate

Duplicate external body.
""",
        )
        catalog = XRefCatalog.build(self.repo, [external_root])

        result = catalog.get_document_by_xid("ABC123")

        self.assertFalse(result["ok"])
        self.assertEqual("xid_conflict", result["error"])
        self.assertEqual(2, len(result["matches"]))
        self.assertEqual(
            ["external_domain_knowledge", "repository"],
            sorted(match["source"] for match in result["matches"]),
        )
        external_match = next(
            match for match in result["matches"] if match["source"] == "external_domain_knowledge"
        )
        self.assertNotIn("path", external_match)
        self.assertNotIn(str(external_root), repr(result))

    def test_ranks_skills_without_selecting_one(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        result = catalog.rank_skills_for_purpose("review sample code", limit=1)[0]

        self.assertEqual(result["skill_id"], "sample_review")
        self.assertGreater(result["score"], 0)
        self.assertIs(result["execution_readiness"]["runnable"], True)
        self.assertEqual(
            result["closure_preview"]["exit_enum"],
            ["completed", "blocked", "needs_input"],
        )

    def test_get_skill_returns_transferred_skill_files_and_links(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        skill = catalog.get_skill("sample_review")

        self.assertIn("Skill Meta: sample_review", skill["meta_content"])
        self.assertIn("Skill: sample_review", skill["skill_content"])
        self.assertEqual(skill["skill_links"][0]["xid"], "ABC123")
        self.assertEqual(skill["skill_links"][0]["resolver_tool"], "get_document_by_xid")

    def test_get_skill_refreshes_skill_files_after_catalog_build(self) -> None:
        catalog = XRefCatalog.build(self.repo)
        meta_path = self.repo / "skills" / "sample" / "meta.md"
        skill_path = self.repo / "skills" / "sample" / "SKILL.md"
        meta_path.write_text(
            meta_path.read_text(encoding="utf-8").replace(
                "- summary: review sample source",
                "- summary: refreshed summary",
            ),
            encoding="utf-8",
        )
        skill_path.write_text(
            skill_path.read_text(encoding="utf-8").replace(
                "# Skill: sample_review",
                "# Skill: sample_review refreshed",
            ),
            encoding="utf-8",
        )

        skill = catalog.get_skill("sample_review")

        self.assertEqual(skill["summary"], "refreshed summary")
        self.assertIn("refreshed summary", skill["meta_content"])
        self.assertIn("# Skill: sample_review refreshed", skill["skill_content"])

    def test_cache_aware_skill_returns_conditional_xid_documents(self) -> None:
        catalog = XRefCatalog.build(self.repo)
        first = catalog.get_skill("sample_review", {})
        versions = {
            document["xid"]: document["content_hash"]
            for document in first["documents"]
            if document["cache_policy"]["cache_recommended"]
        }

        cached = catalog.get_skill("sample_review", versions)

        self.assertIsNone(cached["meta_content"])
        self.assertIsNone(cached["skill_content"])
        self.assertEqual(len(cached["documents"]), 2)
        for document in cached["documents"]:
            if document["xid"] in versions:
                self.assertEqual(document["cache_status"], "not_modified")
                self.assertNotIn("content", document)

    def test_list_skills_defaults_to_metadata_only(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        skill = catalog.list_skills()[0]

        self.assertIsNone(skill["meta_content"])
        self.assertIsNone(skill["skill_content"])
        self.assertTrue(skill["document_versions"])

    def test_list_skills_returns_bodies_only_when_requested(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        skill = catalog.list_skills(include_content=True)[0]

        self.assertIn("Skill: sample_review", skill["skill_content"])
        self.assertIn("skill_id", skill["meta_content"])

    def test_list_skills_can_exclude_document_bodies(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        skill = catalog.list_skills(include_content=False)[0]

        self.assertIsNone(skill["meta_content"])
        self.assertIsNone(skill["skill_content"])
        self.assertEqual(skill["context_size"]["unit"], "estimated_tokens")
        self.assertGreater(skill["context_size"]["total"]["estimated_tokens"], 0)
        self.assertEqual(skill["context_size"]["read"], skill["context_size"]["total"])
        self.assertGreater(skill["context_size"]["write_contract"]["estimated_tokens"], 0)
        self.assertEqual(
            {document["xid"] for document in skill["document_versions"]},
            {"SKILLMETA", "SKILLDOC"},
        )

    def test_surfaces_triad_preconditions_and_knowledge_slots(self) -> None:
        # Skill-centric consolidation (design 083/084): the catalog surfaces the
        # capability/tuning/responsibility triad and declared needs as an
        # additive superset. `responsibility` is the explicit field that
        # replaces role_responsibilities.executor.
        write(
            self.repo / "skills" / "triad_sample" / "meta.md",
            """<!-- xid: TRIADMETA -->
# Skill Meta: triad_sample

- skill_id: `triad_sample`
- summary: review with the new triad fields
- maturity: `trial`
- capability: software_development
- tuning: C#
- responsibility: quality check
- preconditions:
  - implemented code exists
  - design evidence exists
- skill_doc: `./SKILL.md`
""",
        )
        write(
            self.repo / "skills" / "triad_sample" / "SKILL.md",
            "<!-- xid: TRIADDOC -->\n# Skill: triad_sample\n",
        )

        catalog = XRefCatalog.build(self.repo)
        skill = next(
            entry for entry in catalog.list_skills() if entry["skill_id"] == "triad_sample"
        )

        self.assertEqual(skill["capability"], "software_development")
        self.assertEqual(skill["tuning"], "C#")
        self.assertEqual(skill["responsibility"], "quality check")
        self.assertIn("implemented code exists", skill["preconditions"])
        self.assertEqual(skill["knowledge_slots"], [])

        legacy = next(
            entry for entry in catalog.list_skills() if entry["skill_id"] == "sample_review"
        )
        self.assertEqual(legacy["capability"], "")
        self.assertEqual(legacy["knowledge_slots"], [])

    def test_resolve_skill_knowledge_resolves_slots(self) -> None:
        # Design 082 D3 / 084 M5: slots declare needs (query or pinned bind XID)
        # resolved dynamically over the base+local knowledge catalog.
        write(
            self.repo / "skills" / "slot_sample" / "meta.md",
            """<!-- xid: SLOTMETA -->
# Skill Meta: slot_sample

- skill_id: `slot_sample`
- summary: skill with knowledge slots
- maturity: `trial`
- capability: software_development
- responsibility: quality check
- knowledge_slots:
  - name=context; query=context rules external input; domain=organization; min=1; required
  - name=context_pin; bind=ABC123
- skill_doc: `./SKILL.md`
""",
        )
        write(
            self.repo / "skills" / "slot_sample" / "SKILL.md",
            "<!-- xid: SLOTDOC -->\n# Skill: slot_sample\n",
        )

        catalog = XRefCatalog.build(self.repo)
        result = catalog.resolve_skill_knowledge("slot_sample")

        self.assertEqual(result["skill_id"], "slot_sample")
        self.assertEqual(len(result["slots"]), 2)

        query_slot = result["slots"][0]
        self.assertEqual(query_slot["slot"], "context")
        self.assertTrue(query_slot["required"])
        self.assertEqual(query_slot["domain"], "organization")
        self.assertTrue(query_slot["satisfied"])
        self.assertTrue(
            any(candidate["xid"] == "ABC123" for candidate in query_slot["candidates"])
        )

        bind_slot = result["slots"][1]
        self.assertEqual(bind_slot["bind"], "ABC123")
        self.assertEqual(bind_slot["candidates"][0]["xid"], "ABC123")

        self.assertEqual(result["unsatisfied_required"], [])

    def test_rank_skills_uses_triad_facets_and_reports_preconditions(self) -> None:
        # Design 084 M4: the triad is the routing vocabulary; declared
        # preconditions travel with the ranking.
        write(
            self.repo / "skills" / "triad_rank" / "meta.md",
            """<!-- xid: TRIADRANKMETA -->
# Skill Meta: triad_rank

- skill_id: `triad_rank`
- summary: triad-routed review skill
- maturity: `trial`
- capability: software_development
- tuning: C#
- responsibility: quality check
- preconditions:
  - implemented code exists
- skill_doc: `./SKILL.md`
""",
        )
        write(
            self.repo / "skills" / "triad_rank" / "SKILL.md",
            "<!-- xid: TRIADRANKDOC -->\n# Skill: triad_rank\n",
        )

        catalog = XRefCatalog.build(self.repo)
        ranked = catalog.rank_skills_for_purpose("software_development C# quality check")
        entry = next(item for item in ranked if item["skill_id"] == "triad_rank")

        facet_labels = {facet.split("=", 1)[0] for facet in entry["matched_facets"]}
        self.assertIn("capability", facet_labels)
        self.assertIn("tuning", facet_labels)
        self.assertIn(
            "implemented code exists",
            entry["execution_readiness"]["declared_preconditions"],
        )

    def test_rank_skills_uses_categories_for_japanese_test_planning(self) -> None:
        write(
            self.repo / "skills" / "test_flow" / "meta.md",
            """<!-- xid: TESTFLOWMETA -->
# Skill Meta: test_flow

- skill_id: `test_flow`
- summary: execute test-planning, test-item structuring, integration/regression test design, and manufacturing-side test-method review
- use_when: user needs a reviewed test package from planning outputs, requirements, and design evidence
- input: approved requirements, work plan, test policy, test tool policy
- output: test plan with selected test tool basis, test execution preparation plan, local-domain test execution helper script plan, test design
- maturity: `draft`
- capability: test planning
- tuning: test execution preparation and helper scripts
- responsibility: prepare test plans with test data, tools, scripts, and traceability
- skill_doc: `./SKILL.md`
""",
        )
        write(
            self.repo / "skills" / "test_flow" / "SKILL.md",
            "<!-- xid: TESTFLOWDOC -->\n# Skill: test_flow\n",
        )
        write(
            self.repo / "skills" / "implementation_flow" / "meta.md",
            """<!-- xid: IMPLMETA -->
# Skill Meta: implementation_flow

- skill_id: `implementation_flow`
- summary: implement code and scripts after design approval
- use_when: user needs implementation
- input: approved design
- output: source changes
- maturity: `trial`
- capability: implementation
- tuning: code and script implementation
- responsibility: implement approved changes
- skill_doc: `./SKILL.md`
""",
        )
        write(
            self.repo / "skills" / "implementation_flow" / "SKILL.md",
            "<!-- xid: IMPLDOC -->\n# Skill: implementation_flow\n",
        )
        write(
            self.repo / "skills" / "db_design" / "meta.md",
            """<!-- xid: DBDESIGNMETA -->
# Skill Meta: db_design

- skill_id: `db_design`
- summary: design database schema, stored procedures, and SQL helper scripts
- use_when: user needs database design or SQL implementation planning
- input: database requirements, table rules, stored procedure rules
- output: database design, SQL script preparation, database helper tooling
- maturity: `draft`
- capability: database design
- tuning: SQL scripts and database tool preparation
- responsibility: prepare database implementation rules
- skill_doc: `./SKILL.md`
""",
        )
        write(
            self.repo / "skills" / "db_design" / "SKILL.md",
            "<!-- xid: DBDESIGNDOC -->\n# Skill: db_design\n",
        )
        write(
            self.repo / "skills" / "test_tool_catalog_preparation" / "meta.md",
            """<!-- xid: TESTTOOLCATALOGMETA -->
# Skill Meta: test_tool_catalog_preparation

- skill_id: `test_tool_catalog_preparation`
- summary: prepare a domain/environment test-tool catalog as reusable domain knowledge for test planning and test design
- use_when: user needs to catalog test tools before test planning
- input: target domain, test environment, existing test tool information
- output: test tool catalog domain knowledge
- maturity: `draft`
- capability: test tool cataloging
- tuning: domain test-tool catalog preparation
- responsibility: catalog test tools for test planning
- skill_doc: `./SKILL.md`
""",
        )
        write(
            self.repo / "skills" / "test_tool_catalog_preparation" / "SKILL.md",
            "<!-- xid: TESTTOOLCATALOGDOC -->\n# Skill: test_tool_catalog_preparation\n",
        )

        catalog = XRefCatalog.build(self.repo)
        ranked = catalog.rank_skills_for_purpose(
            "テスト用スクリプトを用意し、テストの実行を簡易にする",
            limit=5,
        )
        by_skill_id = {entry["skill_id"]: entry for entry in ranked}

        self.assertEqual(ranked[0]["skill_id"], "test_flow")
        self.assertIn("summary", ranked[0])
        self.assertIn("matched_categories", ranked[0])
        self.assertIn("activity", ranked[0]["matched_categories"])
        self.assertIn("artifact", ranked[0]["matched_categories"])
        self.assertIn("domain", ranked[0]["matched_categories"])
        self.assertIn("tool_runtime", ranked[0]["matched_categories"])
        self.assertGreater(by_skill_id["test_flow"]["score"], by_skill_id["db_design"]["score"])

        catalog_ranked = catalog.rank_skills_for_purpose(
            "試験ツールをカタログ化して試験計画で使う",
            limit=5,
        )
        self.assertEqual(
            catalog_ranked[0]["skill_id"],
            "test_tool_catalog_preparation",
        )

    def test_rejects_server_tool_with_side_effects(self) -> None:
        contract = ToolContract(
            tool_id="bad.write",
            provider="test",
            version="1",
            execution_location="server",
            side_effects="repo_write",
            input_schema={},
            output_schema={},
            requires_workspace=True,
            required_when="never",
        )

        with self.assertRaises(ValueError):
            contract.validate()

    def test_startup_context_lists_base_control_references(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        context = catalog.get_startup_context()
        xids = [reference["xid"] for reference in context["references"]]

        self.assertEqual(context["link_resolution"]["resolver_tool"], "get_document_by_xid")
        self.assertEqual(context["access_policy"]["mode"], "mcp_only")
        self.assertEqual(context["access_policy"]["source_of_truth"], "xrefkit.mcp")
        self.assertIn(
            "get_startup_context",
            context["access_policy"]["required_tools"]["startup"],
        )
        self.assertTrue(
            any("get_document_by_xid" in item for item in context["client_instructions"])
        )
        self.assertTrue(
            any("MCP-only mode is active" in item for item in context["client_instructions"])
        )
        self.assertTrue(
            any("Materialize and apply startup references" in item for item in context["client_instructions"])
        )
        self.assertTrue(
            any("Do not automatically load all links from startup references" in item for item in context["client_instructions"])
        )
        self.assertTrue(
            any("client-side audit log" in item for item in context["client_instructions"])
        )
        self.assertEqual(
            context["context_injection_policy"]["default_document_body_mode"],
            "lazy",
        )
        self.assertEqual(
            context["context_injection_policy"]["model_context_format"],
            "plain_text",
        )
        self.assertEqual(
            context["context_injection_policy"]["model_context_source"],
            "startup_contract_pack.body",
        )
        self.assertIs(
            context["context_injection_policy"]["do_not_inject_raw_startup_json"],
            True,
        )
        self.assertIs(
            context["context_injection_policy"]["materialize_does_not_imply_prompt_injection"],
            True,
        )
        self.assertEqual(
            context["context_injection_policy"]["startup_reference_prompt_mode"],
            "required_startup_contract_pack",
        )
        self.assertIs(
            context["context_injection_policy"]["startup_contract_pack_visible_by_default"],
            True,
        )
        self.assertIs(
            context["context_injection_policy"]["startup_reference_body_visible_by_default"],
            False,
        )
        self.assertEqual(
            context["context_injection_policy"]["default_nonstartup_document_body_mode"],
            "lazy",
        )
        self.assertEqual(
            context["session_context_deduplication"]["dedupe_key"],
            ["repository_fingerprint", "xid", "content_hash"],
        )
        self.assertEqual(
            context["session_context_deduplication"]["active_model_context_cardinality"],
            "at_most_one_body_per_dedupe_key",
        )
        self.assertIn("8A666C1FD121", xids)
        self.assertIn("0B5C58B5E5B2", xids)
        self.assertEqual(context["missing"], [])
        pack = context["startup_contract_pack"]
        self.assertEqual(pack["mode"], "required_startup_contract_pack")
        self.assertEqual(pack["pack_version"], 1)
        self.assertEqual(pack["source_xids"], xids)
        self.assertEqual(
            pack["source_hashes"],
            {reference["xid"]: reference["content_hash"] for reference in context["references"]},
        )
        self.assertIn("# Startup Contract Pack v1", pack["body"])
        self.assertIn(
            'python -m xrefkit skill run --meta <path-to-meta.md> --task "<task>" --json',
            pack["body"],
        )
        self.assertEqual(
            pack["pack_hash"],
            hashlib.sha256(pack["body"].encode("utf-8")).hexdigest(),
        )
        self.assertIn("python -m xrefkit skill verify --log <run-log>", pack["body"])
        self.assertIn("python -m xrefkit xref search \"<query>\"", pack["body"])
        self.assertIn("Stop and escalate", pack["body"])
        self.assertEqual(context["references"][0]["layer"], "base_control")
        self.assertNotIn("reason", context["references"][0])
        self.assertNotIn("path", context["references"][0])
        self.assertIsNone(context["references"][0]["content"])
        self.assertIs(context["references"][0]["content_omitted"], True)
        self.assertIs(
            context["references"][0]["included_in_startup_contract_pack"],
            True,
        )
        first_link = context["references"][0]["links"][0]
        self.assertEqual(first_link["xid"], "8A666C1FD121")
        self.assertNotIn("path", first_link)
        self.assertNotIn("target", first_link)
        self.assertEqual(first_link["resolver_tool"], "get_document_by_xid")
        self.assertEqual(first_link["resolver_argument"], "xid")
        self.assertNotIn("workflows", context)
        self.assertNotIn("workflow_protocol", context)
        self.assertNotIn("runtime_role_contract", context)
        self.assertNotIn("client_tool_distribution", context)
        routing_refs = {
            reference["id"]: reference
            for reference in context["semantic_routing_references"]
        }
        self.assertEqual(
            routing_refs["skills"]["summary_arguments"],
            {"include_content": False},
        )
        self.assertEqual(routing_refs["skills"]["rank_tool"], "rank_skills_for_purpose")
        self.assertEqual(routing_refs["skills"]["materialize_tool"], "get_skill")
        self.assertNotIn("workflows", routing_refs)
        self.assertNotIn("client_tools", routing_refs)
        obligation_ids = {item["id"] for item in context["client_obligations"]}
        self.assertIn("startup.first_call", obligation_ids)
        self.assertIn("content.mcp_only", obligation_ids)
        self.assertIn("startup.log_decision_xids", obligation_ids)
        self.assertIn("tools.materialize_from_mcp", obligation_ids)
        self.assertIn("context.no_duplicate_xid_body_per_session", obligation_ids)

    def test_startup_context_omits_cached_reference_bodies(self) -> None:
        catalog = XRefCatalog.build(self.repo)
        first = catalog.get_startup_context()
        versions = {
            reference["xid"]: reference["content_hash"]
            for reference in first["references"]
        }

        cached = catalog.get_startup_context(versions)

        self.assertTrue(
            all(reference["included_in_startup_contract_pack"] for reference in cached["references"])
        )
        self.assertTrue(
            all(reference["content_omitted"] for reference in cached["references"])
        )
        self.assertTrue(
            all(reference["content"] is None for reference in cached["references"])
        )
        self.assertEqual(
            cached["startup_contract_pack"]["source_hashes"],
            {reference["xid"]: reference["content_hash"] for reference in cached["references"]},
        )

    def test_selected_skill_advertises_client_tool_download(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        skill = catalog.get_skill("sample_review")
        requirements = catalog.get_skill_requirements("sample_review")

        for payload in [skill, requirements]:
            download = payload["client_tool_download"]
            self.assertIs(download["required"], True)
            self.assertIs(download["do_not_download_at_startup"], True)
            self.assertEqual(download["manifest_tool"], "get_client_tool_manifest")
            self.assertEqual(download["package_tool"], "get_client_tool_pip_package")
            self.assertEqual(download["version_check_tool"], "check_client_tool_versions")
            self.assertEqual(
                download["required_client_tools"][0]["name"],
                "xrefkit skill run",
            )

    def test_startup_context_resolves_reference_after_document_move(self) -> None:
        source = self.repo / "docs" / "core" / "contracts" / "016_uncertainty_protocol.md"
        target = self.repo / "docs" / "core" / "contracts" / "uncertainty_protocol.md"
        source.rename(target)

        context = XRefCatalog.build(self.repo).get_startup_context()
        uncertainty = next(
            reference
            for reference in context["references"]
            if reference["xid"] == "8A666C1FD121"
        )

        self.assertNotIn("path", uncertainty)
        self.assertEqual(uncertainty["xid"], "8A666C1FD121")
        self.assertEqual(context["missing"], [])

    def test_resolves_any_managed_document_by_xid(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        document = catalog.get_document_by_xid("8A666C1FD121")

        self.assertNotIn("path", document)
        self.assertIn("# Uncertainty Protocol", document["content"])
        self.assertIn("xid-8A666C1FD121", document["content"])
        self.assertNotIn(".md#xid-", document["content"])
        self.assertNotIn("version", document)
        self.assertIs(document["cache_policy"]["cache_recommended"], True)

    def test_resolves_xid_bearing_yaml_document_by_xid(self) -> None:
        write(
            self.repo / "skills" / "sample" / "references" / "flow_template.yaml",
            """# xid: YAMLXID123

flow_id: sample
""",
        )
        catalog = XRefCatalog.build(self.repo)

        document = catalog.get_document_by_xid("YAMLXID123")

        self.assertEqual(document["xid"], "YAMLXID123")
        self.assertNotIn("path", document)
        self.assertIn("flow_id: sample", document["content"])

    def test_conditional_document_resolution_omits_unchanged_content(self) -> None:
        catalog = XRefCatalog.build(self.repo)
        document = catalog.get_document_by_xid("8A666C1FD121")

        unchanged = catalog.get_document_by_xid(
            "8A666C1FD121",
            document["content_hash"],
        )
        stale = catalog.get_document_by_xid("8A666C1FD121", "stale-version")

        self.assertEqual(unchanged["cache_status"], "not_modified")
        self.assertIs(unchanged["content_omitted"], True)
        self.assertNotIn("version", unchanged)
        self.assertNotIn("content", unchanged)
        self.assertEqual(stale["cache_status"], "modified")
        self.assertNotIn("version", stale)
        self.assertIn("# Uncertainty Protocol", stale["content"])

    def test_cache_policy_bypasses_when_version_payload_is_not_smaller(self) -> None:
        document = XRefDocument(
            xid="A",
            title="",
            path="a",
            summary="",
            content="x",
            links=[],
            content_hash="0" * 64,
        )

        policy = _document_cache_policy(document, REPOSITORY_FINGERPRINT)

        self.assertEqual(policy["maximum_ratio"], CACHE_MAX_VERSION_PAYLOAD_RATIO)
        self.assertIs(policy["cache_recommended"], False)

        first = _conditional_document_response(
            document,
            None,
            REPOSITORY_FINGERPRINT,
        )
        conditional = _conditional_document_response(
            document,
            document.content_hash,
            REPOSITORY_FINGERPRINT,
        )

        self.assertEqual(first["cache_status"], "miss")
        self.assertIs(first["cache_policy"]["cache_recommended"], False)
        self.assertEqual(conditional["cache_status"], "bypassed")
        self.assertIn("content", conditional)

    def test_distributes_client_side_python_tools_without_server_execution(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        manifest = catalog.get_client_tool_manifest()
        file_paths = [file["path"] for file in manifest["files"]]
        tool_file = catalog.get_client_tool_file("tools/sample_tool.py")
        bundle = catalog.get_client_tool_bundle()

        self.assertEqual(manifest["execution_location"], "client")
        self.assertEqual(manifest["version"], "0.1.0")
        self.assertIs(manifest["server_executes_tools"], False)
        self.assertEqual(manifest["file_hash_algorithm"], "sha256")
        self.assertEqual(manifest["version_check_tool"], "check_client_tool_versions")
        self.assertIn("xrefkit-client-tools", manifest["required_package_ids"])
        self.assertEqual(manifest["package_versions"]["xrefkit-client-tools"], "0.1.0")
        self.assertEqual(
            manifest["materialization"]["pip_package_tool"],
            "get_client_tool_pip_package",
        )
        self.assertIs(manifest["update_policy"]["update_when_version_mismatch"], True)
        self.assertIn("tools/sample_tool.py", file_paths)
        self.assertIn("tools/profiles/sample.editorconfig", file_paths)
        self.assertEqual(tool_file["kind"], "python")
        self.assertIn("argparse", tool_file["imports"])
        self.assertIn("argparse.ArgumentParser", tool_file["content"])
        self.assertGreaterEqual(len(bundle["files"]), 2)

    def test_builds_pip_installable_client_tool_package(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        package = catalog.get_client_tool_pip_package()
        data = base64.b64decode(package["content_base64"])
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())
            pyproject = archive.read(
                "xrefkit-client-tools-0.1.0/pyproject.toml"
            ).decode("utf-8")

        self.assertEqual(package["package_format"], "zip-sdist")
        self.assertEqual(package["version"], "0.1.0")
        self.assertIn("python -m pip install", package["install_command"])
        self.assertIn("xrefkit-client-tools-0.1.0/tools/sample_tool.py", names)
        self.assertIn("xrefkit-client-tools-0.1.0/tools/__init__.py", names)
        self.assertIn("xrefkit-sample-tool", pyproject)

    def test_checks_client_tool_versions(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        ok = catalog.check_client_tool_versions(
            {
                "xrefkit-client-python-tools": "0.1.0",
                "xrefkit-client-tools": "0.1.0",
            }
        )
        mismatch = catalog.check_client_tool_versions(
            {"xrefkit-client-python-tools": "0.0.1"}
        )

        self.assertIs(ok["ok"], True)
        self.assertIs(mismatch["ok"], False)
        self.assertTrue(any(row["status"] == "mismatch" for row in mismatch["results"]))
        self.assertTrue(any(row["status"] == "missing" for row in mismatch["results"]))

    def test_tool_contracts_describe_response_envelope_and_json_schema(self) -> None:
        catalog = XRefCatalog.build(self.repo)

        contracts = {contract["tool_id"]: contract for contract in catalog.list_tool_contracts()}

        self.assertEqual(
            contracts["xref.list_skills"]["response_envelope"],
            "mcp_result_array",
        )
        self.assertEqual(
            contracts["xref.get_startup_context"]["response_envelope"],
            "direct_object",
        )
        self.assertEqual(
            contracts["xref.get_document_by_xid"]["input_json_schema"]["properties"]["xid"]["type"],
            "string",
        )
        self.assertNotIn(
            "known_version",
            contracts["xref.get_document_by_xid"]["input_json_schema"]["required"],
        )


if __name__ == "__main__":
    unittest.main()


class FreshnessTests(unittest.TestCase):
    """All catalog accessors must reflect the live repository state.

    Regression tests for the frozen build-time snapshot that let
    expand_knowledge return a stale content_hash next to a live body,
    breaking the client cache protocol on long-running servers.
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        write(
            self.repo / "knowledge" / "organization" / "rules.md",
            """<!-- xid: FRESH01 -->
<a id="xid-FRESH01"></a>

# Original Title

Original summary paragraph.
""",
        )
        write(
            self.repo / "skills" / "first" / "meta.md",
            "- skill_id: `first_skill`\n- summary: first skill\n- skill_doc: `./SKILL.md`\n",
        )
        write(self.repo / "skills" / "first" / "SKILL.md", "# Skill: first_skill\n")
        self.catalog = XRefCatalog.build(self.repo)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_expand_knowledge_hash_matches_body_after_edit(self) -> None:
        write(
            self.repo / "knowledge" / "organization" / "rules.md",
            """<!-- xid: FRESH01 -->
<a id="xid-FRESH01"></a>

# Edited Title

Edited summary paragraph.
""",
        )

        expanded = self.catalog.expand_knowledge("FRESH01")

        self.assertEqual(
            expanded["entry"]["content_hash"],
            hashlib.sha256(expanded["content"].encode("utf-8")).hexdigest(),
        )
        self.assertEqual(expanded["entry"]["title"], "Edited Title")
        self.assertIn("Edited summary", expanded["content"])

    def test_knowledge_catalog_reflects_files_added_after_build(self) -> None:
        write(
            self.repo / "knowledge" / "organization" / "added.md",
            "<!-- xid: FRESH02 -->\n\n# Added Later\n\nAdded body.\n",
        )

        xids = [entry["xid"] for entry in self.catalog.list_knowledge_catalog()]

        self.assertIn("FRESH02", xids)
        self.assertEqual(
            self.catalog.expand_knowledge("FRESH02")["entry"]["title"],
            "Added Later",
        )

    def test_skill_catalog_reflects_additions_and_removals_after_build(self) -> None:
        write(
            self.repo / "skills" / "second" / "meta.md",
            "- skill_id: `second_skill`\n- summary: second skill\n- skill_doc: `./SKILL.md`\n",
        )
        write(self.repo / "skills" / "second" / "SKILL.md", "# Skill: second_skill\n")
        (self.repo / "skills" / "first" / "meta.md").unlink()

        skill_ids = [entry["skill_id"] for entry in self.catalog.list_skills()]

        self.assertIn("second_skill", skill_ids)
        self.assertNotIn("first_skill", skill_ids)

    def test_catalog_version_changes_when_content_changes(self) -> None:
        before = self.catalog.catalog_version

        write(
            self.repo / "knowledge" / "organization" / "rules.md",
            "<!-- xid: FRESH01 -->\n\n# Edited Title\n\nEdited.\n",
        )

        self.assertNotEqual(self.catalog.catalog_version, before)

    def test_catalog_version_changes_when_external_domain_knowledge_changes(self) -> None:
        external_root = self.repo.parent / "domain-store"
        external_file = external_root / "billing.md"
        write(
            external_file,
            "<!-- xid: EXTFRESH01 -->\n\n# External Original\n\nOriginal.\n",
        )
        catalog = XRefCatalog.build(self.repo, [external_root])
        before = catalog.catalog_version

        write(
            external_file,
            "<!-- xid: EXTFRESH01 -->\n\n# External Edited\n\nEdited.\n",
        )

        self.assertNotEqual(catalog.catalog_version, before)

    def test_build_knowledge_context_bodies_match_their_hashes(self) -> None:
        write(
            self.repo / "knowledge" / "organization" / "rules.md",
            "<!-- xid: FRESH01 -->\n\n# Edited Title\n\nEdited context body.\n",
        )

        context = self.catalog.build_knowledge_context("edited title", limit=2)

        self.assertTrue(context["entries"])
        for expanded in context["entries"]:
            self.assertEqual(
                expanded["entry"]["content_hash"],
                hashlib.sha256(expanded["content"].encode("utf-8")).hexdigest(),
            )


class StartupPackDriftTests(unittest.TestCase):
    """The startup contract pack must report drift against its sources."""

    STARTUP_DOCS = [
        ("agent/000_agent_entry.md", "0B5C58B5E5B2", "Agent Entry"),
        ("docs/core/models/017_base_and_xref_layering.md", "5A1C8E4D2F90", "Base Layers"),
        ("docs/core/contracts/011_startup_xref_routing.md", "6C0B62D6366A", "Startup Routing"),
        ("docs/core/contracts/016_uncertainty_protocol.md", "8A666C1FD121", "Uncertainty"),
        ("docs/core/contracts/053_context_direction_security_guard.md", "A7F3C92D4E11", "Guard"),
        ("docs/core/contracts/015_shared_memory_operations.md", "4A423E72D2ED", "Shared Memory"),
    ]
    PACK_DOC_PATH = "docs/core/contracts/079_startup_contract_pack.md"

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        for rel_path, xid, title in self.STARTUP_DOCS:
            write(
                self.repo / rel_path,
                f"<!-- xid: {xid} -->\n<a id=\"xid-{xid}\"></a>\n\n# {title}\n\nBody of {title}.\n",
            )
        self.catalog = XRefCatalog.build(self.repo)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_pack_doc(self, based_on: dict[str, str]) -> None:
        hash_lines = "\n".join(f"- {xid}: `{value}`" for xid, value in based_on.items())
        write(
            self.repo / self.PACK_DOC_PATH,
            f"""<!-- xid: D4E8A1C63B57 -->
<a id="xid-D4E8A1C63B57"></a>

# Startup Contract Pack v1

## Based On

- pack_version: 1
{hash_lines}

## Global startup invariants

- Pack body authored from the sources above.
""",
        )

    def test_missing_pack_doc_falls_back_and_reports_stale(self) -> None:
        context = self.catalog.get_startup_context()
        pack = context["startup_contract_pack"]

        self.assertEqual(pack["pack_source"], "embedded_fallback")
        self.assertIsNone(pack["pack_doc_xid"])
        self.assertTrue(pack["stale"])
        self.assertEqual(len(pack["stale_sources"]), 6)
        self.assertEqual(
            pack["pack_hash"],
            hashlib.sha256(pack["body"].encode("utf-8")).hexdigest(),
        )
        self.assertTrue(
            any(
                "startup_contract_pack is STALE" in instruction
                for instruction in context["client_instructions"]
            )
        )

    def test_repo_pack_doc_with_matching_hashes_is_not_stale(self) -> None:
        live_hashes = self.catalog.get_startup_context()["startup_contract_pack"][
            "source_hashes"
        ]
        self._write_pack_doc(live_hashes)

        context = self.catalog.get_startup_context()
        pack = context["startup_contract_pack"]

        self.assertEqual(pack["pack_source"], "repository_document")
        self.assertEqual(pack["pack_doc_xid"], "D4E8A1C63B57")
        self.assertFalse(pack["stale"])
        self.assertEqual(pack["stale_sources"], [])
        self.assertEqual(pack["pack_version"], 1)
        self.assertEqual(pack["based_on_hashes"], live_hashes)
        self.assertIn("Pack body authored from the sources above.", pack["body"])
        self.assertEqual(
            pack["pack_hash"],
            hashlib.sha256(pack["body"].encode("utf-8")).hexdigest(),
        )
        self.assertFalse(
            any(
                "startup_contract_pack is STALE" in instruction
                for instruction in context["client_instructions"]
            )
        )

    def test_source_edit_after_pack_authoring_flags_exactly_that_source(self) -> None:
        live_hashes = self.catalog.get_startup_context()["startup_contract_pack"][
            "source_hashes"
        ]
        self._write_pack_doc(live_hashes)
        rel_path, xid, title = self.STARTUP_DOCS[3]
        write(
            self.repo / rel_path,
            f"<!-- xid: {xid} -->\n<a id=\"xid-{xid}\"></a>\n\n# {title}\n\nRevised body.\n",
        )

        context = self.catalog.get_startup_context()
        pack = context["startup_contract_pack"]

        self.assertTrue(pack["stale"])
        self.assertEqual([item["xid"] for item in pack["stale_sources"]], [xid])
        self.assertEqual(
            pack["stale_sources"][0]["based_on_hash"], live_hashes[xid]
        )
        self.assertNotEqual(
            pack["stale_sources"][0]["live_hash"], live_hashes[xid]
        )
        self.assertTrue(
            any(
                xid in instruction and "STALE" in instruction
                for instruction in context["client_instructions"]
            )
        )

    def test_parse_helpers(self) -> None:
        from xrefkit.mcp.startup_contract_pack import (
            parse_based_on_hashes,
            parse_pack_version,
        )

        text = "- pack_version: 3\n- 0B5C58B5E5B2: `" + "a" * 64 + "`\n- not a hash line\n"
        self.assertEqual(parse_pack_version(text), 3)
        self.assertEqual(parse_based_on_hashes(text), {"0B5C58B5E5B2": "a" * 64})
