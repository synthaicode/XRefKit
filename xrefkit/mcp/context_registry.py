from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


REUSE_SAME_VERSION_REASON = "same_xid_version_already_visible_in_active_context"
VERSION_CHANGE_REASON = "same_xid_different_content_hash_visible_in_active_context"


@dataclass(frozen=True)
class XidContextKey:
    repository_fingerprint: str
    xid: str
    content_hash: str

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "XidContextKey":
        try:
            return cls(
                repository_fingerprint=str(document["repository_fingerprint"]),
                xid=str(document["xid"]),
                content_hash=str(document["content_hash"]),
            )
        except KeyError as exc:
            raise ValueError(
                "XID context documents must include repository_fingerprint, xid, and content_hash"
            ) from exc


@dataclass
class XidContextEntry:
    key: XidContextKey
    visible_in_active_context: bool = False
    injected_turns: list[str] = field(default_factory=list)
    last_injected_turn: str | None = None
    reuse_reasons: list[str] = field(default_factory=list)
    context_entry_id: str | None = None
    materialized_count: int = 0


class SessionXidContextRegistry:
    """Tracks which XID document bodies are visible in one client session."""

    def __init__(self) -> None:
        self._entries: dict[XidContextKey, XidContextEntry] = {}
        self._entry_sequence = 0
        self.version_changes: list[dict[str, str]] = []

    def register_materialized(self, document: dict[str, Any]) -> XidContextEntry:
        key = XidContextKey.from_document(document)
        entry = self._entries.get(key)
        if entry is None:
            entry = XidContextEntry(key=key)
            self._entries[key] = entry
        entry.materialized_count += 1
        return entry

    def should_inject_body(
        self,
        document: dict[str, Any],
        active_task: str,
        active_workflow: dict[str, Any] | str | None = None,
        active_skill: dict[str, Any] | str | None = None,
    ) -> bool:
        key = XidContextKey.from_document(document)
        entry = self._entries.get(key)
        if entry and entry.visible_in_active_context:
            return False
        if not document.get("content"):
            return False
        return _context_requires_document(
            key.xid,
            active_task,
            active_workflow,
            active_skill,
        )

    def mark_injected(
        self,
        document: dict[str, Any],
        turn_id: str,
        context_entry_id: str | None = None,
    ) -> XidContextEntry:
        entry = self.register_materialized(document)
        entry.visible_in_active_context = True
        entry.injected_turns.append(str(turn_id))
        entry.last_injected_turn = str(turn_id)
        if context_entry_id is not None:
            entry.context_entry_id = context_entry_id
        elif entry.context_entry_id is None:
            self._entry_sequence += 1
            entry.context_entry_id = f"xid-context-{self._entry_sequence}"
        return entry

    def reference_existing(self, document: dict[str, Any], reason: str) -> dict[str, str]:
        entry = self.register_materialized(document)
        if reason not in entry.reuse_reasons:
            entry.reuse_reasons.append(reason)
        key = entry.key
        result = {
            "repository_fingerprint": key.repository_fingerprint,
            "xid": key.xid,
            "content_hash": key.content_hash,
            "mode": "reuse_existing_session_context",
            "reason": reason,
        }
        if entry.context_entry_id:
            result["context_entry_id"] = entry.context_entry_id
        return result

    def mark_context_compacted(
        self,
        documents: list[dict[str, Any]] | None = None,
    ) -> None:
        if documents is None:
            for entry in self._entries.values():
                entry.visible_in_active_context = False
            return
        for document in documents:
            entry = self._entries.get(XidContextKey.from_document(document))
            if entry is not None:
                entry.visible_in_active_context = False

    def handle_version_change(
        self,
        document: dict[str, Any],
        action: str = "replaced",
    ) -> list[dict[str, str]]:
        key = XidContextKey.from_document(document)
        changes: list[dict[str, str]] = []
        for entry_key, entry in list(self._entries.items()):
            if (
                entry_key.repository_fingerprint == key.repository_fingerprint
                and entry_key.xid == key.xid
                and entry_key.content_hash != key.content_hash
                and entry.visible_in_active_context
            ):
                if action == "replaced":
                    entry.visible_in_active_context = False
                change = {
                    "repository_fingerprint": key.repository_fingerprint,
                    "xid": key.xid,
                    "old_content_hash": entry_key.content_hash,
                    "new_content_hash": key.content_hash,
                    "action": action,
                    "reason": VERSION_CHANGE_REASON,
                }
                self.version_changes.append(change)
                changes.append(change)
        return changes

    def entry_for(self, document: dict[str, Any]) -> XidContextEntry | None:
        return self._entries.get(XidContextKey.from_document(document))


