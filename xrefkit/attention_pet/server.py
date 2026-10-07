"""Loopback-only HTTP adapter with public reads and authenticated writes."""
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import urlsplit, parse_qs

from pydantic import ValidationError

from .model import Conversation, WorkingSet, extract
from .store import Store
from .evaluator import evaluate_fit
from .profiles import PROFILES, DEPTHS, canonical_reasoning
from .client_protocol import ClientState, ClientStateSource, StaleActivation, handshake


def make_server(store: Store, port: int = 0, source=None):
    token = secrets.token_urlsafe(32)
    instance_id = secrets.token_urlsafe(18)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            pass  # Never write imported conversation content or tokens to access logs.

        def reply(self, status, body, content_type="application/json; charset=utf-8"):
            payload = json.dumps(body, ensure_ascii=False, allow_nan=False).encode() if content_type.startswith("application/json") else body
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(payload)

        def allowed(self, *, require_auth=True):
            expected_host = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != expected_host:
                self.reply(403, {"error": "invalid host"})
                return False
            origin = self.headers.get("Origin")
            if origin and origin != f"http://{expected_host}":
                self.reply(403, {"error": "cross-origin request rejected"})
                return False
            if require_auth and not secrets.compare_digest(self.headers.get("Authorization", ""), f"Bearer {token}"):
                self.reply(401, {"error": "write authorization required"})
                return False
            return True

        def selection(self, *, mutating=False):
            query = parse_qs(urlsplit(self.path).query, keep_blank_values=True)
            if set(query) - {"model", "reasoning", "lang"} or any(len(v) != 1 for v in query.values()):
                raise ValueError("invalid fit selection")
            selection = (query.get("model", [""])[0], query.get("reasoning", ["standard"])[0],
                         query.get("lang", ["ja"])[0])
            evaluate_fit(None, *selection[:2], locale=selection[2])
            if mutating and (selection[0] and selection[0] not in PROFILES or
                             selection[1] not in DEPTHS or
                             selection[0] and canonical_reasoning(selection[1]) not in PROFILES[selection[0]].supported_reasoning):
                raise ValueError("unknown execution profile")
            return selection

        def with_fit(self, result, selection, observed=None):
            # In chat-bound mode the observed model is the default. An explicit
            # query is a read-only comparison and never changes the Codex run.
            if observed is not None:
                source_selection, source_status = observed
            elif source:
                source_selection, source_status = source.selection(), source.status()
            else:
                source_selection, source_status = selection[:2], {"mode": "manual"}
            actual_selection = selection[:2] if selection[0] else source_selection
            return {**result, "fit": evaluate_fit(result["state"], *actual_selection,
                                                    locale=selection[2]),
                    "source": source_status}

        def do_GET(self):
            assets = {"/": ("pet.html", "text/html; charset=utf-8"), "/pet.css": ("pet.css", "text/css; charset=utf-8"), "/pet.js": ("pet.js", "text/javascript; charset=utf-8")}
            if self.path in assets:
                name, kind = assets[self.path]
                self.reply(200, files("xrefkit").joinpath("resources", "attention_pet", name).read_bytes(), kind)
            elif urlsplit(self.path).path == "/api/profiles":
                if self.allowed(require_auth=False):
                    self.reply(200, {"models": [{"id": p.id, "label": p.label,
                                                  "reasoning": list(p.supported_reasoning)}
                                                 for p in PROFILES.values()],
                                     "legacyAliases": {"light": "low", "standard": "medium"},
                                     "calibration": "uncalibrated"})
            elif urlsplit(self.path).path == "/api/state":
                if self.allowed(require_auth=False):
                    try:
                        selection = self.selection()
                    except ValueError as exc:
                        self.reply(400, {"error": str(exc)})
                        return
                    try:
                        if isinstance(source, ClientStateSource):
                            result, source_selection, source_status = source.snapshot(store)
                            self.reply(200, self.with_fit(result, selection, (source_selection, source_status)))
                        else:
                            result = source.view(store) if source else store.view()
                            self.reply(200, self.with_fit(result, selection))
                    except (OSError, ValueError):
                        self.reply(503, {"error": "bound chat is temporarily unavailable"})
            elif urlsplit(self.path).path == "/api/client/handshake":
                if self.allowed():
                    self.reply(200, handshake(instance_id))
            else:
                self.reply(404, {"error": "not found"})

        def do_POST(self):
            if not self.allowed():
                return
            try:
                selection = self.selection(mutating=True)
                path = urlsplit(self.path).path
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ValueError("application/json required")
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 2_000_000:
                    raise ValueError("body must be between 1 byte and 2 MB")
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise ValueError("object required")
                if path == "/api/active-session":
                    if not source or not hasattr(source, "activate"):
                        self.reply(409, {"error": "client-state mode is not enabled"})
                        return
                    result = source.activate(ClientState.model_validate(body))
                    self.reply(200, {**result, "instanceId": instance_id})
                    return
                if source:
                    self.reply(409, {"error": "bound chat view is read-only"})
                    return
                if path == "/api/snapshot":
                    result = store.submit(WorkingSet.model_validate(body))
                elif path == "/api/conversation":
                    result = store.submit(extract(Conversation.model_validate(body)))
                elif path == "/api/recover":
                    if set(body) != {"action", "expectedObservedAt"} or not isinstance(body["action"], str) or type(body["expectedObservedAt"]) not in {int, float}:
                        raise ValueError("action and expectedObservedAt required")
                    result = store.recover(body["action"], body["expectedObservedAt"])
                else:
                    self.reply(404, {"error": "not found"})
                    return
                self.reply(200, self.with_fit(result, selection))
            except StaleActivation as exc:
                self.reply(409, {"error": str(exc)})
            except (ValueError, ValidationError, TypeError) as exc:
                # Pydantic errors can contain sensitive input; expose only the class.
                message = "invalid contract; check required fields, references and value types" if isinstance(exc, ValidationError) else str(exc)
                self.reply(400, {"error": message})
            except OSError:
                self.reply(500, {"error": "local persistence failed; previous state preserved"})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.write_token = token
    server.instance_id = instance_id
    return server, f"http://127.0.0.1:{server.server_port}/"
