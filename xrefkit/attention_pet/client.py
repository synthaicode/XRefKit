"""Small client used by provider adapters to talk to the local Pet."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .client_protocol import ClientState, PROTOCOL_VERSION, SERVICE_NAME


class ClientProtocolError(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class AttentionPetClient:
    def __init__(self, endpoint: str, token: str, *, instance_id: str | None = None,
                 timeout: float = 2.0):
        parsed = urlsplit(endpoint)
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port
                or parsed.path not in {"", "/"} or parsed.username or parsed.password
                or parsed.query or parsed.fragment):
            raise ValueError("Attention Pet endpoint must be an explicit 127.0.0.1 HTTP port")
        if not token:
            raise ValueError("write token is required")
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.expected_instance_id = instance_id
        self.timeout = timeout
        self.hello: dict | None = None
        self.opener = build_opener(ProxyHandler({}), _NoRedirect())

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
        try:
            with self.opener.open(Request(self.endpoint + path, data, headers, method=method),
                                  timeout=self.timeout) as response:
                if response.headers.get_content_type() != "application/json":
                    raise ClientProtocolError("Attention Pet returned a non-JSON response")
                payload = response.read(65_537)
                if len(payload) > 65_536:
                    raise ClientProtocolError("Attention Pet response is too large")
                value = json.loads(payload)
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ClientProtocolError(f"Attention Pet request failed: {type(exc).__name__}") from exc
        if not isinstance(value, dict):
            raise ClientProtocolError("Attention Pet returned an invalid response")
        return value

    def handshake(self) -> dict:
        value = self._request("GET", "/api/client/handshake")
        if value.get("service") != SERVICE_NAME:
            raise ClientProtocolError("the loopback service is not Attention Pet")
        if value.get("protocolVersion") != PROTOCOL_VERSION:
            raise ClientProtocolError("Attention Pet protocol is incompatible")
        if self.expected_instance_id and value.get("instanceId") != self.expected_instance_id:
            raise ClientProtocolError("Attention Pet instance does not match the launched process")
        capabilities = value.get("capabilities")
        if not isinstance(capabilities, list) or "active-session" not in capabilities:
            raise ClientProtocolError("Attention Pet does not support active-session notifications")
        self.hello = value
        return value

    def activate(self, state: ClientState) -> dict:
        hello = self.hello or self.handshake()
        value = self._request("POST", "/api/active-session", state.model_dump())
        if (value.get("accepted") is not True
                or value.get("instanceId") != hello.get("instanceId")
                or value.get("activeSessionId") != state.sessionId
                or value.get("activationRevision") != state.activationRevision):
            raise ClientProtocolError("Attention Pet did not acknowledge the active session")
        return value
