<!-- xid: 7E4B19C2A860 -->
<a id="xid-7E4B19C2A860"></a>

# Pipeline Dependency Reference

GitHub Actions triggers follow the inputs actually consumed by each workflow.
A product dependency alone does not mean that every workflow tests the checked-out
version of that dependency. Path filters apply to PR and branch events; tag
publication remains independent of changed paths.

## Event And Dependency Matrix

| Workflow | Events | Checked inputs and behavior |
| --- | --- | --- |
| `python-package.yml` | PR; filtered `main` push; `v*.*.*` tag | Repository Core, full root pytest suite, governance validation, package build/security/install gates, and official Skill compatibility against the exact built Core wheel. |
| `python-skill-brownfield-package.yml` | Filtered PR; `xrefkit-skills-brownfield-v*.*.*` tag | Brownfield package tree, its workflow, artifact inspection and import-smoke tools. Package tests run against an installed public Core dependency. |
| `python-skill-csharp-package.yml` | Filtered PR; `xrefkit-skills-csharp-v*.*.*` tag | CSharp package tree, its workflow, artifact inspection tool. Package tests run against an installed public Core dependency. |
| `python-skill-batch-regression-package.yml` | Filtered PR; `xrefkit-skills-batch-regression-v*.*.*` tag | Batch regression package tree, its workflow, artifact inspection and import-smoke tools. Package tests run against an installed public Core dependency. |
| `xrefkit-skills-xddp-design.yml` | Filtered PR and `main` push | XDDP candidate tree, its workflow, artifact inspection tool. Installed wheel/sdist regressions use public `xrefkit==0.6.1`. No publication job. |
| `xref-check.yml` (`slides-app-quality`) | Filtered PR and `main` push | `projects/slides-app/**`, `tools/run_quality_gate.py`, `requirements.txt`, and its workflow. Runs the Slides npm check, not the Core governance gate. |
| `pages.yml` | Filtered `main` push; release lifecycle events; manual dispatch; completion of `python-package` | `site/**`, site build/release tools, its workflow, and the asset/video source trees listed in `site/source_manifest.json`. A workflow completion deploys only after a successful same-repository version-tag push, not a main-branch build. Release and manual events remain independent of path filters. |
| `skill-bundle-release.yml` | `xrefkit-skills-*-v*.*.*` tag; manual dispatch | Selected Skill package assets, manifest, and workflow; builds bundle release assets. No PR or branch CI. |
| `structure-graph-nuget-publish.yml` | `structure-graph-v*.*.*` tag | `tools/structure_graph` project and workflow; publishes stable NuGet tool versions, rejects RC-like tags at the job gate. No PR or branch CI. |
| `structure-graph-publish-github-packages.yml` | `structure-graph-v*.*.*-rc.*` tag; manual dispatch | `tools/structure_graph` project and workflow; publishes RC tool packages. No PR or branch CI. |
| `sync-main-without-mp4.yml` | Every `main` push; manual dispatch | The complete tracked main tree, excluding MP4/site assets from the generated branch. README changes must propagate, so no changed-path filter. |

## Core Gate Inputs

The Core workflow also owns repository-wide validation. Its branch/PR paths
therefore include more than the Core Python module:

- `xrefkit/**` (including packaged resources), `tests/**`, and `tools/**` cover
  runtime code, all root tests, tool contracts, artifact/import scripts, and
  `tools/check_skill_compatibility.py` plus `tools/check_installed_skill_contract.py`.
- `agent/**`, `docs/**`, `skills/**`, `knowledge/**`, and `capabilities/**` are
  governance/XID validation inputs. Adoption records and referenced governance,
  observation records remain covered: `skills/repository_adoption.json` binds
  `governance/skills/planning_flow.json` and an observation basis; repository
  adoption/readiness tests verify those receipts. `flows/**` and
  `work/retrospectives/**` are scanned by the public/private boundary validation
  in `xrefkit/skillmeta.py`; `packs/**` is enumerated by pack lint and the
  ownership-aware content resolver in `xrefkit/ownership.py`.
- `packages/**` supplies candidate packages and regression tests. The compatibility
  inventory in `tools/official_skill_packages.json` is reconciled against all
  package projects, including source-only XDDP candidates.
- All workflow YAML is included because root pytest checks workflow invariants.
  `work/sessions/**` supplies tracked runtime logs to the audit, and
  `work/retrospectives/**` participates in public-content validation.
- `site/**` supplies templates inspected by root site tests. Node project
  `package.json`, `package-lock.json`, and `README.md` are baseline inputs for
  `tools/check_project_quality_baseline.py`; Attention Pet schemas are read by
  Python regression tests. Application source files do not invoke Core solely
  because they belong to a Node project.
- Root build/runtime/ownership/startup files and checkout controls remain covered:
  `pyproject.toml`, `requirements.txt`, `LICENSE`, `ownership.yaml`, `xrefkit.toml`,
  `AGENTS.md`, `CLAUDE.md`, `CHATGPT.md`, `.gitattributes`, and `.gitignore`.

Root `README.md` is an intentional branch/PR exception requested for editorial
updates. It is still package metadata consumed by tag builds. Mixed changes run
all workflows whose paths match any changed file. Other human-facing prose and
unconsumed operational records do not start Core CI merely because they changed.

## Checked-Out Core Versus Public Core

Individual Skill workflows install their package from checkout and run their
compatibility tests outside the checkout against installed packages. Their
Core dependency is resolved from PyPI; changing
`xrefkit/**`, root `pyproject.toml`, or root `requirements.txt` does not replace
that installed dependency. These files consequently do not start those package
workflows. Changing a package's own dependency declaration does.

Core-to-Skill compatibility is validated by the Core workflow with the exact
newly built Core wheel and both published Skills and repository candidates.
A checked-out Core change starts Core CI, which owns this compatibility evidence.
XDDP's independent candidate workflow deliberately remains pinned to public
Core 0.6.1. Neither test environment substitutes for the other.

## Maintaining Coverage

When a workflow, tool, or test starts consuming another repository input, update
its event paths and the scenarios in `tests/test_ci_workflow_invariants.py` together.
Keep package release tag patterns, publication prerequisites, manual events, and
main synchronization intact. The YAML files are the executable trigger source;
this matrix explains their input ownership.

Local tests parse all workflows and exercise positive, negative, mixed-change,
shared-tool, manifest-source, and release-gate scenarios. They simulate changed
path selection; actual GitHub event dispatch requires remote run evidence.

## Related

- [Core Release Compatibility With Official Skill Packages](../guides/112_core_skill_release_compatibility.md#xid-0C41A7D389B2)
- [Project Quality Baseline](056_project_quality_baseline.md#xid-1C4B72D5E901)
