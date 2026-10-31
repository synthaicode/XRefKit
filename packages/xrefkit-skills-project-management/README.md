# XRefKit Project Management

Distribution candidate: **xrefkit-skills-project-management 0.1.0a1**.
Package ID: `xrefkit.skills.project_management`.

Three native SkillDefinitions form one Project Management job:

- `progress_rules_setup`: confirm project rules, record destinations, formats,
  sharing/attachment methods and completion conditions with the human owner.
- `requirements_discovery_coordination`: alternate clarification and bounded
  evidence investigation without requiring finalized requirements first.
- `work_progress_coordination`: guide contributors from confirmed prerequisite
  slices, holds and separate quality-owner decisions.

Technical investigation, quality verification and stakeholder agreement retain
their existing owners. Project Knowledge supplies actual settings. No project
values, custom UI, Azure attachment adapter or generic work tracker is bundled.

## Readiness and installation

All three definitions are **draft**. The alpha distribution version does not
promote maturity. Packaged governance is explicitly bound in the manifest and
checked against each definition's exact hash. Core `0.7.5` is the first planned
version with this package-governance support; it is an unreleased candidate here.
Do not claim the package can currently be installed from public PyPI.

Once compatible Core and this package are separately approved and published:

```console
python -m pip install --pre xrefkit-skills-project-management
```

MCP discovery uses the normal `xrefkit.skill_packages` entry point and the enabled
package ID above. It exposes the three methods and their draft governance.
Semantic selection needs no user-supplied Skill name, but draft execution remains
refused. Supply the packaged `governance/skills/<skill_id>.json` to any direct CLI
readiness/run check; the CLI does not auto-discover external governance.
Native definitions use the MCP distribution path, not legacy v2 `effective-skill`
wrapper inheritance. Do not convert them to YAML to bypass the draft boundary.

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
then tag-gated Trusted Publishing. The official source-only package inventory
also includes this candidate in Core's individual and combined candidate checks.
PR checks use the local candidate Core. Release install checks require compatible
Core from PyPI and fail if it is absent; publish cannot precede those checks.

Publication requires a separate authorized release and the tag matching
`xrefkit-skills-project-management-v0.1.0a1`. No tag or upload is created by
preparation. Configure PyPI pending Trusted Publisher with owner `synthaicode`,
repository `XRefKit`, workflow `python-skill-project-management-package.yml`,
environment `pypi`; existing OIDC publishing needs no API-token secret.
Account/project configuration is not performed by this package preparation.
See [PyPI's pending publisher setup](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
for navigation to current setup instructions. A name lookup is not a reservation.
