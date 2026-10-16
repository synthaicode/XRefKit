"""Client preparation for legacy migration; never imports or executes legacy code.

The Skill Run remains the workflow owner. A bundle is inert contribution input,
not an approval, a test result, or a second migration state machine.
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import base64
import hashlib
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .contribution_returns import MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES, _safe_path

MANIFEST = "legacy-resources.json"
_SKILL_NAMES = {"SKILL.md", "skill.md", "SKILL.v1.md"}
_TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".csv", ".ini", ".cfg"}
_SECRET_NAMES = re.compile(r"(?:^|[._-])(?:secret|secrets|credentials?|tokens?|passwords?)(?:[._-]|$)", re.I)
_SECRET_CONTENT = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|[\"']?\b(?:password|api[_-]?key|access[_-]?token|client[_-]?secret)[\"']?\s*[:=]\s*['\"][^'\"\s]{6,}['\"]", re.I)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _source_file(root: Path, relative: str) -> Path:
    relative = _safe_path(relative)
    target = root.joinpath(*relative.split("/"))
    if any(parent.is_symlink() for parent in [target, *target.parents] if parent != root.parent):
        raise ValueError(f"symlink is not a migration input: {relative}")
    if not target.resolve().is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f"missing or unsafe migration input: {relative}")
    return target


def inspect_legacy_environment(source: Path) -> dict[str, Any]:
    """Inspect local client bytes, including a shared tools/ outside Skill folders."""
    source = source.resolve()
    if not source.is_dir():
        raise ValueError("legacy source must be an accessible client directory")
    files, excluded, skills, imports, tests, dependencies = [], [], [], {}, [], []

    def candidates():
        def traversal_error(error):
            raise error  # Inaccessible selected scope is unknown, never silently omitted.

        for directory, names, filenames in os.walk(source, topdown=True, followlinks=False, onerror=traversal_error):
            retained = []
            for name in sorted(names):
                path = Path(directory) / name
                if (name.startswith(".") or name in {"__pycache__", "node_modules", "venv"}
                        or path.is_symlink() or getattr(path, "is_junction", lambda: False)()):
                    excluded.append({"path": path.relative_to(source).as_posix() + "/",
                                     "reason": "excluded directory; hidden, generated, or linked subtree was not traversed"})
                else:
                    retained.append(name)
            names[:] = retained
            for name in sorted(filenames):
                yield Path(directory) / name

    for path in candidates():
        relative = path.relative_to(source).as_posix()
        if not path.is_file() and not path.is_symlink():
            continue
        reason = None
        if path.is_symlink() or any(p.startswith(".") or p in {"__pycache__", "node_modules", "venv"} for p in path.relative_to(source).parts):
            reason = "hidden, generated, or symlink input"
        elif _SECRET_NAMES.search(path.name) or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            reason = "credential-like input; configure separately"
        elif path.suffix.lower() not in _TEXT_SUFFIXES:
            reason = "unsupported non-text input; preserve and review separately"
        elif path.stat().st_size > MAX_FILE_BYTES:
            reason = "exceeds contribution file limit; split the migration"
        if reason:
            excluded.append({"path": relative, "reason": reason})
            continue
        try:
            content = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            excluded.append({"path": relative, "reason": "not UTF-8; preserve and review separately"})
            continue
        if _SECRET_CONTENT.search(content):
            excluded.append({"path": relative, "reason": "possible embedded credential; remove secret before preparation"})
            continue
        files.append(relative)
        if path.name in _SKILL_NAMES:
            skills.append(path.parent.relative_to(source).as_posix())
        if path.name.startswith("test_") or "tests" in path.relative_to(source).parts:
            tests.append(relative)
        if path.name in {"pyproject.toml", "setup.cfg", "setup.py", "Pipfile", "poetry.lock"} or path.name.startswith("requirements"):
            dependencies.append(relative)
        if path.suffix == ".py":
            try:
                tree = ast.parse(content)
                imports[relative] = sorted({n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
            except SyntaxError as exc:
                imports[relative] = {"syntax_error": str(exc)}
    return {"source": str(source), "skills": sorted(set(skills)), "files": files,
            "excluded": excluded, "imports": imports, "existing_tests": tests,
            "dependency_files": dependencies, "execution_performed": False,
            "coverage": "candidate inventory; dynamic imports, external files and business expectations require review"}


def migration_tasks(version: str) -> list[dict[str, str]]:
    """Concrete work items projected into an existing opened Skill Run."""
    specs = [
        ("scope", "Confirm Skill/resource mapping, shared imports, dependencies and excluded files", "Every selected Skill has reviewed resource mapping; all excluded and dynamic resources have a disposition"),
        ("safety", "Prepare isolated test configuration and credentials outside the bundle", "Test environment or safe mode is explicitly evidenced; side effects and secrets are reviewed before any legacy execution"),
        ("tests", "Reuse existing tests and fill missing test code/data", "Representative inputs and assertions cover selected behavior; generated static scaffolds alone do not satisfy this criterion"),
        ("baseline", "Capture legacy behavior where accessible", "Old-environment command, environment, inputs and outputs are retained as observed baseline; unavailable checks remain unknown"),
        ("expectations", "Obtain required human business judgment", "Business expected results have explicit human evidence; observed legacy output is not automatically approved"),
        ("upload", "Upload, review and adopt the exact inert bundle", "Existing contribution upload and human adoption gate accepted this exact manifest version"),
        ("register", "Register migrated Skills from the adopted bundle", "Selected Skills resolve over MCP and expose the pinned shared resource bundle"),
        ("client", "Fetch pinned resources and verify in clean client environment", "Hash-checked client files preserve layout and imports; tests compared with baseline and approved expectations have explicit results"),
    ]
    return [{"item_id": f"legacy-{version[:12]}-{key}", "status": "pending", "role": "executor", "text": text, "completion_criterion": criterion} for key, text, criterion in specs]


def bind_migration_tasks(log: Path, version: str) -> list[dict[str, str]]:
    from xrefkit.skillrun import _parse_work_items, update_work_item

    existing = {row["item_id"] for row in _parse_work_items(log.read_text(encoding="utf-8"))}
    tasks = migration_tasks(version)
    for task in tasks:
        if task["item_id"] in existing:
            continue  # Resuming preparation must never reset completed or unknown work.
        result = update_work_item(SimpleNamespace(log=str(log), item=task["item_id"],
            status=task["status"], role=task["role"], text=task["text"],
            completion_criterion=task["completion_criterion"], criterion_unknown_reason=None, supersedes=None))
        if not result.ok:
            raise ValueError("; ".join(result.errors))
    return tasks


_SCAFFOLD = '''"""Static migration checks only. Never imports legacy modules."""
import ast
import json
import pathlib
import unittest

class MigrationPreparation(unittest.TestCase):
    def test_python_syntax(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "legacy-resources.json").read_text(encoding="utf-8"))
        for row in manifest["files"]:
            if row["path"].endswith(".py"):
                with self.subTest(path=row["path"]):
                    ast.parse((root / row["path"]).read_bytes().decode("utf-8"))

    @unittest.skip("Supply representative test inputs and business-approved assertions; static syntax is not behavior verification")
    def test_business_behavior(self):
        self.fail("Missing approved behavioral assertions")

if __name__ == "__main__":
    unittest.main()
'''


def prepare_legacy_bundle(source: Path, output: Path, *, skills: list[str],
                          resources: list[str], log: Path | None = None) -> dict[str, Any]:
    """Build selected, non-secret text files for the existing governed upload route."""
    from .legacy_resources import manifest_version, manifest_hash, validate_resource_manifest

    source, output = source.resolve(), output.resolve()
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("source and output must be separate non-overlapping directories")
    inventory = inspect_legacy_environment(source)
    if not skills or any(skill not in inventory["skills"] for skill in skills):
        raise ValueError("select exact Skill folders from the client inventory")
    selected = set(resources)
    for skill in skills:
        selected.update(path for path in inventory["files"] if (skill == "." or path.startswith(skill + "/")))
    if any(path not in inventory["files"] for path in selected):
        raise ValueError("selected resource is absent, excluded, unsafe, or contains a possible secret")
    content = {path: _source_file(source, path).read_bytes() for path in sorted(selected)}
    if any(_SECRET_CONTENT.search(value.decode("utf-8")) for value in content.values()):
        raise ValueError("selected input now contains a possible secret; inspect again")
    generated = {"migration_checks/test_preparation.py": _SCAFFOLD.encode(),
                 "migration_checks/cases.json": b'{"status":"unknown","expected_result_authority":"human_required","cases":[]}\n'}
    reserved = {path.casefold() for path in generated} | {MANIFEST.casefold()}
    if any(path.casefold() in reserved for path in content):
        raise ValueError("reserved migration manifest/scaffold path collision")
    content.update(generated)
    rows = [{"path": path, "content_hash": _digest(value), "size_bytes": len(value)} for path, value in sorted(content.items())]
    manifest = {"schema_version": 1, "version": manifest_version(rows), "files": rows,
                "skills": [{"source": skill, "resources": sorted(content)} for skill in sorted(set(skills))]}
    validate_resource_manifest(manifest, content)
    content[MANIFEST] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    if len(content) > MAX_FILES or sum(map(len, content.values())) > MAX_TOTAL_BYTES:
        raise ValueError("bundle exceeds contribution limits; split selected Skills into smaller migrations")
    if any(len(value) > MAX_FILE_BYTES for value in content.values()):
        raise ValueError("bundle file exceeds contribution file limit")
    # Preflight all paths before writes; repeated preparation must preserve edits.
    for relative, value in content.items():
        target = output / relative
        if target.exists() and (not target.is_file() or target.read_bytes() != value):
            raise ValueError(f"refusing to overwrite prepared input: {relative}")
        if any(p.is_symlink() for p in [target, *target.parents]):
            raise ValueError(f"unsafe output path: {relative}")
    if log is not None:
        bind_migration_tasks(log, manifest_hash(manifest))
    for relative, value in content.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open("xb") as stream:
                stream.write(value)
    return {"bundle": str(output), "manifest": manifest, "inventory": inventory,
            "workflow_log": str(log) if log else None, "tasks": migration_tasks(manifest_hash(manifest)),
            "manifest_hash": manifest_hash(manifest),
            "status": "prepared_not_verified", "execution_performed": False,
            "expected_results": "unknown; legacy observations are not business approval",
            "upload": {"create_tool": "create_contribution_upload_session", "seal_tool": "seal_contribution_upload",
                "kind": "deterministic_tool", "files": [{"path": path, "content_hash": _digest(value), "byte_count": len(value)} for path, value in sorted(content.items())],
                "deterministic_tool": {"runtime": "python", "entrypoint": "migration_checks/test_preparation.py",
                    "input_contract": {"legacy_resources_version": manifest["version"], "configuration": "client-local, never bundle secrets"},
                    "output_contract": {"static_checks": "not_behavioral_verification", "business_expectations": "unknown"},
                    "verification_evidence": [{"kind": "preparation_only", "command": "xrefkit mcp migrate prepare", "result": "Files hashed; no legacy code executed; baseline and business correctness unverified"}]},
                "next": "Upload exact files using issued WebDAV URL, seal, obtain existing human review/adoption, then register_legacy_bundle(contribution_id). Reader profile cannot register."}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit mcp migrate")
    sub = parser.add_subparsers(dest="action", required=True)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--source", type=Path, required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--skill", action="append", required=True)
    prepare.add_argument("--resource", action="append", default=[])
    prepare.add_argument("--log", type=Path, required=True, help="Existing opened Skill Run; migration work items are added without resetting prior progress")
    fetch = sub.add_parser("fetch")
    fetch.add_argument("--url", required=True, help="HTTP MCP URL; requires the xrefkit[mcp] extra")
    fetch.add_argument("--skill-id", required=True)
    fetch.add_argument("--namespace", required=True)
    fetch.add_argument("--manifest-hash", required=True, help="Pinned manifest hash from the registered Skill association")
    fetch.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "fetch":
            result = asyncio.run(fetch_legacy_bundle(args.url, args.skill_id, args.namespace, args.manifest_hash, args.cache))
        else:
            result = inspect_legacy_environment(args.source) if args.action == "inspect" else prepare_legacy_bundle(args.source, args.output, skills=args.skill, resources=args.resource, log=args.log)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


async def fetch_legacy_bundle(url: str, skill_id: str, namespace: str,
                              expected_manifest_hash: str, cache: Path) -> dict[str, Any]:
    """Materialize HTTP MCP resources using the installed Python client, no service."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    from .legacy_resources import materialize_legacy_resources, manifest_hash

    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            async def call(tool: str, arguments: dict | None = None) -> dict:
                result = await session.call_tool(tool, arguments or {})
                if result.isError:
                    raise ValueError(f"MCP {tool} failed: {result.content}")
                return result.structuredContent or json.loads(result.content[0].text)

            await call("get_startup_context")
            skill = await call("get_skill", {"skill_id": skill_id})
            association = skill.get("client_resources", {})
            if association.get("namespace") != namespace or association.get("manifest_hash") != expected_manifest_hash:
                raise ValueError("selected Skill does not bind the requested resource manifest")
            manifest = await call("get_legacy_resource_manifest", {"namespace": namespace})
            if manifest_hash(manifest) != expected_manifest_hash:
                raise ValueError("server manifest changed from selected Skill identity")
            content = {}
            if not (cache / manifest["version"]).exists():
                for row in manifest["files"]:
                    response = await call("get_legacy_resource_file", {"namespace": namespace, "path": row["path"]})
                    if response.get("version") != manifest["version"] or response.get("encoding") != "base64":
                        raise ValueError("resource response changed version or encoding")
                    content[row["path"]] = base64.b64decode(response["content"], validate=True)
            folder = materialize_legacy_resources(manifest, content.__getitem__, cache,
                                                  expected_manifest_hash=expected_manifest_hash)
            return {"cache_root": str(folder), "version": manifest["version"],
                    "manifest_hash": expected_manifest_hash, "execution_performed": False,
                    "next": "Review dependency/configuration and migration safety work items. Run Python locally with this folder as cwd and -B to preserve immutable cache; direct mutable outputs outside the cache. Record observed results in the migration Skill Run."}
