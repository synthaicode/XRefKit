"""python -m xrefkit.attention_pet [serve|evaluate]."""
import argparse
import json
import os
from pathlib import Path

from .evaluator import Weights, evaluate, evaluate_fit
from .profiles import PROFILES, DEPTHS
from .model import Conversation, WorkingSet, extract


def main():
    parser = argparse.ArgumentParser(description="Attention Pet: experimental model and cost fit")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8769)
    serve.add_argument("--session", type=Path)
    serve.add_argument("--thread-id", default=os.environ.get("CODEX_THREAD_ID", ""))
    serve.add_argument("--manual", action="store_true", help="use manually supplied work data instead of a Codex chat")
    serve.add_argument("--weights", type=Path)
    check = sub.add_parser("evaluate")
    check.add_argument("input", type=Path)
    check.add_argument("--conversation", action="store_true")
    check.add_argument("--weights", type=Path)
    check.add_argument("--model", choices=PROFILES)
    check.add_argument("--reasoning", choices=DEPTHS, default="standard")
    args = parser.parse_args()
    weights = Weights(**json.loads(args.weights.read_text(encoding="utf-8"))) if args.weights else Weights()
    if args.command == "evaluate":
        data = json.loads(args.input.read_text(encoding="utf-8"))
        ws = extract(Conversation.model_validate(data)) if args.conversation else WorkingSet.model_validate(data)
        state = evaluate(ws, weights=weights)
        result = {"state": state, "fit": evaluate_fit(state, args.model, args.reasoning)} if args.model else state
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    from .server import make_server
    from .store import Store
    source = None
    if args.thread_id and not args.manual:
        from .codex_session import CodexSessionSource, find_rollout
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        source = CodexSessionSource(find_rollout(args.thread_id, codex_home), args.thread_id)
    session_path = args.session or (Path("work/attention-pet") / f"chat-projection-v1-{args.thread_id}.json"
                                    if source else Path("work/attention-pet/session.json"))
    server, url = make_server(Store(session_path, weights), args.port, source)
    print(url, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
