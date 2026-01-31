from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from fm.xref import MANAGED_FRAGMENT_RE, WIKI_XREF_RE, XrefConfig, build_index


@dataclass(frozen=True)
class PackedDoc:
    xid: str
    path: str
    title: str | None
    bytes_included: int


def _extract_referenced_xids(text: str) -> set[str]:
    xids = set(MANAGED_FRAGMENT_RE.findall(text))
    xids.update(WIKI_XREF_RE.findall(text))
    return xids


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _build_pack_text(
    *,
    root: Path,
    ordered_xids: list[str],
    index,
    per_doc_bytes: int,
    max_bytes: int,
) -> tuple[str, list[PackedDoc]]:
    parts: list[str] = []
    packed: list[PackedDoc] = []

    header = [
        "# Context Pack",
        "",
        f"- root: {root.as_posix()}",
        f"- docs: {len(ordered_xids)}",
        "",
    ]
    parts.append("\n".join(header))

    total = sum(len(p.encode("utf-8")) for p in parts)
    for xid in ordered_xids:
        info = index.get(xid)
        if info is None:
            continue
        rel = str(info.path.relative_to(root)).replace("\\", "/")
        title = info.title

        text = _read_text(info.path)
        blob = text.encode("utf-8")
        truncated = blob[:per_doc_bytes].decode("utf-8", errors="ignore")

        section = [
            "---",
            f"## {title or xid}",
            f"- xid: {xid}",
            f"- path: {rel}",
            "",
            truncated.rstrip("\n"),
            "",
        ]
        section_text = "\n".join(section)
        section_bytes = len(section_text.encode("utf-8"))
        if total + section_bytes > max_bytes:
            break
        parts.append(section_text)
        total += section_bytes
        packed.append(
            PackedDoc(
                xid=xid,
                path=rel,
                title=title,
                bytes_included=len(truncated.encode("utf-8")),
            )
        )

    return "\n".join(parts).rstrip() + "\n", packed


def ctx_pack(
    cfg: XrefConfig,
    *,
    seeds: list[str],
    depth: int,
    max_bytes: int,
    per_doc_bytes: int,
) -> dict[str, object]:
    root = cfg.resolved_root()
    index, issues = build_index(cfg)

    visited: set[str] = set()
    frontier: set[str] = {s for s in seeds if s in index}
    ordered: list[str] = []

    for _ in range(max(0, depth) + 1):
        if not frontier:
            break
        next_frontier: set[str] = set()
        for xid in sorted(frontier):
            if xid in visited:
                continue
            visited.add(xid)
            ordered.append(xid)
            text = _read_text(index[xid].path)
            for ref in _extract_referenced_xids(text):
                if ref in index and ref not in visited:
                    next_frontier.add(ref)
        frontier = next_frontier

    pack_text, packed_docs = _build_pack_text(
        root=root,
        ordered_xids=ordered,
        index=index,
        per_doc_bytes=per_doc_bytes,
        max_bytes=max_bytes,
    )

    return {
        "issues": issues,
        "seeds": seeds,
        "depth": depth,
        "docs": [d.__dict__ for d in packed_docs],
        "text": pack_text,
    }


def cmd_ctx(args: argparse.Namespace, cfg: XrefConfig) -> int:
    if args.ctx_cmd != "pack":
        raise ValueError(f"Unknown ctx command: {args.ctx_cmd}")

    result = ctx_pack(
        cfg,
        seeds=list(args.seed or []),
        depth=int(args.depth),
        max_bytes=int(args.max_bytes),
        per_doc_bytes=int(args.per_doc_bytes),
    )

    out_path = Path(args.out).resolve() if args.out else None
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result["text"], encoding="utf-8", newline="\n")

    if args.json:
        if out_path is not None:
            result["out"] = str(out_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["text"], end="")

    return 0

