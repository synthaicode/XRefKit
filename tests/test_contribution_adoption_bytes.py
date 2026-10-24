"""Raw-byte preparation checks without human review, gate dispatch or adoption."""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest

from test_subagent_startup import command
from xrefkit import governance_entry
from xrefkit.mcp import contribution_returns as cr
from xrefkit.mcp.audit import SessionRunBinding
from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.mcp.update_gate_intake import prepare_contribution_gate
from xrefkit.ownership import Ownership, Zone


VARIANTS = [
    pytest.param(b"# Rule\nalpha\nbeta\n", id="LF"),
    pytest.param(b"# Rule\r\nalpha\r\nbeta\r\n", id="CRLF"),
    pytest.param(b"# Rule\ralpha\rbeta\r", id="CR"),
    pytest.param(b"# Rule\r\nalpha\nbeta\rgamma\r\n", id="mixed"),
    pytest.param("# 検証\n条件：日本語\n".encode(), id="nonASCII-LF"),
    pytest.param("# 検証\r\n条件：日本語\r\n".encode(), id="nonASCII-CRLF"),
]


def _pending(root: Path, raw: bytes) -> tuple[Path, dict]:
    content = "<!-- xid: BUG3TEST01 -->\n" + raw.decode("utf-8", errors="strict")
    identity = str(uuid.uuid4())
    cr.submit_contribution_return(
        root,
        binding=SessionRunBinding(str(uuid.uuid4()), str(uuid.uuid4()), "a" * 32, "sample"),
        source_snapshot={"provider_id": "xrefkit-mcp", "provider_version": "test",
                         "package_id": None, "package_version": None, "skill_id": "sample",
                         "skill_content_hash": "b" * 64, "knowledge_versions": [],
                         "verification": "matched_current_catalog"},
        contribution_id=identity, kind="knowledge", title="Byte fixture",
        summary="Unapproved preparation fixture", files=[{"path": "rule.md", "content": content,
        "content_hash": hashlib.sha256(content.encode()).hexdigest()}],
        knowledge={"xid": "BUG3TEST01"}, proposed_target_path="knowledge/byte_fixture.md",
    )
    record = root / cr.STORE_RELATIVE / identity
    return record, json.loads((record / "manifest.json").read_bytes())


