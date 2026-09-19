import copy
import hashlib
import json

import pytest

from xrefkit.skill_definition import parse_skill_definition, load_skill_definition
from xrefkit.skill_definition_catalog import build_definition_catalog
from test_subagent_startup import command


@pytest.fixture
def metadata():
    return {"schema_version": 1, "skill_id": "sample_skill", "xid": "ABCDEF123456",
            "summary": "Inspect a bounded target", "applies_when": ["analysis requested"],
            "exclusions": [], "inputs": ["target"], "outputs": ["report"],
            "criteria": [{"id": "coverage", "statement": "Every target is accounted for", "verification": "Compare inventory"}],
            "knowledge_needs": [{"id": "rules", "query": "applicable local rules", "required_when": "analysis",
                                  "seed_xids": ["123456ABCDEF"]}],
            "control_refs": ["B7A2C94F0E61"], "aliases": ["FFFFFFFFFFFF"]}


def text_for(metadata, method=None):
    if method is None:
        xid = metadata["xid"]
        method = f'<!-- xid: {xid} -->\n<a id="xid-{xid}"></a>\n\n# Method\nSECRET_METHOD_SENTINEL\n'
    return "---\n" + json.dumps(metadata) + "\n---\n" + method


def test_preserves_method_and_hash(metadata, tmp_path):
    text = text_for(metadata).replace("\n", "\r\n")
    parsed = parse_skill_definition(text)
    assert parsed["method"] == text.split("---\r\n", 2)[2]
    assert parsed["content_hash"] == hashlib.sha256(text.encode()).hexdigest()
    path = tmp_path / "SKILL.md"
    raw = b"\xef\xbb\xbf" + text.encode()
    path.write_bytes(raw)
    loaded = load_skill_definition(path)
    assert loaded["content_hash"] == hashlib.sha256(raw).hexdigest()
    assert loaded["method"] == parsed["method"]


def test_control_refs_may_be_empty(metadata):
    metadata["control_refs"] = []
    parsed = parse_skill_definition(text_for(metadata))
    assert parsed["metadata"]["control_refs"] == []


@pytest.mark.parametrize("key,value", [
    ("schema_version", True), ("schema_version", 2), ("skill_id", "Bad-ID"),
    ("xid", "not-an-xid"), ("summary", ""), ("applies_when", []),
    ("inputs", [{}]), ("outputs", "report"), ("criteria", []),
    ("knowledge_needs", [{"id": "missing"}]),
    ("control_refs", ["B7A2C94F0E61", "B7A2C94F0E61"]),
    ("aliases", ["ABCDEF123456"]), ("capability", "must be dynamic"),
    ("tuning", "must be dynamic"), ("responsibility", "must be dynamic"),
    ("model", "fixed model"),
])
def test_invalid_metadata_rejected(metadata, key, value):
    metadata[key] = value
    with pytest.raises(ValueError):
        parse_skill_definition(text_for(metadata))


@pytest.mark.parametrize("field", ["criteria", "knowledge_needs"])
def test_duplicate_nested_ids_rejected(metadata, field):
    metadata[field].append(copy.deepcopy(metadata[field][0]))
    with pytest.raises(ValueError):
        parse_skill_definition(text_for(metadata))


@pytest.mark.parametrize("header", [
    'schema_version: 1\nschema_version: 1',
    'criteria: [{id: a, id: b}]',
    'schema_version: &a [*a]',
    'schema_version: !!python/object/apply:os.system ["never execute"]',
    '1: value',
    '[not, a, mapping]',
])
def test_unsafe_or_duplicate_yaml_rejected(header):
    with pytest.raises(ValueError):
        parse_skill_definition("---\n" + header + "\n---\n# Body")


@pytest.mark.parametrize("method", ["", "# Missing identity", '<!-- xid: ABCDEF123456 -->\n# Missing anchor'])
def test_body_identity_required(metadata, method):
    with pytest.raises(ValueError):
        parse_skill_definition(text_for(metadata, method))


def test_limits_and_invalid_utf8(metadata, tmp_path):
    with pytest.raises(ValueError):
        parse_skill_definition(text_for(metadata) + "x" * 256001)
    metadata["summary"] = "x" * 64001
    with pytest.raises(ValueError):
        parse_skill_definition(text_for(metadata))
    path = tmp_path / "bad.md"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(ValueError):
        load_skill_definition(path)


def test_catalog_is_metadata_only_and_deterministic(metadata, tmp_path):
    one, two = tmp_path / "one.md", tmp_path / "two.md"
    one.write_text(text_for(metadata), encoding="utf-8")
    other = copy.deepcopy(metadata)
    other.update(skill_id="another_skill", xid="111111111111", aliases=[])
    two.write_text(text_for(other), encoding="utf-8")
    a = build_definition_catalog([one, two])
    b = build_definition_catalog([two, one])
    assert a == b
    assert "SECRET_METHOD_SENTINEL" not in json.dumps(a)
    assert [v["skill_id"] for v in a["entries"]] == ["another_skill", "sample_skill"]
    assert a["xid_index"]["FFFFFFFFFFFF"] == "sample_skill"
    assert a["xid_index"]["ABCDEF123456"] == "sample_skill"
    one.write_text(text_for(metadata) + "Changed method", encoding="utf-8")
    assert build_definition_catalog([one, two])["catalog_hash"] != a["catalog_hash"]


@pytest.mark.parametrize("collision", ["id", "xid", "alias"])
def test_catalog_identity_collision_rejected(metadata, tmp_path, collision):
    one, two = tmp_path / "one.md", tmp_path / "two.md"
    one.write_text(text_for(metadata), encoding="utf-8")
    other = copy.deepcopy(metadata)
    other.update(skill_id="other", xid="111111111111", aliases=[])
    if collision == "id": other["skill_id"] = metadata["skill_id"]
    if collision == "xid": other["xid"] = metadata["xid"]
    if collision == "alias": other["aliases"] = [metadata["xid"]]
    two.write_text(text_for(other), encoding="utf-8")
    with pytest.raises(ValueError): build_definition_catalog([one, two])


def test_cli_does_not_expose_body(metadata, tmp_path):
    path = tmp_path / "SKILL.md"
    path.write_text(text_for(metadata), encoding="utf-8")
    for cmd in ["definition-check", "definition-catalog"]:
        code, output = command("skill", cmd, "--path", str(path), "--json")
        assert code == 0, output
        assert "SECRET_METHOD_SENTINEL" not in output
    path.write_text("malformed", encoding="utf-8")
    code, output = command("skill", "definition-check", "--path", str(path))
    assert code == 1
    assert json.loads(output)["state"] == "blocked"


@pytest.mark.parametrize("field", ["xid", "aliases", "control_refs", "knowledge_needs"])
def test_nonhex_uppercase_xids_rejected(metadata, field):
    invalid = "G" * 12
    if field == "xid": metadata[field] = invalid
    elif field == "knowledge_needs": metadata[field][0]["seed_xids"] = [invalid]
    else: metadata[field] = [invalid]
    with pytest.raises(ValueError): parse_skill_definition(text_for(metadata))


def test_deep_yaml_rejected_as_validation_error():
    header = "summary: " + "[" * 1000 + "0" + "]" * 1000
    with pytest.raises(ValueError): parse_skill_definition("---\n" + header + "\n---\n# body")
