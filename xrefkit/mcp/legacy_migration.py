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
    current = candidate
    while current != root and current != current.parent:
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise ValueError(f"migration path contains a link: {relative}")
        current = current.parent
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
    if unit.get("resource_bundle"):
        record = unit.get("verification_workflow", {}).get("record")
        if not isinstance(record, str) or _verification_errors(record, unit["resource_bundle"]["manifest_hash"]):
            return False
        from .legacy_resources import read_resource_manifest, manifest_hash, validate_resource_manifest
        try:
            bundle_root, manifest = read_resource_manifest(root, unit["resource_bundle"]["namespace"])
            if manifest_hash(manifest) != unit["resource_bundle"]["manifest_hash"]:
                return False
            validate_resource_manifest(manifest, {row["path"]: _path(bundle_root, row["path"]).read_bytes() for row in manifest["files"]})
        except (OSError, ValueError, KeyError):
            return False
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
            "resource_bundle": unit.get("resource_bundle"),
            "verification_requirement": "Submit the existing migration Skill Run record after its deterministic closure gate passes with all migration work items done; baseline/business/client unknowns do not pass" if unit.get("resource_bundle") else None,
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
                "The new connected AI starts this work; no old-environment AI or manually prepared tests are required. "
                "Ask for the legacy source folder if unknown. For a client-local source or Python resources, "
                "run python -m xrefkit mcp migrate inspect --source <client-folder> on the client; "
                "then use migrate prepare with selected Skills/resources and an opened Skill Run --log. "
                "Inventory shared tools, modules, data, tests and dependencies; prepare missing tests safely, "
                "capture an observed baseline where accessible, and retain unknown business expectations for human judgment. "
                "Upload the prepared bundle via contribution upload/seal and existing human review/adoption, "
                "register_legacy_bundle, then fetch hash-pinned files to the client and verify behavior. "
                "Do not execute arbitrary legacy code until test isolation or safe mode is established. "
                "For document-only sources accessible on the server, plan_legacy_migration and its returned import command remain supported. "
                "If the user confirms there are no legacy assets, call dismiss_legacy_migration.",
            ]
        elif status == "in_progress":
            instructions = [
                "Guide only the remaining migration targets below. Retry failed/prepared targets with "
                "the client_import_command with only those --target arguments; do not reimport verified targets. "
                "For installed targets retrieve each "
                "pending XID with get_document_by_xid (without known_version), or get_skill for Skill bodies. "
                "Conversion alone is not completion. Report conflicts instead of overwriting files.",
                "For resource_bundle units, resume the linked migration Skill Run work items and use "
                "register_legacy_bundle with the adopted contribution_id; server paths are not client paths. "
                "Resource verification remains pending until the existing workflow closure record is submitted. "
                "Missing baselines, client tests or business judgments must not be reported as passing.",
            ]
        return {"status": status, "state_path": STATE.as_posix(), "scope": "server_target_repository",
                "remaining": remaining, "client_instructions": instructions,
                "completion_basis": "all selected document bodies retrieved via MCP; resource migrations additionally require unchanged pinned files and completed migration work items in a deterministically closed Skill Run (record-level evidence, not independent proof of business correctness)",
                "client_import_commands": [
                    ["python", "-m", "xrefkit", "mcp", "migrate", "--repo", str(root.resolve()),
                     "--source", item["source"], "--target", item["target"], "--json"]
                    for item in remaining if item["status"] != "installed" and not item.get("resource_bundle")
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


def _prepare(root: Path, stage: Path, source: Path, target: str, skill_id: str,
             resource_bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    from xrefkit.import_skill import convert_skill, _knowledge_target_path, _knowledge_text

    namespace = hashlib.sha256(str(source).casefold().encode()).hexdigest()[:12]
    knowledge_dir = stage / "knowledge" / "imported_skills" / namespace
    source_path = _path(source, target)
    if source_path.is_dir():
        unsupported = [p.name for p in source_path.rglob("*") if p.is_file() and p.suffix.lower() not in {".md", ".txt"}]
        if unsupported and resource_bundle is None:
            raise ValueError(f"Skill contains unsupported resources; preserve and migrate them separately: {', '.join(unsupported)}")
        result = convert_skill(source_dir=source_path, source_root=source, repo_root=stage,
                               skill_id=skill_id, target_skill_dir=stage / "skills" / skill_id,
                               target_knowledge_dir=knowledge_dir,
                               source_skill_doc="SKILL.v1.md" if (source_path / "SKILL.v1.md").is_file() else None).to_dict()
        paths = [result["skill_doc"], result["meta_doc"],
                 *[item["target_path"] for item in result["imported_knowledge"]]]
        if resource_bundle is not None:
            result["client_resources"] = {**resource_bundle, "source_skill": target}
            document = _path(stage, result["skill_doc"])
            text = document.read_text(encoding="utf-8")
            text += ("\n\n## Migrated client resources\n\n"
                     f"This Skill uses resource bundle `{resource_bundle['namespace']}` at version "
                     f"`{resource_bundle['version']}`. Fetch its manifest and files through "
                     "`get_legacy_resource_manifest` and `get_legacy_resource_file`, validate and "
                     "materialize them with the XRefKit Python client. Run legacy commands with the "
                     "materialized bundle root as working directory; original relative paths and "
                     "shared imports are preserved. Execution occurs only on the client. "
                     "Review dependencies, configuration, test safety, observed baseline and "
                     "business-approved expectations in the migration Skill Run before execution. "
                     "Resource adoption and document retrieval do not establish behavioral correctness.\n")
            document.write_text(text, encoding="utf-8")
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
                         prefix: str | None = None, single_skill_id: str | None = None,
                         _resource_bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    """Explicit write operation. Durable staging allows retry after partial I/O."""
    from xrefkit.import_skill import _slug
    from .catalog import XRefCatalog, _managed_markdown_matches_by_xid

    root = root.resolve()
    if _resource_bundle is None:
        plan = plan_legacy_migration(root, source)
    else:
        # Only register_legacy_bundle supplies this internal, verified source.
        source_path = _path(root, "tools/" + _resource_bundle["namespace"])
        if Path(source).resolve() != source_path.resolve():
            raise ValueError("resource bundle source does not match verified namespace")
        plan = {"source": str(source_path), "targets": _resource_bundle["targets"], "unsupported": []}
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
            if _resource_bundle is not None:
                data["units"][key]["resource_bundle"] = {**_resource_bundle, "source_skill": target}
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
                    unit.update(_prepare(root, stage, source_path, target, skill_id, _resource_bundle))
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


def _verification_errors(record: str, version: str) -> list[str]:
    """Reuse runtime closure and concrete work items, not caller pass booleans."""
    from types import SimpleNamespace
    from xrefkit.skillrun import _progression_record_errors, _section_status, close_skill_run
    from .legacy_guidance import migration_tasks

    errors, items, _, _, _ = _progression_record_errors(record)
    errors = list(errors)
    if _section_status(record, "Closure Gate") != "done":
        errors.append("migration Skill Run must have a completed Closure Gate")
    # Replay the existing deterministic closure gate on a disposable copy. This
    # checks roles/phases/concerns without changing the submitted client record.
    with tempfile.TemporaryDirectory(prefix="xrefkit-migration-check-") as temp:
        path = Path(temp) / "run.md"
        path.write_text(record, encoding="utf-8")
        closure = close_skill_run(SimpleNamespace(log=str(path), note="migration record verification"))
        errors.extend(closure.errors)
        if closure.ok and _section_status(path.read_text(encoding="utf-8"), "Closure Gate") != "done":
            errors.append("escalated migration closure is not completed verification")
    actual = {item["item_id"]: item for item in items}
    for task in migration_tasks(version):
        item = actual.get(task["item_id"], {})
        if item.get("status") != "done" or item.get("criterion") != task["completion_criterion"]:
            errors.append(f"migration work item is incomplete or criterion differs: {task['item_id']}")
    return errors


def register_legacy_bundle(root: Path, contribution_id: str, *, approval_verifier: Any,
                           verification_workflow: str | None = None) -> dict[str, Any]:
    """Register only exact bytes already adopted by existing contribution governance.

    Client source paths are never interpreted on the server. Signed adoption is
    the authority for this source; imported documents retain draft readiness.
    """
    from .contribution_returns import (
        STORE_RELATIVE, ADOPTION_SCHEMA, REVIEW_SCHEMA, _uuid, _read_manifest,
        _read_event, _verify_manifest_payload, _verify_review_binding,
    )
    from .legacy_resources import read_resource_manifest, manifest_hash, validate_resource_manifest

    root = root.resolve()
    contribution_id = _uuid(contribution_id)
    record_dir = _path(root, (STORE_RELATIVE / contribution_id).as_posix())
    contribution = _read_manifest(record_dir / "manifest.json")
    _verify_manifest_payload(record_dir, contribution)
    review = _read_event(record_dir / "events" / "review.json", REVIEW_SCHEMA, approval_verifier=approval_verifier)
    adoption = _read_event(record_dir / "events" / "adoption.json", ADOPTION_SCHEMA, approval_verifier=approval_verifier)
    _verify_review_binding(contribution, review)
    if (contribution.get("kind") != "deterministic_tool" or review.get("decision") != "accepted"
            or adoption.get("status") != "adopted" or adoption.get("contribution_id") != contribution_id
            or adoption.get("payload_hash") != contribution["payload_hash"]
            or adoption.get("review_binding_hash") != review.get("review_binding_hash")):
        raise ValueError("legacy registration requires the exact accepted and adopted tool contribution")
    target = adoption["canonical_target"]
    parts = Path(target).parts
    if len(parts) != 2 or parts[0] != "tools":
        raise ValueError("legacy resource adoption target must be tools/<namespace>")
    namespace = parts[1]
    bundle_root, manifest = read_resource_manifest(root, namespace)
    signed_files = {row["path"]: row["content_hash"] for row in adoption["canonical_files"]}
    expected_files = {f"{target}/{row['path']}": row["content_hash"] for row in contribution["files"]}
    if signed_files != expected_files:
        raise ValueError("adopted file identity differs from contribution")
    actual_files = set()
    for path in bundle_root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        _path(root, relative)  # reject every link, including otherwise unused entries
        if path.is_file():
            actual_files.add(relative)
    if actual_files != set(signed_files):
        raise ValueError("adopted legacy tree contains missing or unapproved files")
    for path, expected_hash in signed_files.items():
        if hashlib.sha256(_path(root, path).read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"adopted legacy bytes changed: {path}")
    content = {row["path"]: _path(bundle_root, row["path"]).read_bytes() for row in manifest["files"]}
    validate_resource_manifest(manifest, content)
    if set(signed_files) != {f"{target}/{path}" for path in content} | {f"{target}/legacy-resources.json"}:
        raise ValueError("adopted bundle and resource manifest file sets differ")
    targets = [row["source"] for row in manifest["skills"]]
    if not targets or len(targets) != len(set(targets)):
        raise ValueError("legacy manifest must identify distinct selected Skills")
    if verification_workflow is not None:
        if len(verification_workflow.encode("utf-8")) > 1024 * 1024:
            raise ValueError("migration workflow record exceeds size limit")
        errors = _verification_errors(verification_workflow, manifest_hash(manifest))
        if errors:
            raise ValueError("; ".join(errors))
    resource_bundle = {"namespace": namespace, "version": manifest["version"],
                       "manifest_hash": manifest_hash(manifest), "targets": targets,
                       "contribution_id": contribution_id}
    result = import_legacy_assets(root, str(bundle_root), targets, prefix=f"legacy.{namespace}",
                                  _resource_bundle=resource_bundle)
    if verification_workflow is not None and result["ok"]:
        with _locked(root):
            state = _load(root)
            for unit in state["units"].values():
                if unit.get("resource_bundle", {}).get("contribution_id") == contribution_id:
                    unit["verification_workflow"] = {"record": verification_workflow,
                        "content_hash": hashlib.sha256(verification_workflow.encode()).hexdigest()}
            _save(root, state)
        result["migration"] = migration_context(root)
    return {**result, "client_resources": resource_bundle,
            "behavior_verification": "workflow_recorded" if verification_workflow is not None else "pending",
            "skill_readiness": "imported draft; existing readiness/authoring gates still apply, no automatic promotion",
            "business_correctness": "requires human judgment in the migration workflow"}


def main(argv: list[str] | None = None) -> int:
    if argv and argv[0] in {"inspect", "prepare", "fetch"}:
        from .legacy_guidance import main as guidance_main
        return guidance_main(argv)
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
