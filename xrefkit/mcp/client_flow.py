"""Client-side Prompt Flow initialization for MCP-backed work."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from collections.abc import Awaitable, Callable
from typing import Any

from .repository import stable_hash


FLOW_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")


class PromptFlowProtocolError(RuntimeError):
    """The MCP startup response cannot establish the Prompt Flow contract."""


@dataclass(frozen=True)
class PromptFlowContext:
    flow_id: str
    root_run_id: str
    repository_fingerprint: str
    prompt_hash: str
    protocol_version: str

    def to_dict(self) -> dict[str, str]:
        return {
            "flow_id": self.flow_id,
            "root_run_id": self.root_run_id,
            "repository_fingerprint": self.repository_fingerprint,
            "prompt_hash": self.prompt_hash,
            "protocol_version": self.protocol_version,
        }

    def correlation(
        self,
        *,
        parent_run_id: str | None = None,
        work_item_id: str | None = None,
        node_id: str | None = None,
    ) -> dict[str, str]:
        """Return the correlation fields to pass to a workflow or Skill run."""
        result = {
            "flow_id": self.flow_id,
            "root_run_id": self.root_run_id,
        }
        for key, value in (
            ("parent_run_id", parent_run_id),
            ("work_item_id", work_item_id),
            ("node_id", node_id),
        ):
            if value is not None and str(value).strip():
                result[key] = str(value).strip()
        if parent_run_id is None and (work_item_id is not None or node_id is not None):
            raise PromptFlowProtocolError(
                "work_item_id and node_id require parent_run_id for a child run"
            )
        return result

    def mcp_bind_arguments(
        self,
        *,
        run_id: str,
        skill_id: str,
        parent_run_id: str | None = None,
        work_item_id: str | None = None,
        node_id: str | None = None,
    ) -> dict[str, str]:
        """Return arguments for the MCP ``bind_skill_run`` tool."""
        return {
            "run_id": str(run_id),
            "skill_id": str(skill_id),
            **self.correlation(
                parent_run_id=parent_run_id,
                work_item_id=work_item_id,
                node_id=node_id,
            ),
        }

    def workflow_run_arguments(
        self,
        *,
        task: str,
        parent_run_id: str | None = None,
        work_item_id: str | None = None,
        node_id: str | None = None,
        purpose: str | None = None,
        scope_in: list[str] | None = None,
        scope_out: list[str] | None = None,
        owner: str | None = None,
        authority: str | None = None,
        expected_evidence: list[str] | None = None,
        stop_conditions: list[str] | None = None,
    ) -> list[str]:
        """Build a correlation-safe argv for a host's generic workflow run."""
        task_text = str(task).strip()
        if not task_text:
            raise ValueError("task is required to build a workflow run command")
        self.correlation(
            parent_run_id=parent_run_id,
            work_item_id=work_item_id,
            node_id=node_id,
        )
        arguments = [
            "workflow", "run", "--task", task_text,
            "--flow-id", self.flow_id, "--root-run-id", self.root_run_id,
        ]
        for key, value in (
            ("--parent-run-id", parent_run_id),
            ("--work-item-id", work_item_id),
            ("--node-id", node_id),
            ("--purpose", purpose),
            ("--owner", owner),
            ("--authority", authority),
        ):
            if value is not None and str(value).strip():
                arguments.extend([key, str(value).strip()])
        for key, values in (
            ("--scope-in", scope_in),
            ("--scope-out", scope_out),
            ("--expected-evidence", expected_evidence),
            ("--stop-condition", stop_conditions),
        ):
            for value in values or []:
                if str(value).strip():
                    arguments.extend([key, str(value).strip()])
        return arguments

    def workflow_routing_arguments(
        self,
        *,
        log: str,
        reason: str,
        selection_mode: str = "semantic",
        selected_skill: str | None = None,
        candidates: list[str] | None = None,
        target_work_item: str | None = None,
    ) -> list[str]:
        """Build a validated argv for recording a parent Flow routing decision."""
        mode = str(selection_mode).strip()
        candidate_values = [str(value).strip() for value in candidates or [] if str(value).strip()]
        selected = str(selected_skill or "").strip() or None
        if not str(log).strip() or not str(reason).strip():
            raise ValueError("log and reason are required to record workflow routing")
        if mode not in {"semantic", "explicit", "fallback", "needs_clarification"}:
            raise PromptFlowProtocolError(f"unsupported workflow routing mode: {mode!r}")
        if mode in {"fallback", "needs_clarification"} and selected:
            raise PromptFlowProtocolError(f"selected_skill must be omitted for routing mode {mode}")
        if mode not in {"fallback", "needs_clarification"} and (not selected or selected not in candidate_values):
            raise PromptFlowProtocolError("selected_skill must be present in candidates for a routed Skill decision")
        arguments = [
            "workflow", "routing", "--log", str(log).strip(),
            "--selection-mode", mode, "--reason", str(reason).strip(),
        ]
        if selected:
            arguments.extend(["--selected-skill", selected])
        for candidate in candidate_values:
            arguments.extend(["--candidate", candidate])
        if target_work_item is not None and str(target_work_item).strip():
            arguments.extend(["--target-work-item", str(target_work_item).strip()])
        return arguments

    async def bind_skill_run(
        self,
        call_tool: Callable[[str, dict[str, str]], Awaitable[dict[str, Any]]],
        *,
        run_id: str,
        skill_id: str,
        parent_run_id: str | None = None,
        work_item_id: str | None = None,
        node_id: str | None = None,
    ) -> dict[str, Any]:
        """Call MCP ``bind_skill_run`` and verify the returned Flow identity."""
        arguments = self.mcp_bind_arguments(
            run_id=run_id,
            skill_id=skill_id,
            parent_run_id=parent_run_id,
            work_item_id=work_item_id,
            node_id=node_id,
        )
        result = await call_tool("bind_skill_run", arguments)
        if not isinstance(result, dict):
            raise PromptFlowProtocolError("bind_skill_run returned a non-object result")
        for key in ("flow_id", "root_run_id", "parent_run_id", "work_item_id", "node_id"):
            expected = arguments.get(key)
            actual = result.get(key)
            if expected is not None and actual != expected:
                raise PromptFlowProtocolError(
                    f"bind_skill_run returned mismatched {key}: expected {expected!r}, got {actual!r}"
                )
        return result


