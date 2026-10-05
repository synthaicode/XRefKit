<!-- xid: 0C41A7D389B2 -->
<a id="xid-0C41A7D389B2"></a>

# Core release compatibility with official Skill packages

The Core release workflow tests the exact built Core wheel against official
Skill distributions before it can create a GitHub Release or publish to PyPI.
Changing the Core version in `pyproject.toml` does not bypass this check: it
runs on every Core pull request, main push, and Core release tag. The wheel
version must match the project version. No Core release is performed by the
checker itself.

## Inventory and separate evidence

`tools/official_skill_packages.json` is the explicit official inventory.
The checker reconciles it with every `packages/**/pyproject.toml` declaring
the `xrefkit.skill_packages` entry-point group. A new unlisted package or
a mismatched path fails the inventory check.

| Official distribution | Publication | Published check | Candidate check |
| --- | --- | --- | --- |
| xrefkit-skills-brownfield | PyPI | required | required |
| xrefkit-skills-csharp | PyPI | required | required |
| xrefkit-skills-batch-regression | PyPI | required | required |
| xrefkit-skills-xddp-design | source only | explicitly `not_published` | required; failures block Core release |

The **published** scope retrieves the current non-yanked wheel directly from
official PyPI, verifies its SHA256, and checks its actual `Requires-Dist`.
It installs that wheel and the exact candidate Core wheel in an isolated venv.
It never substitutes the repository's repaired Skill project for the public
wheel. A Skill must be published first if users cannot yet install a compatible
public combination. The published scope is repeated immediately before the
publication job's first external release action to detect registry changes
since the earlier compatibility job.
After the individual checks pass, a further clean environment installs all
published official Skills together and loads them with all their package IDs
enabled, catching shared dependency and registry/XID conflicts. Source-only
rows are confirmed by a PyPI 404; an outage blocks the check, and a newly
published source-only row requires an inventory update.
After all candidate checks pass, a separate environment also installs and
enables every candidate together, including source-only packages. Individual
success cannot mask candidate dependency or XID collisions.

The **candidate** scope builds and installs each inventoried repository Skill
in a separate isolated venv with that same Core artifact. Passing this scope
does not satisfy the published scope. A source-only candidate is not silently
excluded: incompatible dependencies, loader failures, or missing regression
tests block the candidate scope and therefore Core publication.

## Checks and outcomes

Each isolated environment runs `pip check`, discovers the installed entry
point, verifies distribution/manifest identity and version, and uses the real
Core registry and resolver to inherit every packaged Skill through a project
wrapper. Core **protocol** compatibility comes from the runtime's own
`build_registry` check, independently from Python distribution compatibility.
The probe validates actual Skill schemas, retained manifest contracts, required
Knowledge/review-axis/schema/template references, file existence and content,
workflow file handles, all YAML/JSON assets, and the package regression tests.
Tests run outside the repository with source-path injection disabled. A
declared `test` extra is installed for regression tooling; it does not change
the Skill's runtime Core constraint.
JUnit evidence must show executed tests with no failures, errors, or skips;
missing, empty, or skipped regression coverage blocks the gate.

- `passed`: all declared deterministic checks completed successfully.
- `incompatible`: dependency exclusion, schema/contract/load failure, failing
  regression test, or broken installed dependency.
- `blocked`: registry/network/build/install failure, missing test evidence,
  invalid downloaded metadata, or an unavailable command. This is not reported
  as proven incompatibility and cannot authorize release.
- `inventory_error`: an inconsistent or incomplete inventory; release stops.
- `not_published`: explicit source-only published-scope row. It does not waive
  its required candidate check.

The source-only XDDP design candidate targets the Core distribution range
`xrefkit>=0.6.1,<0.7.0` independently of manifest protocol
`>=2.0.0 <3.0.0`. Its installed-runtime regression suite covers discovery,
contract inheritance, file-backed references, on-demand branch availability,
the output schema, CLI resolution, and rejection cases. It remains unpublished;
a successful candidate check does not authorize publication.

## Local use and boundary

```powershell
python -m pip install build packaging
python -m build --outdir dist
python tools/check_skill_compatibility.py --core-wheel dist/xrefkit-0.6.1-py3-none-any.whl --scope all --output .tmp/skill-compatibility
```

The JSON report records scopes, exact versions and hashes, and failure reasons;
per-package command logs retain runtime and test evidence. CI preserves these
reports even on failure. The standard Core quality gate also tests rejection
fixtures for old dependency bounds, incompatible protocol, malformed Skill
schema, missing entry, lost contract, missing regression evidence, omitted
inventory entries, and registry outages.
Use a fresh empty output directory for each run. Reusing an existing evidence
directory is blocked so an earlier environment cannot mask a clean-install
failure.

The guarantee covers official inventoried distributions on the CI Python 3.12
runtime. It does not certify external third-party packages, all possible
dependency/platform combinations, transitive external Knowledge corpus links,
or AI/business judgments during a project's workflow execution.
