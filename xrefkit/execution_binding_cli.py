"""CLI boundary for explicit workflow binding generation."""
import json
from pathlib import Path

from xrefkit.execution_binding import build_execution_binding


def cmd_execution_binding(args):
    try:
        with Path(args.request).open("rb") as stream:
            raw = stream.read(256_001)
        if len(raw) > 256_000:
            raise ValueError("request exceeds byte limit")
        request = json.loads(raw.decode("utf-8-sig"))
        result = build_execution_binding(Path(args.log), request)
    except (OSError, UnicodeError, ValueError, TimeoutError) as exc:
        print(json.dumps({"ok": False, "state": "blocked", "errors": [str(exc)]}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