class PromptFlowClient:
    """Create and preserve Prompt Flow identity after MCP startup loading.

    The client does not choose Skills or execute workflow operations. It only
    validates the startup contract, creates stable correlation fields, and
    records a factual client-side initialization event.
    """

    def __init__(self, cache_root: str | Path, repository_fingerprint: str) -> None:
        self.cache_root = Path(cache_root)
        self.repository_fingerprint = str(repository_fingerprint).strip()
        if not self.repository_fingerprint:
            raise ValueError("repository_fingerprint is required")
        self.flow_dir = self.cache_root / self.repository_fingerprint

    def initialize(
        self,
        startup_context: dict[str, Any],
        prompt: str,
        *,
        flow_id: str | None = None,
        root_run_id: str | None = None,
    ) -> PromptFlowContext:
        protocol = startup_context.get("prompt_flow_protocol")
        self._validate_protocol(protocol)
        prompt_text = str(prompt).strip()
        if not prompt_text:
            raise ValueError("prompt is required to initialize a Prompt Flow")

        root_id = root_run_id or str(uuid.uuid4())
        try:
            root_id = str(uuid.UUID(root_id))
        except (ValueError, AttributeError) as exc:
            raise PromptFlowProtocolError("root_run_id must be a UUID") from exc
        selected_flow_id = flow_id or root_id
        if not FLOW_ID_PATTERN.fullmatch(selected_flow_id):
            raise PromptFlowProtocolError(
                f"flow_id contains unsupported characters: {selected_flow_id!r}"
            )
        context = PromptFlowContext(
            flow_id=selected_flow_id,
            root_run_id=root_id,
            repository_fingerprint=self.repository_fingerprint,
            prompt_hash=stable_hash(prompt_text),
            protocol_version=str(protocol["version"]),
        )
        self._append_event(
            {
                "event": "flow.initialized",
                "flow_id": context.flow_id,
                "root_run_id": context.root_run_id,
                "repository_fingerprint": context.repository_fingerprint,
                "prompt_hash": context.prompt_hash,
                "protocol_version": context.protocol_version,
            }
        )
        return context

    def initialization_events(self) -> list[dict[str, Any]]:
        try:
            lines = self.audit_path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        return [json.loads(line) for line in lines if line.strip()]

    @property
    def audit_path(self) -> Path:
        return self.flow_dir / "_prompt_flow.jsonl"

    def _append_event(self, event: dict[str, Any]) -> None:
        self.flow_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "logged_at": datetime.now(UTC).isoformat(),
            **event,
        }
        with self.audit_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            log_file.write("\n")

    @staticmethod
    def _validate_protocol(protocol: Any) -> None:
        if not isinstance(protocol, dict):
            raise PromptFlowProtocolError(
                "MCP startup response is missing prompt_flow_protocol"
            )
        if str(protocol.get("version")) != "1":
            raise PromptFlowProtocolError(
                f"unsupported prompt_flow_protocol version: {protocol.get('version')!r}"
            )
        reconciliation = protocol.get("reconciliation")
        if not isinstance(reconciliation, dict):
            raise PromptFlowProtocolError(
                "prompt_flow_protocol is missing reconciliation rules"
            )
        if reconciliation.get("default") != "report_only":
            raise PromptFlowProtocolError(
                "Prompt Flow reconciliation must default to report_only"
            )


def initialize_prompt_flow_from_file(
    startup_context_path: str | Path,
    prompt: str,
    *,
    cache_root: str | Path,
    repository_fingerprint: str,
    flow_id: str | None = None,
    root_run_id: str | None = None,
) -> dict[str, Any]:
    """Initialize a Prompt Flow from a saved MCP startup response."""
    startup_context = json.loads(
        Path(startup_context_path).read_text(encoding="utf-8")
    )
    client = PromptFlowClient(cache_root, repository_fingerprint)
    context = client.initialize(
        startup_context,
        prompt,
        flow_id=flow_id,
        root_run_id=root_run_id,
    )
    return {
        "flow": context.to_dict(),
        "root_run_correlation": context.correlation(),
        "audit_path": str(client.audit_path),
    }
