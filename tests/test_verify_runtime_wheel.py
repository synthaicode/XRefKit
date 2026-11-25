import hashlib
from zipfile import ZipFile

import pytest

from tools.verify_runtime_wheel import verify_wheel


def make_wheel(directory, metadata_version="0.0.1"):
    wheel = directory / "xrefkit_openai_runtime-0.0.1-py3-none-any.whl"
    with ZipFile(wheel, "w") as archive:
        archive.writestr(
            "xrefkit_openai_runtime-0.0.1.dist-info/METADATA",
            f"Metadata-Version: 2.1\nName: xrefkit-openai-runtime\nVersion: {metadata_version}\n",
        )
    return wheel, hashlib.sha256(wheel.read_bytes()).hexdigest()


def test_verifies_exact_candidate_without_changing_bytes(tmp_path):
    wheel, digest = make_wheel(tmp_path)
    assert verify_wheel(tmp_path, "0.0.1", digest.upper()) == wheel
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("extra", ["runtime.tar.gz", ".hidden", "another.whl"])
def test_rejects_extra_upload_entries(tmp_path, extra):
    _, digest = make_wheel(tmp_path)
    (tmp_path / extra).touch()
    with pytest.raises(ValueError, match="exactly one"):
        verify_wheel(tmp_path, "0.0.1", digest)


def test_rejects_missing_or_modified_candidate(tmp_path):
    wheel, digest = make_wheel(tmp_path)
    with wheel.open("ab") as stream:
        stream.write(b"changed after acceptance")
    with pytest.raises(ValueError, match="SHA-256"):
        verify_wheel(tmp_path, "0.0.1", digest)
    wheel.unlink()
    with pytest.raises(ValueError, match="exactly one"):
        verify_wheel(tmp_path, "0.0.1", digest)


def test_rejects_identity_and_approval_mismatch(tmp_path):
    _, digest = make_wheel(tmp_path, metadata_version="0.0.2")
    with pytest.raises(ValueError, match="distribution identity"):
        verify_wheel(tmp_path, "0.0.1", digest)
    with pytest.raises(ValueError, match="wheel name or version"):
        verify_wheel(tmp_path, "0.0.2", digest)
    with pytest.raises(ValueError, match="SHA-256"):
        verify_wheel(tmp_path, "0.0.1", "")
