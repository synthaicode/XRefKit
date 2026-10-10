import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from xrefkit.azure_update_candidate import build_candidate, main
from xrefkit.work_management import MAX_BYTES, submitted_hash

SENTINEL = "SYNTHETIC-SECRET-DO-NOT-EXPORT"


def synthetic_envelope():
    """Explicitly hypothetical input, not an Azure/local operational record."""
    plan = {"schema_version": 2, "workspace_id": "synthetic", "repository_root": "C:/synthetic/offline", "plan_id": "synthetic-plan", "plan_revision": "v1", "title": "Synthetic offline example", "source": "synthetic-source.md", "report_id": "synthetic-local-report", "project": {"project_id": "example", "title": "Synthetic"}, "change": {"change_id": "example", "title": "Synthetic"}, "baseline": {"baseline_id": "example"}, "stages": [{"stage_id": "example", "title": "Example"}], "steps": [{"step_id": step_id, "title": "Synthetic task", "stage_id": "example", "dependencies": [], "status": "done", "outputs": [], "runs": []} for step_id in ("a", "b")], "pbis": [], "confirmations": [], "external_refs": []}
    plan.update(observation_revision=1, observation_history=[], report_sha256=submitted_hash(plan))
    remote = {"organization": "example-org", "project": "Synthetic-Project", "item_id": 21, "work_item_type": "Task", "revision": 4, "state": "In Progress", "observed_at": "2026-10-10T00:00:00+00:00"}
    return {"schema_version": 1, "report_id": "synthetic-offline-candidate", "target": {"workspace_id": "synthetic", "connection_id": "offline-synthetic", "organization": "example-org", "project": "Synthetic-Project", "item_id": 21}, "binding": {"plan_id": "synthetic-plan", "plan_revision": "v1", "included_step_ids": ["a", "b"], "completion_criterion": "Synthetic external Task criterion", "initial_binding": False}, "local_snapshot": plan, "expected_observation_revision": 1, "completion": {"confirmed": True, "evidence_refs": ["synthetic-criterion-assertion"]}, "work_authorization": {"active": False, "rework": False, "evidence_refs": []}, "remote_snapshot": remote, "baseline": copy.deepcopy(remote), "metadata": {"work_item_type": "Task", "states": ["To Do", "In Progress", "Done", "Removed"], "transitions": {"To Do": ["To Do", "In Progress", "Done"], "In Progress": ["In Progress", "Done"], "Done": ["Done", "In Progress"], "Removed": []}}, "artifacts": [{"artifact_id": "design", "version": "v1", "availability": "local_only"}]}


def refresh(envelope):
    envelope["local_snapshot"]["report_sha256"] = submitted_hash(envelope["local_snapshot"])
    return envelope


