"""Collect tests for APIs present in the installed PM package version."""

from importlib.metadata import version

from packaging.version import Version


def pytest_ignore_collect(collection_path, config):
    # The Core compatibility gate runs this suite against the last public PM
    # wheel as well as the candidate. The report APIs first shipped in 0.1.4.
    if collection_path.name not in {"test_human_report.py", "test_next_step_readiness.py"}:
        return None
    return Version(version("xrefkit-skills-project-management")) < Version("0.1.4")
