# Core 0.7.12 release metadata

## 2026-11-15: Authorized release preparation

### Event

- Updated `pyproject.toml` and `xrefkit/__init__.py` from 0.7.11 to 0.7.12.
- Changed the existing Quality Issue changelog section from Unreleased to `0.7.12 (2026-11-15)`.
- `git ls-remote --tags origin v0.7.12` returned no matching tag.
- The PyPI version JSON endpoint for `xrefkit/0.7.12` returned HTTP 404 before preparation.

### Decision

- Prepare metadata for the user-authorized PR merge and PyPI release through the existing GitHub workflow, conditional on CI.
- Keep deployment-specific checks deferred as explicitly accepted by the user.
- Do not execute the draft `release_planning_flow`, promote any Skill, or expand product behavior.

### Human Stated Reason

- User authorized merging PR 196 when CI succeeds and publishing the Core release.

### Verification

- Python's deterministic TOML parser accepted `pyproject.toml`.
- Imported runtime version, project version, and dated changelog agree on 0.7.12.
- `python -m xrefkit --version` is not an available CLI operation; no version-flag support is claimed. Version validation used the actual package constant instead.
- No full suite rerun was required for these three metadata-only edits; coordinator owns subsequent CI and package artifact checks.

### Handoff

- Coordinator: inspect the metadata diff, verify/close the run, commit/push, await CI, then perform the authorized merge and existing workflow publication.
- This executor did not commit, push, merge, tag, or publish.
