"""Verify the contents of the Runtime upload directory against the accepted wheel."""

from email.parser import BytesParser
import hashlib
import os
from pathlib import Path
import re
from zipfile import ZipFile


def verify_wheel(directory: Path, version: str, expected_sha256: str) -> Path:
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("expected a SHA-256 recorded for the accepted wheel")
    entries = list(directory.iterdir())
    if len(entries) != 1:
        raise ValueError("upload directory must contain exactly one wheel")
    wheel = entries[0]
    if wheel.is_symlink() or not wheel.is_file() or wheel.suffix != ".whl":
        raise ValueError("expected a regular wheel file")
    fields = wheel.stem.split("-")
    if len(fields) not in (5, 6) or fields[:2] != ["xrefkit_openai_runtime", version]:
        raise ValueError("unexpected wheel name or version")
    with wheel.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != expected_sha256.lower():
            raise ValueError("wheel differs from the accepted SHA-256")
    with ZipFile(wheel) as archive:
        metadata = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if metadata != [f"xrefkit_openai_runtime-{version}.dist-info/METADATA"]:
            raise ValueError("unexpected wheel metadata path")
        headers = BytesParser().parsebytes(archive.read(metadata[0]), headersonly=True)
    if headers.get_all("Name") != ["xrefkit-openai-runtime"] or headers.get_all("Version") != [version]:
        raise ValueError("unexpected distribution identity")
    return wheel


if __name__ == "__main__":
    accepted = verify_wheel(Path("dist"), os.environ["EXPECTED_VERSION"], os.environ["EXPECTED_SHA256"])
    print(f"Verified {accepted.name} SHA-256 {os.environ['EXPECTED_SHA256'].lower()}")
