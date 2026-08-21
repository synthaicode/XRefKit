from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from typing import Any
from pathlib import Path

from xrefkit.__main__ import main
from xrefkit.mcp.client_flow import (
    PromptFlowClient,
    PromptFlowProtocolError,
)
from xrefkit.mcp.client_cache import XidDocumentCache


STARTUP = {
    "prompt_flow_protocol": {
        "version": "1",
        "reconciliation": {"default": "report_only"},
    }
}


class PromptFlowClientTests(unittest.TestCase):
    def test_initialize_creates_root_identity_and_audit_event(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = PromptFlowClient(temp_dir, "repo-fingerprint")
            context = client.initialize(STARTUP, "Implement the requested change")

            self.assertEqual(context.flow_id, context.root_run_id)
            self.assertEqual(len(context.root_run_id), 36)
            self.assertEqual(
                context.correlation(),
                {"flow_id": context.flow_id, "root_run_id": context.root_run_id},
            )
            self.assertEqual(client.initialization_events()[0]["event"], "flow.initialized")
            self.assertNotIn("Implement the requested change", client.audit_path.read_text(encoding="utf-8"))

    def test_child_correlation_preserves_flow_and_parent_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = PromptFlowClient(temp_dir, "repo-fingerprint")
            context = client.initialize(STARTUP, "Task")
            correlation = context.correlation(
                parent_run_id="parent-run",
                work_item_id="WI-001",
                node_id="node-001",
            )

            self.assertEqual(correlation["flow_id"], context.flow_id)
            self.assertEqual(correlation["root_run_id"], context.root_run_id)
            self.assertEqual(correlation["parent_run_id"], "parent-run")
            self.assertEqual(correlation["work_item_id"], "WI-001")
            bind_args = context.mcp_bind_arguments(
                run_id="child-run",
                skill_id="sample_skill",
                parent_run_id="parent-run",
                work_item_id="WI-001",
            )
            self.assertEqual(bind_args["flow_id"], context.flow_id)
            self.assertEqual(bind_args["skill_id"], "sample_skill")

    def test_host_builders_preserve_flow_correlation_and_routing_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = PromptFlowClient(temp_dir, "repo-fingerprint").initialize(
                STARTUP, "Task", flow_id="FLOW-001", root_run_id="11111111-1111-4111-8111-111111111111"
            )
            run_args = context.workflow_run_arguments(
                task="Execute generic work",
                parent_run_id="22222222-2222-4222-8222-222222222222",
                work_item_id="WI-001",
                node_id="NODE-001",
                purpose="Deliver the requested change",
                scope_in=["Dashboard"],
                expected_evidence=["pytest output"],
            )
            self.assertEqual(run_args[:6], ["workflow", "run", "--task", "Execute generic work", "--flow-id", "FLOW-001"])
            self.assertIn("--root-run-id", run_args)
            self.assertIn("--work-item-id", run_args)
            routing_args = context.workflow_routing_arguments(
                log="work/sessions/parent.md",
                selected_skill="skill_a",
                candidates=["skill_a", "skill_b"],
                reason="The Work Item matches skill_a",
                target_work_item="WI-001",
            )
            self.assertIn("--selection-mode", routing_args)
            self.assertIn("semantic", routing_args)
            with self.assertRaises(PromptFlowProtocolError):
                context.workflow_routing_arguments(
                    log="parent.md", selection_mode="needs_clarification",
                    selected_skill="skill_a", candidates=["skill_a"], reason="uncertain",
                )

    def test_rejects_missing_or_unsafe_startup_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = PromptFlowClient(temp_dir, "repo-fingerprint")
            with self.assertRaises(PromptFlowProtocolError):
                client.initialize({}, "Task")
            with self.assertRaises(PromptFlowProtocolError):
                client.initialize(STARTUP, "Task", flow_id="unsafe flow")
            with self.assertRaises(PromptFlowProtocolError):
                client.initialize(STARTUP, "Task").correlation(work_item_id="WI-001")

    def test_existing_document_cache_can_initialize_flow_in_same_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = XidDocumentCache(temp_dir, "repo-fingerprint")
            context = cache.initialize_prompt_flow(STARTUP, "Task", flow_id="FLOW-001")

            self.assertEqual(context.flow_id, "FLOW-001")
            self.assertTrue((cache.cache_dir / "_prompt_flow.jsonl").exists())

    def test_cli_bridges_saved_startup_context_to_run_correlation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            startup = root / "startup.json"
            startup.write_text(json.dumps(STARTUP), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main([
                    "mcp", "flow-init",
                    "--startup-context", str(startup),
                    "--prompt", "Run the requested task",
                    "--cache-root", str(root / "cache"),
                    "--repository-fingerprint", "repo-fingerprint",
                    "--flow-id", "FLOW-CLI",
                ])

            self.assertEqual(result, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["flow"]["flow_id"], "FLOW-CLI")
            self.assertEqual(payload["root_run_correlation"]["flow_id"], "FLOW-CLI")

    def test_adapter_binds_skill_run_and_rejects_mismatched_flow(self) -> None:
        async def call_tool(name: str, arguments: dict[str, str]) -> dict[str, Any]:
            self.assertEqual(name, "bind_skill_run")
            return {**arguments, "audit_enabled": True}

        async def mismatched_tool(name: str, arguments: dict[str, str]) -> dict[str, Any]:
            return {**arguments, "flow_id": "OTHER-FLOW"}

        async def exercise() -> None:
            with tempfile.TemporaryDirectory() as temp_dir:
                context = PromptFlowClient(temp_dir, "repo-fingerprint").initialize(STARTUP, "Task", flow_id="FLOW-001")
                bound = await context.bind_skill_run(
                    call_tool,
                    run_id="child-run",
                    skill_id="sample_skill",
                    parent_run_id="parent-run",
                    work_item_id="WI-001",
                )
                self.assertEqual(bound["flow_id"], "FLOW-001")
                with self.assertRaises(PromptFlowProtocolError):
                    await context.bind_skill_run(
                        mismatched_tool,
                        run_id="child-run",
                        skill_id="sample_skill",
                    )

        import asyncio

        asyncio.run(exercise())
