"""Render verified GitHub release metadata into an already-built site."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
from urllib.parse import quote


def render_release(site: Path, release: dict, repository: str) -> None:
    """Fail before writing if the release or expected page markers are invalid."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid repository")
    tag = release.get("tag_name", "")
    if not isinstance(tag, str) or not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("expected a stable XRefKit version tag")
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("release must be published and stable")
    published = release.get("published_at")
    if not isinstance(published, str):
        raise ValueError("missing release publication date")
    date = datetime.fromisoformat(published.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("publication date must include a timezone")
    date = date.astimezone(timezone.utc)
    base = f"https://github.com/{repository}"
    url = f"{base}/releases/tag/{quote(tag, safe='')}"
    if release.get("html_url") != url:
        raise ValueError("release URL does not match repository and tag")
    label = f"{date:%B} {date.day}, {date.year}"
    fragment = (
        f'Latest published release: <a href="{html.escape(url, quote=True)}">{tag}</a>'
        f' (<time datetime="{date:%Y-%m-%d}">{label}</time>).'
    )
    replacements = [
        (site / "index.html", r"<!-- release-metadata:start -->.*?<!-- release-metadata:end -->",
         f"<!-- release-metadata:start -->{fragment}<!-- release-metadata:end -->"),
        (site / "common/index.html", r'(<a data-release-source href=")[^"]+("[^>]*>)',
         rf'\g<1>{base}/tree/{tag}\g<2>'),
    ]
    pending = []
    for path, pattern, replacement in replacements:
        source = path.read_text(encoding="utf-8")
        result, count = re.subn(pattern, replacement, source, flags=re.DOTALL)
        if count != 1:
            raise ValueError(f"expected exactly one release marker in {path}")
        pending.append((path, result))
    for path, result in pending:
        path.write_bytes(result.replace("\n", "\r\n").encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--release-json", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    try:
        release = json.loads(args.release_json.read_text(encoding="utf-8-sig"))
        if not isinstance(release, dict):
            raise ValueError("expected one GitHub release object")
        render_release(args.site, release, args.repository)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"Release metadata update failed: {exc}\n")
    print(f"Rendered release {release['tag_name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
