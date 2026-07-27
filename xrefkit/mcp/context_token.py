"""Signed, client-carried context for stateless MCP requests."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any


CONTEXT_META_KEY = "io.xrefkit/context_id"


@dataclass(frozen=True)
class ContextClaims:
    context_id: str
    repository_fingerprint: str
    startup_loaded: bool = False
    client_tools_unlocked: bool = False
    run_id: str | None = None
    skill_id: str | None = None
    mcp_session_id: str | None = None
    expires_at: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "repository_fingerprint": self.repository_fingerprint,
            "startup_loaded": self.startup_loaded,
            "client_tools_unlocked": self.client_tools_unlocked,
            "run_id": self.run_id,
            "skill_id": self.skill_id,
            "mcp_session_id": self.mcp_session_id,
            "expires_at": self.expires_at,
        }


class ContextTokenCodec:
    def __init__(self, secret: str, repository_fingerprint: str, *, ttl_seconds: int = 3600) -> None:
        if not secret:
            raise ValueError("context token secret is required")
        self._secret = secret.encode("utf-8")
        self.repository_fingerprint = repository_fingerprint
        self.ttl_seconds = ttl_seconds

    def issue(
        self,
        *,
        startup_loaded: bool = False,
        client_tools_unlocked: bool = False,
        run_id: str | None = None,
        skill_id: str | None = None,
        mcp_session_id: str | None = None,
        context_id: str | None = None,
    ) -> str:
        claims = ContextClaims(
            context_id=context_id or f"xc_{uuid.uuid4().hex}",
            repository_fingerprint=self.repository_fingerprint,
            startup_loaded=startup_loaded,
            client_tools_unlocked=client_tools_unlocked,
            run_id=run_id,
            skill_id=skill_id,
            mcp_session_id=mcp_session_id,
            expires_at=int(time.time()) + self.ttl_seconds,
        )
        body = _encode(claims.to_dict())
        return f"v1.{body}.{self._signature(body)}"

    def verify(self, token: str) -> ContextClaims:
        try:
            version, body, signature = str(token).split(".", 2)
            if version != "v1" or not hmac.compare_digest(signature, self._signature(body)):
                raise ValueError("invalid context token signature")
            payload = json.loads(_decode(body))
            if payload["repository_fingerprint"] != self.repository_fingerprint:
                raise ValueError("context token repository mismatch")
            if int(payload["expires_at"]) < int(time.time()):
                raise ValueError("context token expired")
            return ContextClaims(**payload)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("invalid context token") from exc

    def refresh(self, claims: ContextClaims, **updates: Any) -> str:
        values = claims.to_dict()
        values.update(updates)
        values.pop("context_id", None)
        return self.issue(context_id=claims.context_id, **{k: values[k] for k in (
            "startup_loaded", "client_tools_unlocked", "run_id", "skill_id", "mcp_session_id"
        )})

    def _signature(self, body: str) -> str:
        return _b64(hmac.new(self._secret, body.encode("ascii"), hashlib.sha256).digest())


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _encode(value: dict[str, Any]) -> str:
    return _b64(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _decode(value: str) -> str:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode("utf-8")
