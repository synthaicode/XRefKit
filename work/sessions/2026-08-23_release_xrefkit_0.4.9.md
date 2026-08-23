## 2026-08-23: XRefKit 0.4.9 PyPI release

### Event
The latest `origin/main` commit was prepared for publication. The package
version in `pyproject.toml` was changed from `0.4.8` to `0.4.9` in a clean
release worktree. Local verification completed with `361 passed`, successful
`twine check` for the wheel and source distribution, successful artifact
inspection, `compileall`, and `git diff --check`.

### Decision
Publish XRefKit `0.4.9` from the release commit based on `origin/main`.

### Human Stated Reason
The human requested that the latest XRefKit be published to PyPI and then
confirmed proceeding with version `0.4.9` after `0.4.8` was found to be
already published.

### Deferred
None.

### Open
Remote commit, tag, GitHub Actions, GitHub Release, PyPI visibility, and clean
installation remain to be verified after publication.

## 2026-08-23: Release validation correction

### Event
The pull request workflow found that `xrefkit.__version__` remained `0.4.8`
while package metadata was `0.4.9`. The package metadata and runtime version
are now aligned at `0.4.9`.

### Decision
Update the runtime version before rerunning the release gates.

### Human Stated Reason
The human authorized proceeding with the `0.4.9` publication.

### Deferred
None.

### Open
The corrected commit must pass the remote checks before merge and tagging.
