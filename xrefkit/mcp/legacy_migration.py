"""First-use migration, scoped to the MCP server's target repository.

Conversion is not completion: only successful MCP body retrievals satisfy the
persisted receipt set. State is independent of runtime/package versions.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .repository import first_xid, markdown_xid_only_text, stable_hash

STATE = Path(".xrefkit/legacy-migration.json")
STAGING = Path(".xrefkit/legacy-migration-staging")


def _path(root: Path, relative: str) -> Path:
    candidate = root / relative
    if candidate.is_symlink() or not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"migration path escapes target: {relative}")
    return candidate


def _load(root: Path) -> dict[str, Any]:
    path = _path(root, STATE.as_posix())
    if not path.exists():
        return {"schema_version": 1, "decision": None, "units": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or data.get("schema_version") != 1
            or data.get("decision") not in {None, "not_required"}
            or not isinstance(data.get("units"), dict)):
        raise ValueError("unsupported or invalid legacy migration state; preserve it for recovery")
    for unit in data["units"].values():
        if (not isinstance(unit, dict) or unit.get("status") not in {"pending", "prepared", "installed", "failed"}
                or not isinstance(unit.get("artifacts", []), list)
                or not all(isinstance(unit.get(k), str) for k in ("source", "target"))):
            raise ValueError("invalid legacy migration unit; preserve state for recovery")
        for artifact in unit.get("artifacts", []):
            if not isinstance(artifact, dict) or not all(isinstance(artifact.get(k), str) for k in ("path", "hash", "mcp_hash", "xid")):
                raise ValueError("invalid migration artifact")
            if not artifact["path"].startswith(("skills/", "knowledge/imported_skills/")):
                raise ValueError("invalid migration artifact destination")
            _path(root, artifact["path"])
    return data


def _save(root: Path, data: dict[str, Any]) -> None:
    path = _path(root, STATE.as_posix())
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="migration-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _publish(destination: Path, prepared: Path) -> None:
    """Publish complete bytes exclusively; partial writes stay in a temp file."""
    fd, name = tempfile.mkstemp(prefix="migration-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(prepared.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, destination)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def _locked(root: Path) -> Iterator[None]:
    """OS-owned lock: a crashed process releases it, including on Windows."""
    path = _path(root, ".xrefkit/legacy-migration.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0)
        if not stream.read(1):
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _verified(root: Path, unit: dict[str, Any]) -> bool:
    artifacts = unit.get("artifacts", [])
    return unit["status"] == "installed" and bool(artifacts) and all(
        item.get("receipt") == item["hash"] and _path(root, item["path"]).is_file()
        and stable_hash(_path(root, item["path"]).read_text(encoding="utf-8")) == item["hash"]
        for item in artifacts
    )


def _remaining_unit(root: Path, unit: dict[str, Any]) -> dict[str, Any]:
    changed = unit["status"] == "installed" and any(
        not _path(root, a["path"]).is_file()
        or stable_hash(_path(root, a["path"]).read_text(encoding="utf-8")) != a["hash"]
        for a in unit.get("artifacts", [])
    )
    return {"target": unit["target"], "source": unit["source"],
            "status": "changed" if changed else unit["status"],
            "error": "Installed assets are missing or modified; preserve edits and recover explicitly." if changed else unit.get("error"),
            "retrievals": [{"tool": "get_document_by_xid", "xid": a["xid"]}
                           for a in unit.get("artifacts", []) if a.get("receipt") != a["hash"]]}


def migration_context(root: Path) -> dict[str, Any]:
    """Read-only and uncached, even when startup documents are cached."""
    try:
        data = _load(root)
        remaining = [_remaining_unit(root, item) for item in data["units"].values() if not _verified(root, item)]
        status = ("not_required" if data["decision"] == "not_required" and not data["units"]
                  else "in_progress" if remaining
                  else "completed" if data["units"] else "not_started")
        instructions = []
        if status == "not_started":
            instructions = [
                "Offer to migrate legacy shared XRefKit skills and knowledge in the user's language. "
                "Ask for the legacy source folder if unknown, then call plan_legacy_migration. "
                "Use natural intent; the user need not name a Skill. Run the returned client_import_command "
                "with --target for only the targets the user requests, using client-side Python. "
                "If the user confirms there are no legacy assets, call dismiss_legacy_migration.",
            ]
        elif status == "in_progress":
            instructions = [
                "Guide only the remaining migration targets below. Retry failed/prepared targets with "
                "the client_import_command with only those --target arguments; do not reimport verified targets. "
                "For installed targets retrieve each "
                "pending XID with get_document_by_xid (without known_version), or get_skill for Skill bodies. "
                "Conversion alone is not completion. Report conflicts instead of overwriting files.",
            ]
        return {"status": status, "state_path": STATE.as_posix(), "scope": "server_target_repository",
                "remaining": remaining, "client_instructions": instructions,
                "completion_basis": "all explicitly selected assets installed and body/hash retrieved via MCP",
                "client_import_commands": [
                    ["python", "-m", "xrefkit", "mcp", "migrate", "--repo", str(root.resolve()),
                     "--source", item["source"], "--target", item["target"], "--json"]
                    for item in remaining if item["status"] != "installed"
                ],
                "execution_boundary": "Run import commands only where the server target repository and source are accessible. Confirm the environment mapping for remote MCP; do not treat server paths as local client paths."}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status": "blocked", "state_path": STATE.as_posix(), "error": str(exc), "remaining": [],
                "client_instructions": ["Migration state could not be read. Preserve it and report the error; do not reset it or assume completion."]}


def plan_legacy_migration(root: Path, source: str) -> dict[str, Any]:
    from xrefkit.import_skill import _find_skill_doc

    root, source_path = root.resolve(), Path(source).resolve()
    if not source_path.is_dir():
        raise ValueError(f"legacy source folder does not exist on the MCP server: {source_path}")
    if source_path.is_relative_to(root) or root.is_relative_to(source_path):
        raise ValueError("legacy source and target must be separate, non-overlapping folders")
    targets: list[str] = []
    unsupported: list[str] = []
    if (source_path / "skills").is_dir():
        for folder in sorted((source_path / "skills").rglob("*")):
            if folder.is_dir() and any((folder / name).is_file() for name in ("SKILL.md", "skill.md", "README.md", "readme.md")):
                targets.append(folder.relative_to(source_path).as_posix())
        for path in sorted((source_path / "knowledge").rglob("*")):
            if path.is_file():
                (targets if path.suffix.lower() in {".md", ".txt"} else unsupported).append(path.relative_to(source_path).as_posix())
    else:
        try:
            _find_skill_doc(source_path, None)
            targets.append(".")
        except FileNotFoundError:
            if (source_path / "knowledge").is_dir():
                for path in sorted((source_path / "knowledge").rglob("*")):
                    if path.is_file():
                        (targets if path.suffix.lower() in {".md", ".txt"} else unsupported).append(path.relative_to(source_path).as_posix())
            else:
                raise ValueError("legacy source must contain skills/, knowledge/, or a Skill document")
    for target in targets:
        _path(source_path, target)
        folder = _path(source_path, target)
        if folder.is_dir():
            unsupported.extend(p.relative_to(source_path).as_posix() for p in folder.rglob("*")
                               if p.is_file() and p.suffix.lower() not in {".md", ".txt"})
    return {"source": str(source_path), "target_repository": str(root), "targets": targets,
            "unsupported": unsupported, "writes": False,
            "client_import_command": ["python", "-m", "xrefkit", "mcp", "migrate", "--repo", str(root),
                                      "--source", str(source_path), "--json"],
            "instruction": "Review the scope with the user. Append --target <exact-target> for each requested target and execute client-side. Run only where these folders are accessible; for remote MCP confirm the environment mapping. Source bytes are preserved."}


def _prepare(root: Path, stage: Path, source: Path, target: str, skill_id: str) -> dict[str, Any]:
    from xrefkit.import_skill import convert_skill, _knowledge_target_path, _knowledge_text

    namespace = hashlib.sha256(str(source).casefold().encode()).hexdigest()[:12]
    knowledge_dir = stage / "knowledge" / "imported_skills" / namespace
    source_path = _path(source, target)
    if source_path.is_dir():
        unsupported = [p.name for p in source_path.rglob("*") if p.is_file() and p.suffix.lower() not in {".md", ".txt"}]
        if unsupported:
            raise ValueError(f"Skill contains unsupported resources; preserve and migrate them separately: {', '.join(unsupported)}")
        result = convert_skill(source_dir=source_path, source_root=source, repo_root=stage,
                               skill_id=skill_id, target_skill_dir=stage / "skills" / skill_id,
                               target_knowledge_dir=knowledge_dir).to_dict()
        paths = [result["skill_doc"], result["meta_doc"],
                 *[item["target_path"] for item in result["imported_knowledge"]]]
    else:
        path = _knowledge_target_path(source_path, source, knowledge_dir)
        if not path.exists():
            text, _, _ = _knowledge_text(source_path, source, "legacy-migration", set())
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        paths = [path.relative_to(stage).as_posix()]
        result = {"imported_knowledge": [{"target_path": paths[0], "xid": first_xid(path.read_text(encoding="utf-8"))}]}
    artifacts = []
    for relative in paths:
        if Path(relative).suffix.lower() != ".md":
            raise ValueError(f"MCP cannot resolve this legacy document format: {relative}")
        text = _path(stage, relative).read_text(encoding="utf-8")
        xid = first_xid(text)
        if not xid:
            raise ValueError(f"converted artifact has no XID: {relative}")
        artifacts.append({"path": relative, "hash": stable_hash(text), "xid": xid,
                          "mcp_hash": stable_hash(markdown_xid_only_text(text))})
    return {"artifacts": artifacts, "result": result}


def import_legacy_assets(root: Path, source: str, targets: list[str], *,
                         prefix: str | None = None, single_skill_id: str | None = None) -> dict[str, Any]:
    """Explicit write operation. Durable staging allows retry after partial I/O."""
    from xrefkit.import_skill import _slug
    from .catalog import XRefCatalog, _managed_markdown_matches_by_xid

    root = root.resolve()
    plan = plan_legacy_migration(root, source)
    if not targets or any(item not in plan["targets"] for item in targets):
        raise ValueError("select one or more exact targets from plan_legacy_migration")
    source_path = Path(plan["source"])
    namespace = hashlib.sha256(str(source_path).casefold().encode()).hexdigest()[:12]
    stage = _path(root, (STAGING / namespace).as_posix())
    results: list[dict[str, Any]] = []
    with _locked(root):
        data = _load(root)
        data["decision"] = None
        # Persist the requested scope before conversion, including later targets
        # when an earlier target fails. Never infer scope from package versions.
        for target in dict.fromkeys(targets):
            key = f"{namespace}:{target}"
            data["units"].setdefault(key, {"source": str(source_path), "target": target,
                                         "status": "pending", "artifacts": []})
        _save(root, data)
        # Reuse previously assigned knowledge XIDs, including shared dependencies.
        for unit in data["units"].values():
            for a in unit.get("artifacts", []):
                destination = _path(stage, a["path"])
                original = _path(root, a["path"])
                if not destination.exists() and original.is_file() and stable_hash(original.read_text(encoding="utf-8")) == a["hash"]:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(original, destination)
        for target in dict.fromkeys(targets):
            unit = data["units"][f"{namespace}:{target}"]
            if unit["status"] == "installed" and all(
                _path(root, a["path"]).is_file()
                and stable_hash(_path(root, a["path"]).read_text(encoding="utf-8")) == a["hash"]
                for a in unit["artifacts"]
            ):
                results.append(unit.get("result", {}))
                continue
            try:
                if not unit.get("artifacts"):
                    local = _slug(source_path.name if target == "." else target.removeprefix("skills/"))
                    skill_id = single_skill_id or f"{_slug(prefix or ('legacy.' + namespace))}.{local}"
                    unit.update(_prepare(root, stage, source_path, target, skill_id))
                    unit["status"] = "prepared"
                    _save(root, data)
                # Preflight every destination before publishing any unit bytes.
                for a in unit["artifacts"]:
                    destination = _path(root, a["path"])
                    if destination.exists() and (not destination.is_file() or stable_hash(destination.read_text(encoding="utf-8")) != a["hash"]):
                        raise ValueError(f"refusing to overwrite existing asset: {a['path']}")
                    prepared = _path(stage, a["path"])
                    if not prepared.is_file() or stable_hash(prepared.read_text(encoding="utf-8")) != a["hash"]:
                        raise ValueError(f"prepared asset missing or changed: {a['path']}")
                    catalog = XRefCatalog.build(root)
                    matches = _managed_markdown_matches_by_xid(root, catalog.ownership, a["xid"])
                    if any(path.resolve() != destination.resolve() for path, _ in matches):
                        raise ValueError(f"existing catalog XID conflict: {a['xid']}")
                    if not matches:
                        try:
                            catalog.get_document_by_xid(a["xid"])
                        except KeyError:
                            pass
                        else:
                            raise ValueError(f"existing embedded XID conflict: {a['xid']}")
                    if any(other["xid"] == a["xid"] and other["path"] != a["path"]
                           for other in unit["artifacts"]):
                        raise ValueError(f"duplicate converted XID: {a['xid']}")
                for a in unit["artifacts"]:
                    destination = _path(root, a["path"])
                    if not destination.exists():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        _publish(destination, _path(stage, a["path"]))
                unit["status"] = "installed"
                unit.pop("error", None)
                results.append(unit["result"])
            except (OSError, ValueError) as exc:
                unit["status"] = "failed"
                unit["error"] = str(exc)
            _save(root, data)
    context = migration_context(root)
    return {"ok": all(data["units"][f"{namespace}:{t}"]["status"] == "installed" for t in targets),
            "converted_skills": [item for item in results if item.get("skill_id")],
            "unsupported": plan["unsupported"],
            "migration": context}


def record_mcp_retrieval(root: Path, documents: list[dict[str, Any]]) -> None:
    """Called only by successful MCP handlers, never CLI/catalog reads."""
    if not _path(root, STATE.as_posix()).exists():
        return
    with _locked(root):
        data = _load(root)
        changed = False
        for unit in data["units"].values():
            if unit["status"] != "installed":
                continue
            for artifact in unit["artifacts"]:
                for document in documents:
                    content = document.get("content")
                    if (isinstance(content, str) and document.get("xid") == artifact["xid"]
                            and document.get("path") in {None, artifact["path"]}
                            and stable_hash(content) == artifact["mcp_hash"]
                            and artifact.get("receipt") != artifact["hash"]):
                        artifact["receipt"] = artifact["hash"]
                        changed = True
        if changed:
            _save(root, data)


def dismiss_legacy_migration(root: Path) -> dict[str, Any]:
    with _locked(root):
        data = _load(root)
        if data["units"]:
            raise ValueError("cannot dismiss a migration with selected targets; finish or recover the remaining assets")
        data["decision"] = "not_required"
        _save(root, data)
    return migration_context(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit mcp migrate")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", action="append", required=True, help="Exact target from the migration inventory; repeatable")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = import_legacy_assets(Path(args.repo), args.source, args.target)
    except (OSError, ValueError) as exc:
        result = {"ok": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1
