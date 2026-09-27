"""Provider-neutral same-host client protocol for Attention Pet."""

import hashlib
import threading
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .model import Contract, WorkingSet
from .store import Store


PROTOCOL_VERSION = "attention-pet-client-v1"
SERVICE_NAME = "xrefkit-attention-pet"


class ClientCapabilities(Contract):
    activeSessionChanged: bool
    promptSubmitted: bool
    modelSelected: bool
    fullConversationAccess: bool = False


class ClientState(Contract):
    protocolVersion: Literal["attention-pet-client-v1"]
    provider: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    clientInstanceId: str = Field(min_length=1, max_length=100)
    sessionId: str = Field(min_length=1, max_length=100)
    activationRevision: int = Field(ge=0)
    observedAt: float = Field(ge=0, allow_inf_nan=False)
    model: str = Field(default="", max_length=200)
    reasoning: str = Field(default="", max_length=80)
    capabilities: ClientCapabilities
    workingSet: WorkingSet

    @model_validator(mode="after")
    def working_set_matches_session(self):
        if self.workingSet.contextId != self.sessionId:
            raise ValueError("workingSet.contextId must match sessionId")
        if self.workingSet.observedAt != self.observedAt:
            raise ValueError("workingSet.observedAt must match observedAt")
        return self


class StaleActivation(ValueError):
    """The client tried to replace a newer active-session notification."""


class ClientStateSource:
    """Keep independent session stores and expose the client's active one."""

    def __init__(self, directory: Path, weights):
        self.directory = directory
        self.weights = weights
        self.lock = threading.RLock()
        self.stores: dict[tuple[str, str, str], Store] = {}
        self.active: tuple[str, str, str] | None = None
        self.states: dict[tuple[str, str, str], ClientState] = {}
        self.last_revision: dict[tuple[str, str], int] = {}

    def _store(self, key: tuple[str, str, str]) -> Store:
        if key not in self.stores:
            digest = hashlib.sha256("\0".join(key).encode()).hexdigest()
            self.stores[key] = Store(self.directory / f"{digest}.json", self.weights)
        return self.stores[key]

    def activate(self, state: ClientState) -> dict:
        client = (state.provider, state.clientInstanceId)
        key = (*client, state.sessionId)
        with self.lock:
            previous = self.last_revision.get(client)
            if previous is not None and state.activationRevision < previous:
                raise StaleActivation("activationRevision is older than the accepted revision")
            if previous == state.activationRevision:
                if self.active == key and self.states.get(key) == state:
                    return self.acknowledgement(state)
                raise StaleActivation("activationRevision was already used for different state")
            self._store(key).submit(state.workingSet)
            self.states[key] = state
            self.last_revision[client] = state.activationRevision
            self.active = key
            return self.acknowledgement(state)

    def acknowledgement(self, state: ClientState) -> dict:
        return {
            "accepted": True,
            "activeSessionId": state.sessionId,
            "activationRevision": state.activationRevision,
        }

    def view(self, _fallback_store: Store) -> dict:
        with self.lock:
            return self._store(self.active).view() if self.active else _fallback_store.view()

    def selection(self) -> tuple[str, str]:
        with self.lock:
            state = self.states.get(self.active) if self.active else None
            if not state:
                return "", "standard"
            family = state.model.rsplit("-", 1)[-1]
            model = family if state.model.startswith("gpt-") and family in {"luna", "terra", "sol", "astra"} else ""
            depth = {"none": "light", "minimal": "light", "low": "light", "medium": "standard",
                     "high": "high", "xhigh": "high", "max": "high", "ultra": "high"}.get(state.reasoning)
            return (model, depth) if model and depth else ("", "standard")

    def status(self) -> dict:
        with self.lock:
            state = self.states.get(self.active) if self.active else None
            if not state:
                return {"mode": "client-state", "connected": False}
            return {
                "mode": "client-state",
                "connected": True,
                "provider": state.provider,
                "clientInstanceId": state.clientInstanceId,
                "sessionId": state.sessionId,
                "activationRevision": state.activationRevision,
                "model": state.model,
                "effort": state.reasoning,
                "profile": self.selection()[0],
                "reasoning": self.selection()[1],
                "capabilities": state.capabilities.model_dump(),
                "coverage": state.workingSet.coverage,
            }


def handshake(instance_id: str) -> dict:
    return {
        "service": SERVICE_NAME,
        "protocolVersion": PROTOCOL_VERSION,
        "instanceId": instance_id,
        "capabilities": ["active-session", "working-set-snapshot"],
        "writeAuthentication": "bearer",
        "hostScope": "loopback",
    }
