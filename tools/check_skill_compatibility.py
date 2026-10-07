"""Fail closed on official Skill compatibility with the exact Core release wheel.

Published PyPI wheels and repository candidates are distinct scopes. Neither
scope can replace the other at Core publication. The inventory is reconciled
against every entry-point-bearing package project, including source-only ones.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import venv
import xml.etree.ElementTree as ET
import zipfile
from email.parser import BytesParser
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version


class GateError(Exception):
    def __init__(self, status: str, reason: str):
        super().__init__(reason)
        self.status = status


def inventory(repo: Path) -> list[dict]:
    value = json.loads((repo / "tools/official_skill_packages.json").read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise GateError("inventory_error", "unsupported inventory schema")
    packages = value["packages"]
    declared = {}
    for project in (repo / "packages").rglob("pyproject.toml"):
        if any(part in {"build", "dist", ".venv", "venv"} for part in project.relative_to(repo).parts):
            continue
        data = tomllib.loads(project.read_text(encoding="utf-8"))["project"]
        if data.get("entry-points", {}).get("xrefkit.skill_packages"):
            name = canonicalize_name(data["name"])
            if name in declared:
                raise GateError("inventory_error", f"duplicate project: {name}")
            declared[name] = project.parent.relative_to(repo).as_posix()
    names = [canonicalize_name(p["name"]) for p in packages]
    if len(set(names)) != len(names) or set(names) != set(declared):
        raise GateError("inventory_error", "official inventory does not match all Skill entry-point projects")
    if not packages:
        raise GateError("inventory_error", "official Skill inventory must not be empty")
    for package in packages:
        if package["path"] != declared[canonicalize_name(package["name"])]:
            raise GateError("inventory_error", f"inventory path mismatch: {package['name']}")
        if package["publication"] not in {"pypi", "source_only"}:
            raise GateError("inventory_error", "publication must be pypi or source_only")
    return packages


def wheel_metadata(path: Path):
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(members) != 1:
            raise GateError("incompatible", "wheel has missing or ambiguous METADATA")
        return BytesParser().parsebytes(archive.read(members[0]))


def check_dependency(wheel: Path, name: str, core_version: str) -> str:
    data = wheel_metadata(wheel)
    if canonicalize_name(data["Name"]) != canonicalize_name(name):
        raise GateError("incompatible", "wheel project identity mismatch")
    requirements = [Requirement(text) for text in data.get_all("Requires-Dist", [])]
    active = [r for r in requirements if canonicalize_name(r.name) == "xrefkit"
              and (r.marker is None or r.marker.evaluate({"extra": ""}))]
    if not active:
        raise GateError("incompatible", "missing active Core distribution dependency")
    for requirement in active:
        if requirement.url or Version(core_version) not in requirement.specifier:
            raise GateError("incompatible", f"candidate Core {core_version} is excluded by {requirement}")
    return data["Version"]


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "XRefKit-release-compatibility/1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        reason = "registry_missing" if exc.code == 404 else "registry_unavailable"
        raise GateError("blocked", f"{reason}: HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GateError("blocked", "registry_unavailable: could not retrieve official PyPI data") from exc


def published_wheel(name: str, destination: Path) -> Path:
    data = json.loads(_download(f"https://pypi.org/pypi/{name}/json"))
    wheels = [item for item in data["urls"] if item["packagetype"] == "bdist_wheel" and not item["yanked"]]
    if len(wheels) != 1:
        raise GateError("blocked", "unverified: expected one non-yanked official wheel")
    item = wheels[0]
    url = urllib.parse.urlparse(item["url"])
    filename = item["filename"]
    if url.scheme != "https" or url.hostname != "files.pythonhosted.org" or Path(filename).name != filename:
        raise GateError("blocked", "unexpected PyPI artifact location")
    content = _download(item["url"])
    if hashlib.sha256(content).hexdigest() != item["digests"]["sha256"]:
        raise GateError("blocked", "registry artifact SHA256 mismatch")
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / filename
    path.write_bytes(content)
    if wheel_metadata(path)["Version"] != data["info"]["version"]:
        raise GateError("blocked", "registry/wheel version mismatch")
    (destination / "pypi.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def run(command: list[str], cwd: Path, log: Path, *, stage: str) -> str:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PIP_CONFIG_FILE"] = os.devnull
    environment.pop("PIP_EXTRA_INDEX_URL", None)
    try:
        result = subprocess.run(command, cwd=cwd, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=600, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateError("blocked", f"{stage}: command unavailable or timed out") from exc
    with log.open("a", encoding="utf-8") as handle:
        handle.write(f"\n[{stage}]\n{result.stdout}\n")
    if result.returncode:
        if stage in {"install", "build"}:
            # The dependency exclusion is already diagnosed deterministically.
            # Network/build-tool/dependency resolution failures block validation.
            raise GateError("blocked", f"{stage} failed; see {log.name}")
        raise GateError("incompatible", f"{stage} failed; see {log.name}")
    return result.stdout


def regression_result(path: Path) -> dict:
    try:
        root = ET.parse(path).getroot()
        suites = list(root.iter("testsuite"))
        count = sum(int(s.get("tests", "0")) for s in suites)
        skipped = sum(int(s.get("skipped", "0")) for s in suites)
        failed = sum(int(s.get("failures", "0")) + int(s.get("errors", "0")) for s in suites)
    except (OSError, ET.ParseError, ValueError) as exc:
        raise GateError("blocked", "unverified: missing or invalid regression JUnit evidence") from exc
    if failed:
        raise GateError("incompatible", "regression JUnit records failures/errors")
    if count == 0 or skipped:
        raise GateError("blocked", f"unverified regression coverage: {count} tests, {skipped} skipped")
    return {"executed_tests": count, "skipped_tests": skipped}


def probe(repo: Path, package: dict, wheel: Path, core: Path, core_version: str,
          work: Path, log: Path) -> dict:
    environment_root = work / "venv"
    venv.EnvBuilder(with_pip=True).create(environment_root)
    python = environment_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    test_target = (f"{wheel}[test]" if "test" in wheel_metadata(wheel).get_all("Provides-Extra", [])
                   else str(wheel))
    run([str(python), "-m", "pip", "install", "--index-url", "https://pypi.org/simple",
         str(core), test_target, "pytest"], work, log, stage="install")
    run([str(python), "-m", "pip", "check"], work, log, stage="pip-check")
    run([str(python), "-I", str(repo / "tools/check_installed_skill_contract.py"),
         "--name", package["name"], "--package-id", package["package_id"],
         "--core-version", core_version], work, log, stage="contract-load")
    tests = repo / package["path"] / "tests"
    if not tests.is_dir() or not list(tests.glob("test_*.py")):
        raise GateError("blocked", "unverified: no package regression tests")
    run([str(python), "-I", "-m", "pytest", str(tests), "--import-mode=importlib",
         "-o", "pythonpath=", "--basetemp", str(work / "pytest-temp"),
         "--junitxml", str(work / "regression.xml"),
         "-p", "no:cacheprovider", "-q"], work, log, stage="package-regression")
    return regression_result(work / "regression.xml")


def probe_combined(repo: Path, packages: list[dict], wheels: list[Path], core: Path,
                   core_version: str, work: Path) -> None:
    work.mkdir(parents=True, exist_ok=True)
    environment_root = work / "venv"
    venv.EnvBuilder(with_pip=True).create(environment_root)
    python = environment_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    log = work / "commands.log"
    run([str(python), "-m", "pip", "install", "--index-url", "https://pypi.org/simple",
         str(core), *map(str, wheels)], work, log, stage="install")
    run([str(python), "-m", "pip", "check"], work, log, stage="pip-check")
    enabled = [argument for p in packages for argument in ("--enabled-package", p["package_id"])]
    for package in packages:
        run([str(python), "-I", str(repo / "tools/check_installed_skill_contract.py"),
             "--name", package["name"], "--package-id", package["package_id"],
             "--core-version", core_version, *enabled], work, log, stage="combined-contract-load")


def check(repo: Path, core: Path, scope: str, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise GateError("blocked", "use a fresh empty output directory for isolated environments")
    output.mkdir(parents=True, exist_ok=True)
    data = wheel_metadata(core)
    if canonicalize_name(data["Name"]) != "xrefkit":
        raise GateError("inventory_error", "expected a Core xrefkit wheel")
    core_version = data["Version"]
    project_version = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if core_version != project_version:
        raise GateError("inventory_error", "candidate wheel/project version mismatch")
    packages = inventory(repo)
    results = []
    published_artifacts = {}
    candidate_artifacts = {}
    for package in packages:
        for selected in (["published", "candidate"] if scope == "all" else [scope]):
            row = {"name": package["name"], "scope": selected}
            if selected == "published" and package["publication"] == "source_only":
                try:
                    _download(f"https://pypi.org/pypi/{package['name']}/json")
                    row.update(status="inventory_error", reason="source_only project is now published; update inventory")
                except GateError as exc:
                    if "registry_missing" in str(exc):
                        row.update(status="not_published", reason="PyPI returned 404; candidate validation still required")
                    else:
                        row.update(status=exc.status, reason=str(exc))
                results.append(row)
                continue
            work = output / selected / package["name"]
            work.mkdir(parents=True, exist_ok=True)
            log = work / "commands.log"
            try:
                if selected == "published":
                    wheel = published_wheel(package["name"], work / "dist")
                else:
                    dist = work / "dist"
                    run([sys.executable, "-m", "build", "--wheel", "--outdir", str(dist),
                         str(repo / package["path"])], work, log, stage="build")
                    wheels = list(dist.glob("*.whl"))
                    if len(wheels) != 1:
                        raise GateError("blocked", "unverified candidate wheel")
                    wheel = wheels[0]
                row.update(version=wheel_metadata(wheel)["Version"],
                           sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
                           regression_suite="present" if list((repo / package["path"] / "tests").glob("test_*.py")) else "missing")
                check_dependency(wheel, package["name"], core_version)
                row.update(probe(repo, package, wheel, core, core_version, work, log))
                row["status"] = "passed"
                if selected == "published":
                    published_artifacts[package["name"]] = wheel
                else:
                    candidate_artifacts[package["name"]] = wheel
            except GateError as exc:
                row.update(status=exc.status, reason=str(exc))
            except (ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
                row.update(status="blocked", reason=f"unverified metadata or filesystem: {type(exc).__name__}")
            results.append(row)
            print(f"[{selected}] {package['name']}: {row['status']} {row.get('reason', '')}", flush=True)
    published_packages = [p for p in packages if p["publication"] == "pypi"]
    combinations = [
        ("published", published_packages, published_artifacts),
        ("candidate", packages, candidate_artifacts),
    ]
    for selected, combined_packages, artifacts in combinations:
        if not combined_packages or scope not in {selected, "all"} or len(artifacts) != len(combined_packages):
            continue
        row = {"name": f"all-{selected}-official-skills", "scope": f"{selected}_combination"}
        try:
            probe_combined(repo, combined_packages,
                           [artifacts[p["name"]] for p in combined_packages],
                           core, core_version, output / f"{selected}-combination")
            row["status"] = "passed"
        except GateError as exc:
            row.update(status=exc.status, reason=str(exc))
        except (ValueError, KeyError, OSError) as exc:
            row.update(status="blocked", reason=f"combined validation unavailable: {type(exc).__name__}")
        results.append(row)
    return {"ok": all(r["status"] in {"passed", "not_published"} for r in results),
            "core_version": core_version, "core_sha256": hashlib.sha256(core.read_bytes()).hexdigest(),
            "scope": scope, "results": results,
            "boundary": "Official inventory only; third-party packages and AI/business judgments are not certified."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--core-wheel", type=Path, required=True)
    parser.add_argument("--scope", choices=["published", "candidate", "all"], default="all")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists() and any(args.output.iterdir()):
        print(json.dumps({"ok": False, "status": "blocked",
                          "reason": "use a fresh empty output directory; existing evidence preserved"}))
        return 1
    try:
        report = check(args.repo.resolve(), args.core_wheel.resolve(), args.scope, args.output.resolve())
    except (GateError, ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
        report = {"ok": False, "status": getattr(exc, "status", "blocked"), "reason": str(exc)}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
