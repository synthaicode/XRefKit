"""python -m xrefkit.attention_pet [serve|evaluate]."""
import argparse
import json
import os
import platform
from pathlib import Path

from .evaluator import Weights, evaluate, evaluate_fit
from .profiles import PROFILES, DEPTHS
from .model import Conversation, WorkingSet, extract


def main(argv=None):
    parser = argparse.ArgumentParser(description="Attention Pet: experimental model and cost fit")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8769)
    serve.add_argument("--session", type=Path)
    serve.add_argument("--thread-id", default=os.environ.get("CODEX_THREAD_ID", ""))
    serve.add_argument("--manual", action="store_true", help="use manually supplied work data instead of a Codex chat")
    serve.add_argument("--client", action="store_true", help="accept authenticated same-host client-state notifications")
    serve.add_argument("--weights", type=Path)
    check = sub.add_parser("evaluate")
    check.add_argument("input", type=Path)
    check.add_argument("--conversation", action="store_true")
    check.add_argument("--weights", type=Path)
    check.add_argument("--model", choices=PROFILES)
    check.add_argument("--reasoning", choices=DEPTHS, default="standard")
    args = parser.parse_args(argv)
    weights = Weights(**json.loads(args.weights.read_text(encoding="utf-8"))) if args.weights else Weights()
    if args.command == "evaluate":
        data = json.loads(args.input.read_text(encoding="utf-8"))
        ws = extract(Conversation.model_validate(data)) if args.conversation else WorkingSet.model_validate(data)
        state = evaluate(ws, weights=weights)
        result = {"state": state, "fit": evaluate_fit(state, args.model, args.reasoning)} if args.model else state
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    from .server import make_server
    from .store import Store
    if args.manual and args.client:
        parser.error("--manual and --client cannot be used together")
    source = None
    if args.thread_id and not args.manual and not args.client:
        from .codex_session import CodexSessionSource, find_rollout
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        source = CodexSessionSource(find_rollout(args.thread_id, codex_home), args.thread_id)
    if args.client:
        from .client_protocol import ClientStateSource, PROTOCOL_VERSION, SERVICE_NAME
        if args.session:
            client_directory = args.session
        elif platform.system() == "Windows" and os.environ.get("LOCALAPPDATA"):
            client_directory = Path(os.environ["LOCALAPPDATA"]) / "XRefKit" / "AttentionPet" / "sessions"
        else:
            client_directory = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "xrefkit" / "attention-pet" / "sessions"
        source = ClientStateSource(client_directory, weights)
    session_path = (None if args.client else args.session or
                    (Path("work/attention-pet") / f"chat-projection-v1-{args.thread_id}.json"
                     if source else Path("work/attention-pet/session.json")))
    server, url = make_server(Store(session_path, weights), args.port, source)
    if args.client:
        print(json.dumps({"service": SERVICE_NAME, "endpoint": url.rstrip("/"),
                          "protocolVersion": PROTOCOL_VERSION, "instanceId": server.instance_id,
                          "writeToken": server.write_token}, separators=(",", ":")), flush=True)
    else:
        print(url, flush=True)
    if args.manual:
        print(f"Write API Authorization: Bearer {server.write_token}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    main()
