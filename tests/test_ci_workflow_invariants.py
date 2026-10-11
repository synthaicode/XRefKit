"""CI cleanup must retain release coverage and only cancel obsolete PR runs."""
from pathlib import Path

import pytest
import yaml


WORKFLOWS = Path(__file__).resolve().parents[1] / ".github/workflows"
PACKAGES = {
    "python-package.yml": ("Core", "v*.*.*", {"sdist-install-smoke", "skill-compatibility"}),
    "python-skill-brownfield-package.yml": (
        "Brownfield", "xrefkit-skills-brownfield-v*.*.*", {"sdist-install-smoke"}),
    "python-skill-csharp-package.yml": ("CSharp", "xrefkit-skills-csharp-v*.*.*", set()),
    "python-skill-batch-regression-package.yml": (
        "Batch regression", "xrefkit-skills-batch-regression-v*.*.*", {"sdist-install-smoke"}),
}


def workflow(filename):
    # BaseLoader preserves GitHub's `on` key instead of YAML 1.1's boolean True.
    return yaml.load((WORKFLOWS / filename).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_core_full_quality_gate_runs_once_and_retains_security():
    matches = []
    for path in WORKFLOWS.glob("*.yml"):
        for job_id, job in workflow(path.name).get("jobs", {}).items():
            for step in job.get("steps", []):
                if "python tools/run_quality_gate.py xrefkit" in step.get("run", ""):
                    matches.append((path.name, job_id))
    assert matches == [("python-package.yml", "quality")]
    runs = "\n".join(step.get("run", "") for step in workflow("python-package.yml")["jobs"]["quality"]["steps"])
    assert '".[test,mcp]"' in runs
    assert 'bandit -r "${PYTHON_SOURCE_ROOT}" -ll' in runs
    assert "-r requirements.txt" in runs and "--local" in runs and "--skip-editable" in runs
    slides = workflow("xref-check.yml")
    assert set(slides["jobs"]) == {"slides-app-quality"}
    assert any("run_quality_gate.py slides-app --install-node-deps" in step.get("run", "")
               for step in slides["jobs"]["slides-app-quality"]["steps"])


@pytest.mark.parametrize("filename", [*PACKAGES, "xref-check.yml"])
def test_only_superseded_pull_request_runs_are_canceled(filename):
    data = workflow(filename)
    assert data["concurrency"] == {
        "group": "${{ github.workflow }}-${{ github.event_name == 'pull_request' && github.event.pull_request.number || github.run_id }}",
        "cancel-in-progress": "${{ github.event_name == 'pull_request' }}",
    }
    assert "pull_request" in data["on"]
    if filename in {"python-package.yml", "xref-check.yml"}:
        assert data["on"]["push"]["branches"] == ["main"]
    else:
        assert "branches" not in data["on"]["push"]


@pytest.mark.parametrize("filename", PACKAGES)
def test_release_gates_and_unique_target_names_are_retained(filename):
    prefix, tag, extra_gates = PACKAGES[filename]
    data = workflow(filename)
    jobs = data["jobs"]
    gates = {"quality", "build-distribution", "artifact-inspection", "install-smoke-test"} | extra_gates
    assert set(jobs) == gates | {"publish-to-pypi"}
    assert set(jobs["publish-to-pypi"]["needs"]) == gates
    for job_id in gates - {"quality", "build-distribution"}:
        assert jobs[job_id]["needs"] == "build-distribution"
    assert data["on"]["push"]["tags"] == [tag]
    assert jobs["publish-to-pypi"]["if"] == (
        "github.event_name == 'push' && startsWith(github.ref, 'refs/tags/" + tag.split("*")[0] + "')")
    assert jobs["publish-to-pypi"]["permissions"]["id-token"] == "write"
    assert data["permissions"] == {"contents": "read"}
    names = [job["name"] for job in jobs.values()]
    assert len(set(names)) == len(names)
    assert all(name.startswith(prefix + " / ") for name in names)


def accepts_changes(filename, event, files):
    from fnmatch import fnmatchcase

    config = workflow(filename)["on"].get(event)
    if config is None:
        return False
    if not isinstance(config, dict):
        return True
    if "paths" in config:
        return any(fnmatchcase(path, pattern) for path in files for pattern in config["paths"])
    return any(not any(fnmatchcase(path, pattern) for pattern in config.get("paths-ignore", []))
               for path in files)


@pytest.mark.parametrize("filename", [*PACKAGES, "xref-check.yml", "pages.yml",
                                      "xrefkit-skills-xddp-design.yml"])
def test_readme_only_changes_skip_unrelated_workflows(filename):
    for event in ("pull_request", "push"):
        # Tag pushes deliberately do not evaluate GitHub path filters.
        if event == "push" and "branches" not in workflow(filename)["on"].get(event, {}):
            continue
        assert not accepts_changes(filename, event, ["README.md"])


@pytest.mark.parametrize("path", ["xrefkit/cli.py", "docs/core/contracts/example.md",
                                  "skills/example/SKILL.v1.md", "knowledge/example.md",
                                  "agent/000_agent_entry.md", "tests/test_example.py"])
def test_readme_exclusion_retains_core_and_governance_checks(path):
    for event in ("pull_request", "push"):
        assert accepts_changes("python-package.yml", event, [path])
        assert accepts_changes("python-package.yml", event, ["README.md", path])
    assert workflow("python-package.yml")["on"]["push"]["paths-ignore"] == ["README.md"]


@pytest.mark.parametrize("package", ["batch-regression", "brownfield", "csharp"])
def test_skill_packages_cover_own_sources_and_shared_dependencies(package):
    filename = f"python-skill-{package}-package.yml"
    for path in [f"packages/xrefkit-skills-{package}/tests/test_package.py",
                 f".github/workflows/{filename}", "tools/inspect_python_artifacts.py",
                 "xrefkit/workspace.py", "pyproject.toml", "requirements.txt"]:
        assert accepts_changes(filename, "pull_request", [path])
    if package in {"brownfield", "batch-regression"}:
        assert accepts_changes(filename, "pull_request", ["tools/run_import_smoke.py"])
    assert not accepts_changes(filename, "pull_request", ["projects/slides-app/src/App.tsx"])


def test_slides_inputs_and_pages_manifest_inputs_are_covered():
    import json

    for event in ("pull_request", "push"):
        for path in ["projects/slides-app/package.json", "tools/run_quality_gate.py",
                     "requirements.txt", ".github/workflows/xref-check.yml"]:
            assert accepts_changes("xref-check.yml", event, [path])
        assert not accepts_changes("xref-check.yml", event, ["xrefkit/cli.py"])
    manifest = json.loads((WORKFLOWS.parents[1] / "site/source_manifest.json").read_text())
    for tree in manifest["trees"]:
        assert accepts_changes("pages.yml", "push", [tree["source"] + "/index.html"])
    for path in ["site/source_manifest.json", "site/index.html", "tools/site_build.py",
                 "tools/site_release_metadata.py", ".github/workflows/pages.yml"]:
        assert accepts_changes("pages.yml", "push", [path])
    assert not accepts_changes("pages.yml", "push", ["human-docs/ja/unrelated.md"])
    data = workflow("pages.yml")
    assert {"release", "workflow_run", "workflow_dispatch"} <= set(data["on"])
    condition = data["jobs"]["deploy"]["if"]
    assert "github.event.workflow_run.conclusion == 'success'" in condition
    assert "github.event.workflow_run.event == 'push'" in condition
    assert "startsWith(github.event.workflow_run.head_branch, 'v')" in condition
    assert "github.event.workflow_run.head_repository.full_name == github.repository" in condition


def test_all_workflows_parse_and_sync_still_includes_readme_updates():
    for path in WORKFLOWS.glob("*.yml"):
        data = workflow(path.name)
        assert isinstance(data["on"], dict)
        assert isinstance(data["jobs"], dict)
    assert accepts_changes("sync-main-without-mp4.yml", "push", ["README.md"])
    assert workflow("sync-main-without-mp4.yml")["on"]["push"] == {"branches": ["main"]}
