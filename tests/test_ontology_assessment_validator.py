import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/os/knowledge_ontology_management/scripts/validate_ontology_assessment.py"
SPEC = importlib.util.spec_from_file_location("ontology_assessment_validator", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "knowledge").mkdir()
        (self.root / "knowledge/a.md").write_text("<!-- xid: A -->\n# A\n", encoding="utf-8")
        self.record = {
            "target_knowledge_path": "knowledge/new.md",
            "proposed_primary_concept": "locally evidenced concept",
            "aliases_or_competing_terms_searched": ["concept", "local alias"],
            "candidate_existing_xids": ["A"],
            "concept_decision": "create",
            "concept_comparison": {
                "classification": "different_conditions", "rationale": "A applies only to CI; source limits this to local execution",
                "applicability": "local execution", "version": "source version 2", "constraints": "local evidence only",
                "source_authority": "maintainer supplied source"
            },
            "accepted_relationships": [], "no_relation_reason": "No stronger semantic relation is supported",
            "rejected_relationship_candidates": [{"target_xid": "A", "reason": "load dependence is not semantic dependence"}],
            "source_basis": "sources/policy-v2.md", "unresolved_semantic_conflicts": [],
            "publication_or_handoff_decision": "authorized apply after human review",
            "runtime_load_dependencies": ["A"],
        }

    def test_different_conditions_without_edge_is_valid_and_not_merged(self):
        before = copy.deepcopy(self.record)
        self.assertEqual([], VALIDATOR.validate(self.root, self.record, for_publication=True))
        self.assertEqual(before, self.record)
        self.assertFalse((self.root / "knowledge/new.md").exists())

    def test_missing_review_evidence_and_unknown_identity_are_rejected(self):
        for field in ("source_basis", "concept_comparison", "no_relation_reason"):
            record = copy.deepcopy(self.record)
            del record[field]
            self.assertTrue(VALIDATOR.validate(self.root, record), field)
        self.record["candidate_existing_xids"] = ["UNKNOWN"]
        self.assertTrue(any("unresolved candidate" in e for e in VALIDATOR.validate(self.root, self.record)))

    def test_conflict_can_be_recorded_in_proposal_but_blocks_publication(self):
        self.record["unresolved_semantic_conflicts"] = ["ownership between A and candidate unresolved"]
        self.assertEqual([], VALIDATOR.validate(self.root, self.record))
        self.assertTrue(any("block canonical publication" in e for e in VALIDATOR.validate(self.root, self.record, for_publication=True)))

    def test_relations_require_rationale_valid_targets_and_are_not_load_edges(self):
        self.record["accepted_relationships"] = [{"type": "related_to", "target_xid": "A", "rationale": "shared explicitly evidenced domain boundary"}]
        self.assertEqual([], VALIDATOR.validate(self.root, self.record))
        for bad in (
            {"type": "supersedes", "target_xid": "A", "rationale": "invalid manual replacement"},
            {"type": "related_to", "target_xid": "MISSING", "rationale": "unresolved"},
            {"type": "depends_on", "target_xid": "A"},
        ):
            self.record["accepted_relationships"] = [bad]
            self.assertTrue(VALIDATOR.validate(self.root, self.record))

    def test_self_duplicates_escape_and_invalid_types_fail_closed(self):
        relation = {"type": "depends_on", "target_xid": "A", "rationale": "condition requires A"}
        self.record["accepted_relationships"] = [relation, relation]
        self.assertTrue(any("duplicate" in e for e in VALIDATOR.validate(self.root, self.record)))
        self.record["target_knowledge_path"] = "knowledge/a.md"
        self.assertTrue(any("self relationship" in e for e in VALIDATOR.validate(self.root, self.record)))
        self.record["target_knowledge_path"] = "../outside.md"
        self.record["concept_decision"] = {}
        self.record["concept_comparison"]["classification"] = []
        self.assertTrue(any("target must" in e for e in VALIDATOR.validate(self.root, self.record)))

    def test_existing_contract_target_is_valid_without_becoming_knowledge(self):
        (self.root / "docs").mkdir()
        (self.root / "docs/contract.md").write_text("<!-- xid: CONTRACT -->\n# Contract\n", encoding="utf-8")
        self.record["accepted_relationships"] = [{"type": "constrains", "target_xid": "CONTRACT", "rationale": "explicitly limits the contract interpretation"}]
        self.assertEqual([], VALIDATOR.validate(self.root, self.record))

    def test_cli_rejects_surrogate_identity_with_json_diagnostic(self):
        self.record["candidate_existing_xids"] = ["\ud800"]
        record_path = self.root / "assessment.json"
        record_path.write_text(json.dumps(self.record), encoding="ascii")
        result = subprocess.run([sys.executable, str(SCRIPT), str(record_path), "--root", str(self.root)],
                                capture_output=True, text=True, encoding="ascii",
                                env={**os.environ, "PYTHONIOENCODING": "ascii"})
        self.assertEqual(1, result.returncode)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual("not_verified", payload["semantic_acceptance"])
        self.assertIn("unresolved candidate", payload["errors"][0])
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_rejects_deep_json_without_uncaught_recursion(self):
        record_path = self.root / "assessment.json"
        record_path.write_text("[" * 25000 + "0" + "]" * 25000, encoding="ascii")
        result = subprocess.run([sys.executable, str(SCRIPT), str(record_path), "--root", str(self.root)],
                                capture_output=True, text=True, encoding="ascii")
        self.assertEqual(1, result.returncode)
        self.assertEqual(["assessment nesting exceeds parser limit"], json.loads(result.stdout)["errors"])
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
