"""Local, read-only projection of one explicitly bound Codex chat.

The rollout JSONL is an application implementation detail, so this adapter is
best effort. It never persists message text or interprets an assistant reply as
proof that the task succeeded or failed.
"""

import json
import re
import threading
from collections import deque
from datetime import datetime
from pathlib import Path

from .model import Edge, Item, WorkingSet


_THREAD_ID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
_AMBIENT = re.compile(r"<in-app-browser-context\b[^>]*>.*?</in-app-browser-context>", re.S)
_REFERENCE = re.compile(r"(?:^|\s)(?:この|これ|それ|その|同じ|つづけて|続けて)")
_CONSTRAINT = ("不要", "削除", "しない", "なくす", "やめ", "違う", "おかしい", "修正", "変更")
_MODEL_SUFFIX = {"luna": "luna", "terra": "terra", "sol": "sol", "astra": "astra"}
_DEPTH = {"none": "light", "minimal": "light", "low": "light", "medium": "standard",
          "high": "high", "xhigh": "high", "max": "high", "ultra": "high"}


def find_rollout(thread_id: str, codex_home: Path) -> Path:
    """Bind a known chat ID; never guess the active chat from recent files."""
    if not _THREAD_ID.fullmatch(thread_id):
        raise ValueError("invalid Codex thread id")
    matches = list((codex_home / "sessions").rglob(f"*{thread_id}.jsonl"))
    if len(matches) != 1:
        raise FileNotFoundError("exactly one local rollout is required for the bound chat")
    return matches[0]


def _request(payload: dict) -> tuple[str, bool]:
    chunks = [part.get("text", "") for part in payload.get("content", [])
              if part.get("type") == "input_text"]
    text = _AMBIENT.sub("", "\n".join(chunks))
    if "## My request:" in text:
        text = text.rsplit("## My request:", 1)[1]
    text = text.strip()
    if text.startswith("# AGENTS.md instructions for"):
        return "", False
    if text:
        return text, False
    return "", "Pasted text contains the user's request" in "\n".join(chunks)


def _timestamp(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


class CodexSessionSource:
    def __init__(self, path: Path, thread_id: str):
        if not _THREAD_ID.fullmatch(thread_id):
            raise ValueError("invalid Codex thread id")
        self.path = path
        self.thread_id = thread_id
        self.offset = 0
        self.messages = deque(maxlen=100)
        self.seen = set()
        self.model = ""
        self.effort = ""
        self.changed = False
        self.lock = threading.RLock()

    def _ingest(self, entry: dict):
        payload = entry.get("payload", {})
        if entry.get("type") == "turn_context":
            self.model = payload.get("model") or ""
            self.effort = payload.get("effort") or ""
        if not (entry.get("type") == "response_item" and
                payload.get("type") == "message" and payload.get("role") == "user"):
            return
        message_id = payload.get("id")
        if not isinstance(message_id, str) or message_id in self.seen:
            return
        request, opaque = _request(payload)
        if not request and not opaque:
            return
        self.seen.add(message_id)
        kind = "constraint" if any(word in request for word in _CONSTRAINT) else "goal"
        references_previous = bool(_REFERENCE.search(request))
        self.messages.append((message_id, _timestamp(entry["timestamp"]), kind, opaque,
                              references_previous))
        self.changed = True

    def scan(self):
        with self.lock:
            size = self.path.stat().st_size
            if size < self.offset:
                raise OSError("bound Codex chat log was truncated")
            with self.path.open("r", encoding="utf-8") as stream:
                stream.seek(self.offset)
                while True:
                    start = stream.tell()
                    line = stream.readline()
                    if not line or not line.endswith("\n"):
                        stream.seek(start)
                        break
                    try:
                        self._ingest(json.loads(line))
                    except (ValueError, KeyError, TypeError):
                        # A malformed record provides no evidence. Keep the
                        # cursor moving so a single bad event cannot freeze UI.
                        pass
                self.offset = stream.tell()

    def selection(self) -> tuple[str, str]:
        family = self.model.rsplit("-", 1)[-1]
        profile = _MODEL_SUFFIX.get(family, "") if self.model.startswith("gpt-") else ""
        depth = _DEPTH.get(self.effort)
        return (profile, depth) if profile and depth else ("", "standard")

    def status(self) -> dict:
        profile, depth = self.selection()
        return {"mode": "codex-chat", "threadId": self.thread_id,
                "observedUserTurns": len(self.messages), "model": self.model,
                "effort": self.effort, "profile": profile, "reasoning": depth,
                "coverage": "partial"}

    def sync(self, store):
        with self.lock:
            self.scan()
            if not self.changed or not self.messages:
                return
            items = []
            edges = []
            previous = None
            for message_id, _, kind, opaque, references_previous in self.messages:
                item_id = "u-" + message_id[:95]
                items.append(Item(id=item_id, kind=kind,
                                  text="添付内容を伴う依頼（内容未解析）" if opaque else "チャット内の依頼（本文は保存しない）",
                                  source=message_id))
                if previous and references_previous:
                    edges.append(Edge(source=previous, target=item_id,
                                      evidence="明示的な前方参照の手掛かり。意味上の依存は未確認"))
                previous = item_id
            observed_at = self.messages[-1][1]
            ws = WorkingSet(taskId="codex-" + self.thread_id,
                            contextId=self.thread_id, observedAt=observed_at,
                            coverage="partial", items=items, dependencies=edges,
                            observations=[])
            store.submit(ws)
            self.changed = False
