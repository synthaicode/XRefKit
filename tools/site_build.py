"""Build or verify the generated public site from its declared source manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_site(root: Path, manifest_path: Path, output: Path, *, check: bool) -> dict[str, object]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema") != "xrefkit.site/v1":
        raise ValueError("unsupported site manifest")
    mismatches: list[str] = []
    written: list[str] = []
    items = list(data.get("files", []))
    for tree in data.get("trees", []):
        source_root = root / tree["source"]
        if not source_root.is_dir():
            mismatches.append(f"missing source tree: {tree['source']}")
            continue
        includes = tree.get("include", ["*", "**/*"])
        for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
            relative = source.relative_to(source_root).as_posix()
            if not any(Path(relative).match(pattern) for pattern in includes):
                continue
            items.append(
                {
                    "source": f"{tree['source'].rstrip('/')}/{relative}",
                    "target": f"{tree['target'].rstrip('/')}/{relative}".lstrip("/"),
                }
            )

    if not check:
        base = data.get("base_tree")
        if base:
            base_root = root / base
            if output.resolve() == base_root.resolve():
                raise ValueError("build output must differ from base_tree")
            shutil.copytree(
                base_root,
                output,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("sources", "source_manifest.json"),
            )

    for item in items:
        source = root / item["source"]
        target = output / item["target"]
        if not source.is_file():
            mismatches.append(f"missing source: {item['source']}")
            continue
        if check:
            if not target.is_file() or _hash(source) != _hash(target):
                mismatches.append(str(item["target"]))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            written.append(str(item["target"]))
    if output.is_dir():
        mismatches.extend(_broken_local_links(output))
    return {"ok": not mismatches, "mismatches": sorted(set(mismatches)), "written": written}


_LINK_RE = re.compile(r'(?:href|src)=["\']([^"\']+)["\']', re.IGNORECASE)


def _broken_local_links(site_root: Path) -> list[str]:
    broken: list[str] = []
    for page in sorted(site_root.rglob("*.html")):
        if "sources" in page.relative_to(site_root).parts:
            continue
        text = page.read_text(encoding="utf-8", errors="replace")
        for link in _LINK_RE.findall(text):
            if link.startswith(("http://", "https://", "mailto:", "#", "data:", "javascript:")):
                continue
            clean = link.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            target = (site_root / clean.lstrip("/")) if clean.startswith("/") else (page.parent / clean)
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                broken.append(f"broken link: {page.relative_to(site_root).as_posix()} -> {link}")
    return broken


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest", default="site/source_manifest.json")
    parser.add_argument("--output", default="site")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        result = build_site(root, root / args.manifest, root / args.output, check=args.check)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"ok": False, "mismatches": [str(exc)], "written": []}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("ok" if result["ok"] else "failed")
        for mismatch in result["mismatches"]:
            print(f"- {mismatch}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
