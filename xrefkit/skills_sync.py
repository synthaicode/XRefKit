"""Synchronize released Skill/Knowledge bundles into an XRefKit repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


DEFAULT_SOURCE_REPOSITORY = "synthaicode/XRefKit"
DEFAULT_GITHUB_API = "https://api.github.com"
ASSET_PREFIX = "xrefkit-skills-"
VERSION_SUFFIX_RE = re.compile(r"^(?P<bundle>.+)-(?P<version>\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?)$")
ALLOWED_ROOTS = {"skills", "knowledge", "review_axes", "schemas"}


@dataclass(frozen=True)
class SyncResult:
    bundle: str
    release: str
    asset: str
    sha256: str
    files: tuple[str, ...]
    changed: bool
    dry_run: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "bundle": self.bundle,
            "release": self.release,
            "asset": self.asset,
            "sha256": self.sha256,
            "files": list(self.files),
            "changed": self.changed,
            "dry_run": self.dry_run,
        }


def _github_json(url: str) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "xrefkit-skill-sync",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise RuntimeError(f"could not read GitHub release metadata: {url}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"GitHub release metadata was not an object: {url}")
    return payload


def _release(source_repository: str, release: str) -> dict[str, object]:
    encoded_repo = urllib.parse.quote(source_repository, safe="/")
    if release == "latest":
        url = f"{DEFAULT_GITHUB_API}/repos/{encoded_repo}/releases/latest"
    else:
        encoded_release = urllib.parse.quote(release, safe="")
        url = f"{DEFAULT_GITHUB_API}/repos/{encoded_repo}/releases/tags/{encoded_release}"
    return _github_json(url)


def _assets(release: dict[str, object]) -> list[dict[str, object]]:
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise RuntimeError("GitHub release has no assets list")
    return [item for item in assets if isinstance(item, dict)]


def _asset_for_bundle(release: dict[str, object], bundle: str) -> dict[str, object]:
    expected_prefix = f"{ASSET_PREFIX}{bundle}-"
    candidates = [
        asset
        for asset in _assets(release)
        if isinstance(asset.get("name"), str)
        and asset["name"].startswith(expected_prefix)
        and asset["name"].endswith(".zip")
    ]
    if len(candidates) != 1:
        names = ", ".join(str(item.get("name")) for item in candidates) or "none"
        raise RuntimeError(f"expected one release asset for bundle {bundle}; found: {names}")
    return candidates[0]


def _download_asset(asset: dict[str, object]) -> tuple[str, bytes]:
    name = asset.get("name")
    url = asset.get("browser_download_url")
    if not isinstance(name, str) or not isinstance(url, str):
        raise RuntimeError("GitHub release asset has no usable name or download URL")
    request = urllib.request.Request(url, headers={"User-Agent": "xrefkit-skill-sync"})
    try:
        with urllib.request.urlopen(request) as response:
            return name, response.read()
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise RuntimeError(f"could not download release asset: {name}") from exc


def _safe_zip_extract(data: bytes, destination: Path) -> None:
    with zipfile.ZipFile(__import__("io").BytesIO(data)) as archive:
        for member in archive.infolist():
            relative = PurePosixPath(member.filename)
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"unsafe path in Skill bundle: {member.filename}")
            target = (destination / Path(*relative.parts)).resolve()
            target.relative_to(destination.resolve())
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))


def _bundle_root(extracted: Path) -> Path:
    if any((extracted / name).is_dir() for name in ALLOWED_ROOTS):
        return extracted
    children = [path for path in extracted.iterdir() if path.is_dir()]
    if len(children) == 1 and any((children[0] / name).is_dir() for name in ALLOWED_ROOTS):
        return children[0]
    raise RuntimeError("Skill bundle must contain skills/ or knowledge/ at its root")


def _bundle_files(root: Path) -> list[tuple[Path, Path]]:
    files: list[tuple[Path, Path]] = []
    for dirname in sorted(ALLOWED_ROOTS):
        base = root / dirname
        if not base.is_dir():
            continue
        for source in sorted(path for path in base.rglob("*") if path.is_file()):
            files.append((source, Path(dirname) / source.relative_to(base)))
    manifest = root / "package_manifest.yaml"
    if manifest.is_file():
        files.append((manifest, Path("package_manifest.yaml")))
    if not files:
        raise RuntimeError("Skill bundle contains no files under skills/ or knowledge/")
    return files


def _state_path(repo: Path, bundle: str) -> Path:
    return repo / ".xrefkit" / "skill-sync" / f"{bundle}.json"


def sync_bundle(
    *,
    repo: Path,
    source_repository: str,
    bundle: str,
    release: str = "latest",
    force: bool = False,
    dry_run: bool = False,
) -> SyncResult:
    repo = repo.resolve()
    if not repo.is_dir():
        raise FileNotFoundError(f"XRefKit repository not found: {repo}")
    release_payload = _release(source_repository, release)
    asset = _asset_for_bundle(release_payload, bundle)
    asset_name, data = _download_asset(asset)
    digest = hashlib.sha256(data).hexdigest()
    release_name = str(release_payload.get("tag_name") or release)

    with tempfile.TemporaryDirectory(prefix="xrefkit-skill-sync-") as temp_dir:
        extracted = Path(temp_dir) / "bundle"
        extracted.mkdir()
        _safe_zip_extract(data, extracted)
        root = _bundle_root(extracted)
        files = _bundle_files(root)
        relative_files = tuple(sorted(destination.as_posix() for _source, destination in files))

        previous: dict[str, object] = {}
        state = _state_path(repo, bundle)
        if state.is_file():
            try:
                loaded = json.loads(state.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    previous = loaded
            except json.JSONDecodeError:
                raise RuntimeError(f"invalid sync state: {state}")
        managed = {str(item) for item in previous.get("files", []) if isinstance(item, str)}
        conflicts = [
            str(destination)
            for _source, destination in files
            if (repo / destination).exists() and destination.as_posix() not in managed and not force
        ]
        if conflicts:
            raise RuntimeError(
                "refusing to overwrite existing files not owned by sync state; "
                f"use --force after review: {', '.join(sorted(conflicts))}"
            )

        if not dry_run:
            for source, destination in files:
                target = repo / destination
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(
                json.dumps(
                    {
                        "source_repository": source_repository,
                        "release": release_name,
                        "asset": asset_name,
                        "sha256": digest,
                        "files": list(relative_files),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
    return SyncResult(bundle, release_name, asset_name, digest, relative_files, True, dry_run)


def _print(payload: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    results = payload if isinstance(payload, list) else [payload]
    for item in results:
        print(f"synced: {item['bundle']} ({item['release']})")
        print(f"asset: {item['asset']}")
        print(f"files: {len(item['files'])}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit skills")
    sub = parser.add_subparsers(dest="command", required=True)
    sync = sub.add_parser("sync", help="download and register Skill/Knowledge bundles from GitHub Releases")
    sync.add_argument("--repo", default=".", help="Target XRefKit repository; defaults to the current directory")
    sync.add_argument("--source-repository", default=DEFAULT_SOURCE_REPOSITORY, help="GitHub owner/repository containing releases")
    sync.add_argument("--bundle", action="append", help="Bundle name, for example csharp; repeat for multiple bundles")
    sync.add_argument("--all", action="store_true", help="Synchronize every xrefkit-skills-*.zip asset in the release")
    sync.add_argument("--release", default="latest", help="Release tag, or latest (default)")
    sync.add_argument("--force", action="store_true", help="Allow overwriting files not owned by a previous sync")
    sync.add_argument("--dry-run", action="store_true", help="Download and validate without writing the repository")
    sync.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.bundle and not args.all:
        parser.error("one of --bundle or --all is required")
    release_payload = _release(args.source_repository, args.release)
    bundles = list(args.bundle or [])
    if args.all:
        for asset in _assets(release_payload):
            name = asset.get("name")
            if not isinstance(name, str) or not name.startswith(ASSET_PREFIX) or not name.endswith(".zip"):
                continue
            stem = name[:-4][len(ASSET_PREFIX) :]
            match = VERSION_SUFFIX_RE.match(stem)
            bundles.append(match.group("bundle") if match else stem)
    bundles = list(dict.fromkeys(bundles))
    results = [
        sync_bundle(
            repo=Path(args.repo),
            source_repository=args.source_repository,
            bundle=bundle,
            release=args.release,
            force=args.force,
            dry_run=args.dry_run,
        ).to_dict()
        for bundle in bundles
    ]
    _print(results, as_json=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
