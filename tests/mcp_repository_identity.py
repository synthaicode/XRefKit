from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.mcp.repository import repository_fingerprint, repository_identity


def git(cwd: Path, *arguments: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@example.test",
            "-c",
            "user.name=test",
            *arguments,
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def make_commit(repo: Path, name: str, content: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-m", f"add {name}")


class RepositoryIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_non_git_directory_falls_back_to_path_basis(self) -> None:
        plain = self.root / "plain"
        plain.mkdir()

        fingerprint, basis = repository_identity(plain)

        self.assertEqual(basis, "resolved_repository_root")
        normalized = plain.resolve().as_posix().casefold()
        expected = hashlib.sha256(
            f"resolved-repository-root:{normalized}".encode("utf-8")
        ).hexdigest()[:32]
        self.assertEqual(fingerprint, expected)

    def test_git_repo_without_commits_falls_back_to_path_basis(self) -> None:
        repo = self.root / "empty"
        repo.mkdir()
        git(repo, "init", "-q")

        _fingerprint, basis = repository_identity(repo)

        self.assertEqual(basis, "resolved_repository_root")

    def test_git_repo_uses_root_commit_basis(self) -> None:
        repo = self.root / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        make_commit(repo, "a.md", "first\n")

        fingerprint, basis = repository_identity(repo)

        self.assertEqual(basis, "git_root_commits")
        root_commit = git(repo, "rev-list", "--max-parents=0", "HEAD")
        expected = hashlib.sha256(
            f"git-root-commits:{root_commit}".encode("utf-8")
        ).hexdigest()[:32]
        self.assertEqual(fingerprint, expected)

    def test_fingerprint_is_stable_across_later_commits(self) -> None:
        repo = self.root / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        make_commit(repo, "a.md", "first\n")
        before = repository_fingerprint(repo)

        make_commit(repo, "b.md", "second\n")

        self.assertEqual(repository_fingerprint(repo), before)

    def test_clone_at_different_path_shares_fingerprint(self) -> None:
        origin = self.root / "origin"
        origin.mkdir()
        git(origin, "init", "-q")
        make_commit(origin, "a.md", "first\n")
        clone = self.root / "somewhere-else" / "clone"
        clone.parent.mkdir()
        git(self.root, "clone", "-q", origin.as_uri(), str(clone))

        self.assertEqual(
            repository_fingerprint(clone),
            repository_fingerprint(origin),
        )
        self.assertEqual(repository_identity(clone)[1], "git_root_commits")

    def test_shallow_clone_falls_back_to_path_basis(self) -> None:
        origin = self.root / "origin"
        origin.mkdir()
        git(origin, "init", "-q")
        make_commit(origin, "a.md", "first\n")
        make_commit(origin, "b.md", "second\n")
        shallow = self.root / "shallow"
        git(self.root, "clone", "-q", "--depth", "1", origin.as_uri(), str(shallow))

        fingerprint, basis = repository_identity(shallow)

        self.assertEqual(basis, "resolved_repository_root")
        self.assertNotEqual(fingerprint, repository_fingerprint(origin))

    def test_catalog_identity_reports_basis_and_scope(self) -> None:
        repo = self.root / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        make_commit(repo, "a.md", "first\n")

        identity = XRefCatalog.build(repo).get_repository_identity()

        self.assertEqual(identity["fingerprint_basis"], "git_root_commits")
        self.assertEqual(identity["fingerprint_scope"], "shared_across_clones")
        self.assertEqual(len(identity["repository_fingerprint"]), 32)
        self.assertEqual(
            identity["cache_namespace"],
            identity["repository_fingerprint"],
        )

    def test_catalog_identity_for_plain_directory_is_local_scope(self) -> None:
        plain = self.root / "plain"
        plain.mkdir()

        identity = XRefCatalog.build(plain).get_repository_identity()

        self.assertEqual(identity["fingerprint_basis"], "resolved_repository_root")
        self.assertEqual(identity["fingerprint_scope"], "local_path_only")


if __name__ == "__main__":
    unittest.main()
