"""Inspect Python distribution contents before a PyPI upload.

This checker intentionally uses only the Python standard library so the
artifact-inspection job does not need to trust another third-party scanner.
It validates wheel metadata and layout, safely expands both archive formats,
prints their member lists, and rejects common release contamination and
high-confidence credential patterns without printing matched secret values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import zipfile
from email.parser import BytesParser
from email.policy import compat32
from pathlib import Path, PurePosixPath
from typing import Iterable


DEFAULT_MAX_FILE_BYTES = 5 * 1024 * 1024

_PRIVATE_KEY = re.compile(
    rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
    rb"[\s\S]+?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
)
_TOKEN_PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("GitHub token", re.compile(rb"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("PyPI token", re.compile(rb"\bpypi-[A-Za-z0-9_-]{20,}\b")),
    ("AWS access key", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(rb"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("Slack token", re.compile(rb"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    ("npm token", re.compile(rb"\bnpm_[A-Za-z0-9]{20,}\b")),
    (
        "Bearer token",
        re.compile(rb"\bauthorization\s*:\s*bearer\s+[A-Za-z0-9._~+/=-]{20,}", re.I),
    ),
)
_GENERIC_SECRET_ASSIGNMENT = re.compile(
    rb"\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|"
    rb"secret(?:[_-]?key)?)\s*[:=]\s*[\"']?(?P<value>[A-Za-z0-9+/=_-]{20,})",
    re.I,
)
_PLACEHOLDER_VALUES = {
    "change-me",
    "changeme",
    "example",
    "fake",
    "placeholder",
    "password",
    "secret",
    "test",
    "token",
    "your-token",
    "your_token",
}

_BANNED_COMPONENTS = {
    ".git",
    ".github",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".vscode",
    "__macosx",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "test-results",
}
_BANNED_NAMES = {
    ".coverage",
    ".gitattributes",
    ".gitignore",
    ".ds_store",
    "coverage.xml",
    "desktop.ini",
    "thumbs.db",
}
_BANNED_SUFFIXES = (
    ".bak",
    ".log",
    ".orig",
    ".pyc",
    ".pyo",
    ".rej",
    ".swp",
    ".swo",
    ".tmp",
    ".temp",
)


def normalize_project_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def display_path(path: PurePosixPath | Path) -> str:
    return str(path).replace("\\", "/")


def safe_archive_parts(name: str) -> tuple[str, ...]:
    """Return safe POSIX archive components or raise for traversal paths."""

    if not name or "\\" in name or name.startswith("/"):
        raise ValueError(f"unsafe archive member path: {display_path(PurePosixPath(name))}")
    parts = PurePosixPath(name).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unsafe archive member path: {name}")
    return parts


def path_issues(name: str, *, archive_label: str) -> list[str]:
    lowered_parts = [part.lower() for part in PurePosixPath(name).parts]
    lowered_name = lowered_parts[-1] if lowered_parts else ""
    issues: list[str] = []

    if any(part in _BANNED_COMPONENTS for part in lowered_parts):
        component = next(part for part in lowered_parts if part in _BANNED_COMPONENTS)
        issues.append(f"{archive_label}: forbidden generated/internal path component {component}: {name}")
    if lowered_name in _BANNED_NAMES:
        issues.append(f"{archive_label}: forbidden generated/OS file {name}")
    if lowered_name == ".env" or lowered_name.startswith(".env."):
        issues.append(f"{archive_label}: environment file is not allowed: {name}")
    if lowered_name.endswith(_BANNED_SUFFIXES):
        issues.append(f"{archive_label}: temporary/cache/output suffix is not allowed: {name}")
    return issues


def is_placeholder(value: bytes) -> bool:
    text = value.decode("ascii", errors="ignore").lower().strip("'\" `")
    return (
        text in _PLACEHOLDER_VALUES
        or text.startswith("your-")
        or text.startswith("your_")
        or text.startswith("<")
        or text.startswith("${")
        or set(text) <= {"*", ".", "-", "_"}
    )


def content_issues(data: bytes, name: str, *, archive_label: str) -> list[str]:
    issues: list[str] = []
    if _PRIVATE_KEY.search(data):
        issues.append(f"{archive_label}: private-key material detected in {name} (value omitted)")
    for label, pattern in _TOKEN_PATTERNS:
        if pattern.search(data):
            issues.append(f"{archive_label}: {label} pattern detected in {name} (value omitted)")
    generic = _GENERIC_SECRET_ASSIGNMENT.search(data)
    if generic and not is_placeholder(generic.group("value")):
        issues.append(f"{archive_label}: possible credential assignment in {name} (value omitted)")
    return issues


def size_issues(size: int, name: str, *, archive_label: str, max_file_bytes: int) -> list[str]:
    if size > max_file_bytes:
        return [
            f"{archive_label}: file exceeds {max_file_bytes} bytes: {name} ({size} bytes)"
        ]
    return []


def scan_extracted_tree(
    root: Path,
    *,
    archive_label: str,
    max_file_bytes: int,
) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = display_path(path.relative_to(root))
        if path.is_dir():
            continue
        files.append(relative)
        issues.extend(path_issues(relative, archive_label=archive_label))
        size = path.stat().st_size
        issues.extend(size_issues(size, relative, archive_label=archive_label, max_file_bytes=max_file_bytes))
        if size <= max_file_bytes:
            issues.extend(content_issues(path.read_bytes(), relative, archive_label=archive_label))
    return issues, files


def safe_extract_zip(archive: zipfile.ZipFile, destination: Path, *, label: str, max_file_bytes: int) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    names: list[str] = []
    seen: set[str] = set()
    for info in archive.infolist():
        try:
            parts = safe_archive_parts(info.filename)
        except ValueError as exc:
            issues.append(f"{label}: {exc}")
            continue
        name = "/".join(parts)
        if name in seen:
            issues.append(f"{label}: duplicate member path: {name}")
        seen.add(name)
        names.append(name)
        issues.extend(path_issues(name, archive_label=label))
        if info.is_dir():
            (destination.joinpath(*parts)).mkdir(parents=True, exist_ok=True)
            continue
        issues.extend(size_issues(info.file_size, name, archive_label=label, max_file_bytes=max_file_bytes))
        mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode):
            issues.append(f"{label}: symbolic link member is not allowed: {name}")
            continue
        target = destination.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info, "r") as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
    return issues, names


def safe_extract_tar(archive: tarfile.TarFile, destination: Path, *, label: str, max_file_bytes: int) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    names: list[str] = []
    seen: set[str] = set()
    for member in archive.getmembers():
        try:
            parts = safe_archive_parts(member.name)
        except ValueError as exc:
            issues.append(f"{label}: {exc}")
            continue
        name = "/".join(parts)
        if name in seen:
            issues.append(f"{label}: duplicate member path: {name}")
        seen.add(name)
        names.append(name)
        issues.extend(path_issues(name, archive_label=label))
        if member.isdir():
            destination.joinpath(*parts).mkdir(parents=True, exist_ok=True)
            continue
        if member.issym() or member.islnk():
            issues.append(f"{label}: link member is not allowed: {name}")
            continue
        if not member.isfile():
            issues.append(f"{label}: unsupported archive member type: {name}")
            continue
        issues.extend(size_issues(member.size, name, archive_label=label, max_file_bytes=max_file_bytes))
        target = destination.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        source = archive.extractfile(member)
        if source is None:
            issues.append(f"{label}: member could not be read: {name}")
            continue
        with source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
    return issues, names


def validate_wheel(
    path: Path,
    *,
    project_name: str,
    package_module: str,
    destination: Path,
    max_file_bytes: int,
) -> tuple[list[str], list[str]]:
    label = f"wheel {path.name}"
    issues: list[str] = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        member_names = [info.filename.rstrip("/") for info in infos if not info.is_dir()]
        dist_info_roots = {
            PurePosixPath(name).parts[0]
            for name in member_names
            if name.endswith(".dist-info/METADATA")
        }
        if len(dist_info_roots) != 1:
            issues.append(f"{label}: expected exactly one .dist-info/METADATA directory")
            dist_info_root = ""
        else:
            dist_info_root = next(iter(dist_info_roots))
        required = {
            f"{dist_info_root}/METADATA",
            f"{dist_info_root}/WHEEL",
            f"{dist_info_root}/RECORD",
        }
        if not required.issubset(set(member_names)):
            issues.append(f"{label}: missing required wheel metadata: {sorted(required - set(member_names))}")
        for name in member_names:
            try:
                parts = safe_archive_parts(name)
            except ValueError as exc:
                issues.append(f"{label}: {exc}")
                continue
            if parts[0] != package_module and parts[0] != dist_info_root:
                issues.append(f"{label}: unexpected top-level path: {name}")
            issues.extend(path_issues(name, archive_label=label))
        if dist_info_root:
            metadata_name = f"{dist_info_root}/METADATA"
            metadata = BytesParser(policy=compat32).parsebytes(archive.read(metadata_name))
            actual_name = metadata.get("Name", "")
            actual_version = metadata.get("Version", "")
            if normalize_project_name(actual_name) != normalize_project_name(project_name):
                issues.append(f"{label}: metadata Name does not match project: {actual_name!r}")
            if not actual_version:
                issues.append(f"{label}: metadata Version is empty")
            record_name = f"{dist_info_root}/RECORD"
            if record_name in member_names:
                record_rows = csv.reader(io.StringIO(archive.read(record_name).decode("utf-8")))
                record_paths = {row[0] for row in record_rows if row}
                if record_paths != set(member_names):
                    issues.append(f"{label}: RECORD entries do not match wheel members")
        extract_issues, names = safe_extract_zip(
            archive,
            destination,
            label=label,
            max_file_bytes=max_file_bytes,
        )
    issues.extend(extract_issues)
    tree_issues, files = scan_extracted_tree(
        destination,
        archive_label=label,
        max_file_bytes=max_file_bytes,
    )
    issues.extend(tree_issues)
    return issues, sorted(set(names) | set(files))


def allowed_sdist_member(relative_parts: tuple[str, ...], package_module: str) -> bool:
    if not relative_parts:
        return True
    if len(relative_parts) == 1 and relative_parts[0] in {
        "LICENSE",
        "LICENSE.txt",
        "PKG-INFO",
        "README.md",
        "README.rst",
        "README.txt",
        "pyproject.toml",
        "setup.cfg",
    }:
        return True
    if len(relative_parts) == 1 and relative_parts[0] in {"src", "tests"}:
        return True
    if relative_parts[0] == "tests":
        return True
    if relative_parts[0] == package_module:
        return True
    if len(relative_parts) >= 2 and relative_parts[0] == "src" and relative_parts[1] == package_module:
        return True
    egg_info_names = {
        f"{package_module}.egg-info",
        f"src/{package_module}.egg-info",
    }
    if relative_parts[0] in egg_info_names:
        return True
    if len(relative_parts) >= 2 and f"{relative_parts[0]}/{relative_parts[1]}" in egg_info_names:
        return True
    return False


def validate_sdist(
    path: Path,
    *,
    project_name: str,
    package_module: str,
    destination: Path,
    max_file_bytes: int,
) -> tuple[list[str], list[str]]:
    label = f"sdist {path.name}"
    issues: list[str] = []
    with tarfile.open(path, "r:gz") as archive:
        raw_names = [member.name for member in archive.getmembers()]
        top_levels = {PurePosixPath(name).parts[0] for name in raw_names if name}
        if len(top_levels) != 1:
            issues.append(f"{label}: expected one top-level source directory: {sorted(top_levels)}")
            root_name = ""
        else:
            root_name = next(iter(top_levels))
            if not normalize_project_name(root_name).startswith(normalize_project_name(project_name) + "-"):
                issues.append(f"{label}: top-level directory does not match project name: {root_name}")
        for name in raw_names:
            try:
                parts = safe_archive_parts(name)
            except ValueError as exc:
                issues.append(f"{label}: {exc}")
                continue
            issues.extend(path_issues("/".join(parts), archive_label=label))
            if root_name and parts[0] == root_name:
                relative_parts = parts[1:]
                if not allowed_sdist_member(relative_parts, package_module):
                    issues.append(f"{label}: unexpected sdist member: {'/'.join(parts)}")
        extract_issues, names = safe_extract_tar(
            archive,
            destination,
            label=label,
            max_file_bytes=max_file_bytes,
        )
    issues.extend(extract_issues)
    tree_issues, files = scan_extracted_tree(
        destination,
        archive_label=label,
        max_file_bytes=max_file_bytes,
    )
    issues.extend(tree_issues)
    return issues, sorted(set(names) | set(files))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(path: Path, project_name: str, distributions: Iterable[tuple[Path, list[str]]]) -> None:
    lines = [f"project: {project_name}", ""]
    for archive, members in distributions:
        lines.append(f"distribution: {archive.name}")
        lines.append(f"sha256: {sha256(archive)}")
        lines.append("members:")
        lines.extend(f"  - {member}" for member in members)
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True, help="directory containing exactly one wheel and one sdist")
    parser.add_argument("--project-name", required=True, help="PEP 621 project name")
    parser.add_argument("--package-module", required=True, help="import/package directory expected in the wheel")
    parser.add_argument(
        "--required-member",
        action="append",
        default=[],
        help="member path that must be present in both distributions",
    )
    parser.add_argument("--manifest-output", type=Path, help="optional member-list manifest path")
    parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_file_bytes <= 0:
        print("--max-file-bytes must be positive", file=sys.stderr)
        return 2
    dist = args.dist.resolve()
    if not dist.is_dir():
        print(f"artifact directory not found: {dist}", file=sys.stderr)
        return 2
    archives = sorted(path for path in dist.iterdir() if path.is_file())
    wheels = [path for path in archives if path.name.endswith(".whl")]
    sdists = [path for path in archives if path.name.endswith(".tar.gz")]
    issues: list[str] = []
    if len(wheels) != 1:
        issues.append(f"expected exactly one wheel, found {len(wheels)}")
    if len(sdists) != 1:
        issues.append(f"expected exactly one sdist, found {len(sdists)}")
    expected_files = set(wheels + sdists)
    unexpected_files = [path.name for path in archives if path not in expected_files]
    if unexpected_files:
        issues.append(f"unexpected files in dist/: {sorted(unexpected_files)}")

    distributions: list[tuple[Path, list[str]]] = []
    with tempfile.TemporaryDirectory(prefix="xrefkit-artifact-inspection-") as temporary:
        root = Path(temporary)
        if wheels:
            wheel_issues, wheel_members = validate_wheel(
                wheels[0],
                project_name=args.project_name,
                package_module=args.package_module,
                destination=root / "wheel",
                max_file_bytes=args.max_file_bytes,
            )
            issues.extend(wheel_issues)
            distributions.append((wheels[0], wheel_members))
        if sdists:
            sdist_issues, sdist_members = validate_sdist(
                sdists[0],
                project_name=args.project_name,
                package_module=args.package_module,
                destination=root / "sdist",
                max_file_bytes=args.max_file_bytes,
            )
            issues.extend(sdist_issues)
            distributions.append((sdists[0], sdist_members))

        for archive, members in distributions:
            for required in args.required_member:
                if not any(member == required or member.endswith("/" + required) for member in members):
                    issues.append(f"{archive.name}: required package member is missing: {required}")

    print(f"artifact inspection: project={args.project_name}")
    for archive, members in distributions:
        print(f"{archive.name}: sha256={sha256(archive)}")
        print(f"{archive.name} members ({len(members)}):")
        for member in members:
            print(f"  {member}")
    if args.manifest_output:
        write_manifest(args.manifest_output, args.project_name, distributions)
        print(f"member manifest: {args.manifest_output}")
    if issues:
        print("artifact inspection failed:")
        for issue in sorted(set(issues)):
            print(f"- {issue}")
        return 1
    print("artifact inspection passed: no forbidden paths, oversized files, or credential patterns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