class AzureUpdateCandidateTests(unittest.TestCase):
    def setUp(self):
        self.input = synthetic_envelope()

    def result(self):
        return build_candidate(refresh(self.input))

    def set_remote(self, state):
        self.input["remote_snapshot"]["state"] = state
        self.input["baseline"]["state"] = state

    def authorize(self, rework=False):
        self.input["work_authorization"] = {"active": True, "rework": rework, "evidence_refs": ["synthetic-authorization"]}

    def test_done_candidate_exact_fields_rev_guard_and_no_publish_claim(self):
        result = self.result()
        self.assertEqual("candidate", result["outcome"])
        self.assertEqual("Done", result["proposed_state"])
        self.assertEqual({"op": "test", "path": "/rev", "value": 4}, result["patch_preview"][0])
        self.assertEqual(["/rev", "/fields/System.State", "/fields/System.History"], [operation["path"] for operation in result["patch_preview"]])
        self.assertEqual("not_sent", result["delivery_status"])
        for key in ("network_performed", "remote_freshness_verified", "write_permission_verified", "publish_ready"):
            self.assertFalse(result[key])
        self.assertIn("task19_binding_import", result["publication_prerequisites"])
        self.assertIn("task20_local_first_evidence_policy", result["publication_prerequisites"])

    def test_identical_input_output_and_no_input_mutation_or_environment_lookup(self):
        before = copy.deepcopy(self.input)
        with patch.object(os.environ, "get", side_effect=AssertionError("credential lookup forbidden")), patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            first = build_candidate(self.input)
            second = build_candidate(self.input)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(before, self.input)

    def test_done_needs_grouped_external_criterion(self):
        self.input["local_snapshot"]["steps"][1]["status"] = "pending"
        self.assertEqual(["no_active_work"], self.result()["reason_codes"])
        self.input["local_snapshot"]["steps"][1]["status"] = "done"
        self.input["completion"]["confirmed"] = False
        self.assertEqual(["criterion_unconfirmed"], self.result()["reason_codes"])

    def test_missing_unknown_blocked_escalated_and_unrecognized_status_hold(self):
        for status, code in ((None, "local_status_missing"), ("unknown", "local_status_unknown"), ("blocked", "local_blocked"), ("escalated", "local_escalated"), (SENTINEL, "local_status_unrecognized")):
            with self.subTest(status=status):
                self.input["local_snapshot"]["steps"][0]["status"] = status
                result = self.result()
                self.assertEqual("hold", result["outcome"])
                self.assertIn(code, result["reason_codes"])
                self.assertEqual([], result["patch_preview"])
                self.assertNotIn(SENTINEL, json.dumps(result))

    def test_revalidation_and_explicit_actual_rework(self):
        self.input["local_snapshot"]["steps"][1]["revalidation_needed"] = True
        self.assertEqual(["revalidation_pending"], self.result()["reason_codes"])
        self.set_remote("Done")
        self.input["local_snapshot"]["steps"][0]["status"] = "in_progress"
        self.authorize(rework=True)
        result = self.result()
        self.assertEqual("In Progress", result["proposed_state"])
        self.assertEqual(["authorized_rework", "revalidation_pending"], result["reason_codes"])
        self.assertTrue(self.input["local_snapshot"]["steps"][1]["revalidation_needed"])

    def test_null_revalidation_is_not_new_completion_policy(self):
        self.input["local_snapshot"]["steps"][0]["revalidation_needed"] = None
        self.assertEqual("Done", self.result()["proposed_state"])
        self.assertIn("revalidation=unrecorded", self.result()["summary"])

    def test_active_and_rework_authority_are_not_inferred(self):
        self.input["local_snapshot"]["steps"][0]["status"] = "in_progress"
        self.assertEqual(["active_work_not_authorized"], self.result()["reason_codes"])
        self.authorize()
        self.assertEqual("In Progress", self.result()["proposed_state"])
        self.set_remote("Done")
        self.assertEqual(["rework_not_authorized"], self.result()["reason_codes"])

    def test_pending_never_regresses_remote_advanced_state(self):
        for step in self.input["local_snapshot"]["steps"]:
            step["status"] = "pending"
        self.input["binding"]["initial_binding"] = True
        self.assertEqual(["no_forward_transition"], self.result()["reason_codes"])
        self.set_remote("To Do")
        result = self.result()
        self.assertEqual("To Do", result["proposed_state"])
        self.assertEqual(["/rev", "/fields/System.History"], [item["path"] for item in result["patch_preview"]])

    def test_captured_same_state_requires_explicit_transition(self):
        self.set_remote("Done")
        self.input["metadata"]["transitions"]["Done"] = []
        self.assertEqual(["transition_unavailable"], self.result()["reason_codes"])

    def test_stale_local_and_remote_changes_are_distinct(self):
        self.input["expected_observation_revision"] = 2
        self.assertEqual(["stale_local_snapshot"], self.result()["reason_codes"])
        self.input["expected_observation_revision"] = 1
        self.input["remote_snapshot"]["revision"] = 5
        result = self.result()
        self.assertEqual("conflict", result["outcome"])
        self.assertEqual(["remote_changed"], result["reason_codes"])
        self.assertEqual([], result["patch_preview"])

    def test_removed_conflicts_and_missing_transition_holds(self):
        self.set_remote("Removed")
        self.assertEqual(["removed"], self.result()["reason_codes"])
        self.set_remote("In Progress")
        self.input["metadata"]["transitions"]["In Progress"] = ["In Progress"]
        self.assertEqual(["transition_unavailable"], self.result()["reason_codes"])

    def test_structural_invalid_input_does_not_echo_values(self):
        mutations = [lambda value: value.update(token=SENTINEL), lambda value: value["target"].update(project="Other"), lambda value: value["remote_snapshot"].update(work_item_type="Product Backlog Item"), lambda value: value["binding"].update(included_step_ids=["missing"]), lambda value: value["binding"].update(included_step_ids=["a", "a"]), lambda value: value["baseline"].update(revision=True), lambda value: value["completion"].update(confirmed=True, evidence_refs=[]), lambda value: value["metadata"].update(states=["Done", "Done"]), lambda value: value["remote_snapshot"].update(state="Future state"), lambda value: value["work_authorization"].update(active=False, rework=True, evidence_refs=["ref"])]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                envelope = synthetic_envelope()
                mutate(envelope)
                result = build_candidate(envelope)
                self.assertEqual("invalid", result["outcome"])
                self.assertEqual([], result["patch_preview"])
                self.assertNotIn(SENTINEL, json.dumps(result))

    def test_source_titles_evidence_paths_and_prose_never_leave_generator(self):
        self.input["binding"]["completion_criterion"] = SENTINEL
        self.input["completion"]["evidence_refs"] = ["C:/secret/" + SENTINEL]
        self.input["local_snapshot"]["title"] = "<script>" + SENTINEL
        self.input["local_snapshot"]["steps"][0].update(title=SENTINEL, status_evidence="C:/private/" + SENTINEL, completion_criterion=SENTINEL, outputs=["C:/private/" + SENTINEL])
        result = self.result()
        self.assertEqual("candidate", result["outcome"])
        rendered = json.dumps(result)
        self.assertNotIn(SENTINEL, rendered)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("C:/", rendered)

    def test_unicode_controls_in_target_state_and_references_are_invalid_without_echo(self):
        for control in ("\x7f", "\x85", "\u202e", "\u2028"):
            for field in ("project", "state", "evidence"):
                with self.subTest(control=ord(control), field=field):
                    envelope = synthetic_envelope()
                    value = "CONTROL-SENTINEL" + control
                    if field == "project":
                        for key in ("target", "remote_snapshot", "baseline"):
                            envelope[key]["project"] = value
                    elif field == "state":
                        envelope["remote_snapshot"]["state"] = value
                        envelope["baseline"]["state"] = value
                        envelope["metadata"]["states"].append(value)
                    else:
                        envelope["completion"]["evidence_refs"] = [value]
                    result = build_candidate(envelope)
                    self.assertEqual("invalid", result["outcome"])
                    self.assertNotIn("CONTROL-SENTINEL", json.dumps(result))

    def test_artifact_id_version_only_sorted_local_and_exact_duplicate_rejected(self):
        self.input["artifacts"] += [{"artifact_id": "design", "version": "v0", "availability": "local_only"}]
        result = self.result()
        self.assertIn("design@v0; design@v1", result["summary"])
        self.assertNotIn("http", result["summary"])
        self.input["artifacts"].append(copy.deepcopy(self.input["artifacts"][0]))
        self.assertEqual("invalid", self.result()["outcome"])

    def test_cli_repeat_is_identical_and_input_file_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "synthetic.json"
            source.write_text(json.dumps(self.input), encoding="utf-8")
            before = source.read_bytes()
            outputs = []
            for _ in range(2):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(0, main(["--input", str(source)]))
                outputs.append(stdout.getvalue())
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(before, source.read_bytes())
            self.assertEqual([source], list(Path(directory).iterdir()))

    def test_cli_invalid_arguments_duplicate_keys_and_oversize_are_inert(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.json"
            for body in (b'{"secret":"' + SENTINEL.encode() + b'","secret":"again"}', b"x" * (MAX_BYTES + 1)):
                source.write_bytes(body)
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(1, main(["--input", str(source)]))
                self.assertNotIn(SENTINEL, stdout.getvalue() + stderr.getvalue())
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(1, main(["--pat", SENTINEL]))
        self.assertNotIn(SENTINEL, stdout.getvalue() + stderr.getvalue())

    def test_cli_unicode_identity_works_with_windows_cp932_stdout(self):
        for key in ("target", "remote_snapshot", "baseline"):
            self.input[key]["project"] = "Project🚀"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "unicode.json"
            source.write_text(json.dumps(self.input), encoding="utf-8")
            buffer = io.BytesIO()
            stream = io.TextIOWrapper(buffer, encoding="cp932")
            with redirect_stdout(stream):
                self.assertEqual(0, main(["--input", str(source)]))
            stream.flush()
            self.assertEqual("Project🚀", json.loads(buffer.getvalue())["target"]["project"])
            stream.close()