def _inventory(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("raw", VARIANTS)
def test_stored_files_preserve_original_bytes_and_repeated_reads(tmp_path: Path, raw: bytes) -> None:
    record, manifest = _pending(tmp_path, raw)
    original = (record / "files/rule.md").read_bytes()
    before = _inventory(tmp_path)
    assert cr.list_contribution_returns(tmp_path)[0]["status"] == "pending_review"
    exported = cr.export_contribution_return(tmp_path, manifest["contribution_id"])
    assert exported["review_bundle"]["files"][0]["content"].encode() == original
    cr._verify_manifest_payload(record, manifest)
    first = cr._stored_files(record, manifest)
    assert first == cr._stored_files(record, manifest)
    assert first[0].content.encode("utf-8") == original
    assert first[0].content_hash == hashlib.sha256(original).hexdigest()
    assert manifest["files"][0]["byte_count"] == len(original)
    # This is the same encode used by gate intake, without bypassing its approval gate.
    staged = tmp_path / "scratch/unapproved-candidate.md"
    staged.parent.mkdir()
    staged.write_bytes(first[0].content.encode("utf-8"))
    assert staged.read_bytes() == original
    staged.unlink()
    assert _inventory(tmp_path) == before
    assert not (record / "events").exists()
    assert not (tmp_path / "knowledge").exists()


@pytest.mark.parametrize("corruption", ["hash", "byte_count", "invalid_utf8", "changed_bytes", "missing", "newline_only"])
def test_stored_files_reject_corrupt_candidate(tmp_path: Path, corruption: str) -> None:
    record, manifest = _pending(tmp_path, b"# Rule\nbody\n")
    stored = record / "files/rule.md"
    if corruption == "hash":
        manifest["files"][0]["content_hash"] = "0" * 64
    elif corruption == "byte_count":
        manifest["files"][0]["byte_count"] += 1
    elif corruption == "invalid_utf8":
        invalid = stored.read_bytes() + b"\xff"
        stored.write_bytes(invalid)
        manifest["files"][0].update(content_hash=hashlib.sha256(invalid).hexdigest(), byte_count=len(invalid))
    elif corruption == "changed_bytes":
        stored.write_bytes(stored.read_bytes() + b"tamper")
    elif corruption == "newline_only":
        stored.write_bytes(stored.read_bytes().replace(b"\n", b"\r\n"))
    else:
        stored.unlink()
    before = _inventory(tmp_path)
    with pytest.raises((ValueError, FileNotFoundError)):
        cr._stored_files(record, manifest)
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize("corruption", ["payload", "extra_file", "deleted_file", "byte_count", "metadata_xid_tamper"])
def test_preparation_verifier_retains_manifest_and_tree_rejections(tmp_path: Path, corruption: str) -> None:
    record, manifest = _pending(tmp_path, b"# Rule\nbody\n")
    if corruption == "payload":
        manifest["summary"] += " tampered"
    elif corruption == "extra_file":
        (record / "files/extra.md").write_bytes(b"extra")
    elif corruption == "deleted_file":
        (record / "files/rule.md").unlink()
    elif corruption == "byte_count":
        manifest["files"][0]["byte_count"] += 1
    else:
        manifest["kind_metadata"]["xid"] = "UNLISTED01"
    before = _inventory(tmp_path)
    with pytest.raises(ValueError):
        cr._verify_manifest_payload(record, manifest)
    assert _inventory(tmp_path) == before


class _ReadOnlyTargetRoot:
    """Route a logical target to a real scratch file; never create canonical paths."""
    def __init__(self, target: Path):
        self.target = target

    def joinpath(self, *parts: str) -> Path:
        assert parts == ("knowledge", "byte_fixture.md")
        return self.target


def _target_check(target: Path, raw: bytes, **changes) -> str:
    xid = "BUG3TEST01"
    logical = "knowledge/byte_fixture.md"
    kwargs = dict(ownership=Ownership((Zone("kernel-content", "base", ("knowledge/",), True,
                                          True, True, False),)),
                  existing_knowledge_xids={xid}, existing_knowledge_xid_locations={xid: {logical}},
                  repository_xid_paths={xid: {logical}}, allow_same_xid_after_prepare=True)
    kwargs.update(changes)
    return cr._validate_canonical_target(
        _ReadOnlyTargetRoot(target),
        {"kind": "knowledge", "kind_metadata": {"xid": xid},
         "files": [{"content_hash": hashlib.sha256(raw).hexdigest(), "byte_count": len(raw)}]},
        logical, **kwargs,
    )


@pytest.mark.parametrize("raw", VARIANTS)
def test_recovery_target_matches_raw_hash_without_newline_conversion(tmp_path: Path, raw: bytes) -> None:
    target = tmp_path / "scratch-target.md"
    target.write_bytes(raw)
    before = target.read_bytes()
    assert _target_check(target, raw) == "knowledge/byte_fixture.md"
    assert target.read_bytes() == before
    assert not (tmp_path / "knowledge").exists()


@pytest.mark.parametrize("mismatch", ["target_version", "expected_hash", "duplicate_xid", "unlocated_xid", "no_prepare", "missing_target", "newline_only"])
def test_recovery_retains_collision_and_version_rejections(tmp_path: Path, mismatch: str) -> None:
    original = b"# Original\nbody\n"
    target = tmp_path / "scratch-target.md"
    target.write_bytes(original)
    expected = original
    changes = {}
    if mismatch == "target_version":
        target.write_bytes(b"# Other version\nbody\n")
    elif mismatch == "newline_only":
        target.write_bytes(original.replace(b"\n", b"\r\n"))
    elif mismatch == "expected_hash":
        expected = b"# Different expected base\nbody\n"
    elif mismatch == "duplicate_xid":
        changes["repository_xid_paths"] = {"BUG3TEST01": {"knowledge/byte_fixture.md", "knowledge/other.md"}}
    elif mismatch == "unlocated_xid":
        changes["unlocated_existing_knowledge_xids"] = {"BUG3TEST01"}
    elif mismatch == "no_prepare":
        changes["allow_same_xid_after_prepare"] = False
    else:
        target.unlink()
    before = _inventory(tmp_path)
    with pytest.raises(ValueError, match="Knowledge XID already exists"):
        _target_check(target, expected, **changes)
    assert _inventory(tmp_path) == before


def test_gate_preparation_requires_real_approval_and_leaves_pending_state(tmp_path: Path) -> None:
    record, manifest = _pending(tmp_path, b"# Rule\r\nbody\r\n")
    before = _inventory(tmp_path)
    with pytest.raises(RuntimeError, match="trusted human approval verifier"):
        prepare_contribution_gate(tmp_path, contribution_id=manifest["contribution_id"],
                                  log="work/not-created.md", binding_request={},
                                  specialist_evidence=[], approval_verifier=None)
    assert _inventory(tmp_path) == before
    assert not (record / "events").exists()
    assert not (tmp_path / "knowledge").exists()


def test_unsigned_gate_packet_revalidation_rejects_wrong_base_hash(tmp_path: Path) -> None:
    log = tmp_path / "work/run.md"
    code, output = command("workflow", "run", "--root", str(tmp_path), "--task",
                           "Unsigned base hash regression fixture", "--out", str(log),
                           "--completion-condition", "read-only packet checked", "--json")
    assert code == 0, output
    code, output = command("skill", "workitem", "--log", str(log), "--item", "WI-BASE",
                           "--text", "Validate unsigned frozen packet", "--completion-criterion",
                           "base mismatch rejected without writing target", "--status", "pending",
                           "--role", "instruction:executor", "--json")
    assert code == 0, output
    paths = ["work/candidate.md", *sorted(governance_entry.RULE_SOURCES)]
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"# Isolated unsigned packet material\r\n")
    request = {"work_item_id": "WI-BASE", "source_mode": "filesystem", "purpose": "base hash test",
               "capability": "analysis", "tuning": "read-only fixture", "responsibility": "reject changed base",
               "instruction_basis": "Authorized BUG3 regression scope", "scope_in": paths,
               "scope_out": ["approval", "dispatch", "adoption"], "stop_conditions": ["unexpected write"],
               "protocols": ["workflow"], "knowledge_access": {"mode": "on_demand", "catalog": "work/index.md"}}
    packet = governance_entry.prepare(
        tmp_path, kind="asset_update", log="work/run.md", binding_request=request, materials=paths,
        payload={"candidate": "work/candidate.md", "target": "knowledge/not-created.md",
                 "rules": sorted(governance_entry.RULE_SOURCES), "checks": sorted(governance_entry.CORE_CHECKS),
                 "specialist_evidence": []},
    )
    assert packet["payload"]["expected_target_hash"] is None
    before = _inventory(tmp_path)
    governance_entry.revalidate(tmp_path, packet)
    packet["payload"]["expected_target_hash"] = "0" * 64
    # Packet digest is an unsigned content digest, never human authority or a host receipt.
    packet["packet_hash"] = governance_entry.digest({k: v for k, v in packet.items() if k != "packet_hash"})
    with pytest.raises(ValueError, match="target baseline changed"):
        governance_entry.revalidate(tmp_path, packet)
    assert _inventory(tmp_path) == before
    assert not (tmp_path / "knowledge").exists()


def test_nonexistent_xid_lookup_does_not_invent_a_document(tmp_path: Path) -> None:
    before = _inventory(tmp_path)
    with pytest.raises(KeyError, match="document xid not found: ABCDEF987654"):
        XRefCatalog.build(tmp_path).get_document_by_xid("ABCDEF987654")
    assert _inventory(tmp_path) == before
