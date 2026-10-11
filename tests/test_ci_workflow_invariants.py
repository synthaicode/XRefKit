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
    assert "paths" not in data["on"]["pull_request"]
    assert "paths" not in data["on"]["push"]


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