class PromptContextAssembler:
    def __init__(self, registry: SessionXidContextRegistry | None = None) -> None:
        self.registry = registry or SessionXidContextRegistry()

    def assemble(
        self,
        documents: list[dict[str, Any]],
        *,
        turn_id: str,
        active_task: str,
        active_workflow: dict[str, Any] | str | None = None,
        active_skill: dict[str, Any] | str | None = None,
    ) -> dict[str, Any]:
        prompt_items: list[dict[str, Any]] = []
        trace = {
            "turn_id": str(turn_id),
            "active_task": active_task,
            "injected_xids": [],
            "reused_xids": [],
            "version_changes": [],
        }

        for document in documents:
            self.registry.register_materialized(document)
            visible_entry = self.registry.entry_for(document)
            if visible_entry and visible_entry.visible_in_active_context:
                reuse = self.registry.reference_existing(
                    document,
                    REUSE_SAME_VERSION_REASON,
                )
                prompt_items.append(reuse)
                trace["reused_xids"].append(reuse)
                continue

            version_changes = self.registry.handle_version_change(document)
            trace["version_changes"].extend(version_changes)

            if self.registry.should_inject_body(
                document,
                active_task,
                active_workflow,
                active_skill,
            ):
                entry = self.registry.mark_injected(document, str(turn_id))
                item = _body_prompt_item(document, entry.context_entry_id)
                prompt_items.append(item)
                trace["injected_xids"].append(
                    {
                        "repository_fingerprint": document["repository_fingerprint"],
                        "xid": document["xid"],
                        "content_hash": document["content_hash"],
                        "reason": "body_required_by_active_context",
                    }
                )
                continue

            prompt_items.append(_metadata_prompt_item(document))

        return {"prompt_items": prompt_items, "trace": trace}


def _metadata_prompt_item(document: dict[str, Any]) -> dict[str, Any]:
    item = {
        "mode": "metadata_only",
        "xid": document.get("xid"),
        "title": document.get("title"),
        "summary": document.get("summary"),
        "layer": document.get("layer"),
        "required_at_init": document.get("required_at_init"),
        "content_hash": document.get("content_hash"),
        "links": document.get("links", []),
    }
    for field_name in ["cache_status", "client_cache_status"]:
        if field_name in document:
            item[field_name] = document[field_name]
    return item


def _body_prompt_item(
    document: dict[str, Any],
    context_entry_id: str | None,
) -> dict[str, Any]:
    item = _metadata_prompt_item(document)
    item["mode"] = "body"
    item["content"] = document["content"]
    if context_entry_id:
        item["context_entry_id"] = context_entry_id
    return item


def _context_requires_document(
    xid: str,
    active_task: str,
    active_workflow: dict[str, Any] | str | None,
    active_skill: dict[str, Any] | str | None,
) -> bool:
    task = active_task.lower()
    if xid.lower() in task:
        return True
    return _context_declares_xid(active_workflow, xid) or _context_declares_xid(
        active_skill,
        xid,
    )


def _context_declares_xid(context: dict[str, Any] | str | None, xid: str) -> bool:
    if context is None:
        return False
    if isinstance(context, str):
        return xid in context
    return _contains_xid(context, xid)


def _contains_xid(value: Any, xid: str) -> bool:
    if isinstance(value, str):
        return value == xid or xid in value
    if isinstance(value, dict):
        return any(_contains_xid(item, xid) for item in value.values())
    if isinstance(value, list | tuple | set):
        return any(_contains_xid(item, xid) for item in value)
    return False
