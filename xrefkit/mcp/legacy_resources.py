from __future__ import annotations

import base64
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Callable

MANIFEST_NAME = 'legacy-resources.json'


def relative_path(value: str) -> str:
    """Accept portable relative paths, without Windows aliases or traversal."""
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('resource path must be a portable relative path')
    parts = value.split('/')
    for part in parts:
        if (part in ('', '.', '..') or part.endswith((' ', '.'))
                or re.search(r'[<>:"|?*\x00-\x1f]', part)
                or re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', part)):
            raise ValueError(f'unsafe resource path: {value}')
    return value


def manifest_version(files: list[dict]) -> str:
    return hashlib.sha256(json.dumps(sorted(files, key=lambda f: f['path']),
        sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


resource_version = manifest_version


def manifest_hash(manifest: dict) -> str:
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def validate_resource_manifest(manifest: dict, files: dict[str, bytes] | None = None) -> dict:
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 1:
        raise ValueError('unsupported legacy resource manifest')
    rows = manifest.get('files')
    if not isinstance(rows, list) or not rows:
        raise ValueError('resource manifest requires files')
    seen: set[str] = set()
    paths: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('invalid resource descriptor')
        path = relative_path(row.get('path'))
        if path.casefold() in seen or path.casefold() == MANIFEST_NAME.casefold():
            raise ValueError('duplicate or reserved resource path')
        seen.add(path.casefold())
        paths.add(path)
        if not re.fullmatch('[0-9a-f]{64}', str(row.get('content_hash', ''))):
            raise ValueError('invalid resource content hash')
        if type(row.get('size_bytes')) is not int or row['size_bytes'] < 0:
            raise ValueError('invalid resource size')
        if files is not None:
            content = files.get(path)
            if not isinstance(content, bytes) or len(content) != row['size_bytes'] or hashlib.sha256(content).hexdigest() != row['content_hash']:
                raise ValueError(f'resource content mismatch: {path}')
    if any('/'.join(path.split('/')[:i]).casefold() in seen for path in paths for i in range(1, len(path.split('/')))):
        raise ValueError('resource file/directory collision')
    if manifest.get('version') != manifest_version(rows):
        raise ValueError('resource manifest version mismatch')
    if files is not None and set(files) != paths:
        raise ValueError('resource file set mismatch')
    skills = manifest.get('skills', [])
    if not isinstance(skills, list):
        raise ValueError('invalid resource Skill associations')
    for skill in skills:
        if not isinstance(skill, dict):
            raise ValueError('invalid resource Skill association')
        if skill.get('source') != '.':
            relative_path(skill.get('source'))
        resources = skill.get('resources')
        if not isinstance(resources, list) or any(p not in paths for p in resources):
            raise ValueError('Skill references missing resource')
    return manifest


def _contained(root: Path, path: str) -> Path:
    target = root / relative_path(path)
    current = target
    while current != root:
        if current.is_symlink() or getattr(current, 'is_junction', lambda: False)():
            raise ValueError('resource links are not allowed')
        current = current.parent
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('resource escapes root')
    return target


def read_resource_manifest(repo_root: Path, namespace: str) -> tuple[Path, dict]:
    if '/' in relative_path(namespace):
        raise ValueError('namespace must be one path component')
    root = _contained(repo_root, f'tools/{namespace}')
    manifest = json.loads(_contained(root, MANIFEST_NAME).read_text(encoding='utf-8'))
    return root, validate_resource_manifest(manifest)


def resource_file(repo_root: Path, namespace: str, path: str) -> dict:
    root, manifest = read_resource_manifest(repo_root, namespace)
    relative_path(path)
    row = next((row for row in manifest['files'] if row['path'] == path), None)
    if row is None:
        raise KeyError(f'resource is not declared: {path}')
    content = _contained(root, path).read_bytes()
    if len(content) != row['size_bytes'] or hashlib.sha256(content).hexdigest() != row['content_hash']:
        raise ValueError(f'resource content mismatch: {path}')
    return {**row, 'version': manifest['version'], 'encoding': 'base64',
            'content': base64.b64encode(content).decode('ascii')}


def materialize_legacy_resources(manifest: dict, fetch_file: Callable[[str], bytes], cache_dir: Path, *, expected_manifest_hash: str | None = None) -> Path:
    """Fetch verified resources without running code or installing dependencies.

    Every reuse revalidates all files. A damaged cache is rejected, never executed.
    """
    validate_resource_manifest(manifest)
    if expected_manifest_hash is not None and manifest_hash(manifest) != expected_manifest_hash:
        raise ValueError('resource manifest identity mismatch')
    cache_dir = Path(cache_dir).resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = _contained(cache_dir, manifest['version'])
    if target.exists():
        cached_manifest = json.loads(_contained(target, MANIFEST_NAME).read_text(encoding='utf-8'))
        if cached_manifest != manifest:
            raise ValueError('cached resource manifest mismatch')
        contents = {row['path']: _contained(target, row['path']).read_bytes() for row in manifest['files']}
        validate_resource_manifest(manifest, contents)
        entries = list(target.rglob('*'))
        for entry in entries:
            _contained(target, entry.relative_to(target).as_posix())
        actual = {p.relative_to(target).as_posix() for p in entries if p.is_file()}
        if actual != set(contents) | {MANIFEST_NAME}:
            raise ValueError('cached resource file set mismatch')
        return target
    with tempfile.TemporaryDirectory(prefix='.legacy-', dir=cache_dir) as staging:
        staged = Path(staging) / 'bundle'
        staged.mkdir()
        contents = {}
        for row in manifest['files']:
            contents[row['path']] = fetch_file(row['path'])
        validate_resource_manifest(manifest, contents)
        for path, content in contents.items():
            destination = _contained(staged, path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        (staged / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        try:
            staged.rename(target)
        except FileExistsError:
            return materialize_legacy_resources(manifest, fetch_file, cache_dir, expected_manifest_hash=expected_manifest_hash)
    return target
