# XRefKit Project Management

Distribution: **xrefkit-skills-project-management 0.1.0a3**.
Package ID: `xrefkit.skills.project_management`.

Five native SkillDefinitions form one Project Management job:

- `progress_rules_setup`: confirm project rules, record destinations, formats,
  sharing/attachment methods and completion conditions with the human owner.
- `requirements_discovery_coordination`: alternate clarification and bounded
  evidence investigation without requiring finalized requirements first.
- `work_progress_coordination`: guide contributors from confirmed prerequisite
  slices, holds and separate quality-owner decisions.
- `pm_coordination_setup`: extend confirmed progress setup with organization-aware
  decision authority, stakeholder responsibilities and trace-record settings.
- `pm_decision_coordination`: support PM handling and stakeholder agreement,
  trace internal reflection and quality results, and prepare bounded work-start
  choices from existing readiness results throughout the project.

Technical investigation, quality verification and final agreement judgments retain
their existing owners. Project Knowledge supplies actual settings. No project
values, custom UI, Azure attachment adapter or generic work tracker is bundled.

## Structured scheduling and Gantt history

This release adds the explicit Python tool
`xrefkit_skills_project_management.schedule`. It independently calculates Decision
and Execution networks, generates Mermaid Gantt from authoritative JSON, and
saves separate immutable Revision/Snapshot files. The history index retains change
reasons, requirement XIDs, evidence, judgment and recorded approval. Proposed,
approved and baseline plan references remain separate; actual observations never
replace the baseline. SHA-256 checks detect changed historical files or metadata.

Deterministic CPM supports finish-to-start dependencies, nonnegative working-day
lags, milestones, release dates, declared working weekdays and holidays. It reports
all critical branches, float and remaining-work forecasts. Unsupported constraints
and cyclic/missing dependencies refuse calculation. This is not resource leveling,
project approval or a start/quality-condition matcher.

Brownfield notifications use receiver-owned `brownfield.change_impact/v1`
validation. `assess_impact` maps requirement and task references, dependent work,
Decision activities and Holds without mutating a plan or claiming readiness.
`compare` and `compare_plans` report baseline/forecast or revision differences;
cross-plan effects remain evidence-linked decisions, not inferred CPM edges.

```console
python -m xrefkit_skills_project_management.schedule plan.json
python -m xrefkit_skills_project_management.schedule plan.json --snapshot actual.json
python -m xrefkit_skills_project_management.schedule plan.json --save management --metadata change.json
```

Use the project's confirmed destination and settings. The complete JSON/API,
calendar semantics, failure-recovery limits and authority boundary are bundled at
`package_root()/docs/packs/project-management/scheduling.md` and documented in the
[repository scheduling interface](https://github.com/synthaicode/XRefKit/blob/main/docs/packs/project-management/scheduling.md).
This explicit tool does not execute or promote the five Skills.

## Readiness and installation

All five definitions are **trial**, following explicit user approval and a
bundled authoring/readiness bootstrap observation. Actual project operation is
not established by that observation. Packaged governance is explicitly bound in the manifest and
checked against each definition's exact hash. This package requires Core
`>=0.7.5,<0.8.0` for native package-governance support. Publication and public
availability are verified separately from source and candidate-build validation.

Install after compatible Core and this package are published:

```console
python -m pip install --pre xrefkit-skills-project-management
```

MCP discovery uses the normal `xrefkit.skill_packages` entry point and the enabled
package ID above. It exposes the five methods and their trial governance.
Semantic selection needs no user-supplied Skill name. Trial runs still require
instruction-derived runtime inputs and applicable project prerequisites. Supply
the packaged `governance/skills/<skill_id>.json` to any direct CLI
readiness/run check; the CLI does not auto-discover external governance.
Native definitions use the MCP distribution path, not legacy v2 `effective-skill`
wrapper inheritance. Maturity does not grant project adoption or human authority.

The installed `package_root()` points to all bundled files. Repository handoff
links to existing technical/persistence Skills are navigation links; those Skills
are not copied into or automatically installed by this distribution. Resolve an
available applicable route, or return the missing dependency as an explicit gap.

## Development and publication checks

Canonical sources live in `skills/packs/project-management/`. Run
`python tools/materialize_project_management_package.py` after source changes;
`--check` rejects stale packaged content or bound governance. Build wheel and
sdist with `python -m build packages/xrefkit-skills-project-management`.

The existing Skill-package pipeline pattern is used: tests, build, metadata and
archive inspection, secret checks, malware scan, isolated wheel/sdist install,
then tag-gated Trusted Publishing. The official package inventory also includes this package in Core's individual
and combined candidate checks; its publication state is updated after release.
PR checks use the local candidate Core. Release install checks require compatible
Core from PyPI and fail if it is absent; publish cannot precede those checks.

Publication requires a separate authorized release and the tag matching
`xrefkit-skills-project-management-v0.1.0a3`. No tag or upload is created by
preparation. Configure PyPI pending Trusted Publisher with owner `synthaicode`,
repository `XRefKit`, workflow `python-skill-project-management-package.yml`,
environment `pypi`; existing OIDC publishing needs no API-token secret.
Account/project configuration is not performed by this package preparation.
See [PyPI's pending publisher setup](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
for navigation to current setup instructions. A name lookup is not a reservation.
