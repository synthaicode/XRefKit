# xrefkit-skills-brownfield

Public XRefKit Skill Package for brownfield change work, version **0.3.0**.

The package provides `brownfield.workflow`, which carries upstream work items
through requirements, planning, design, manufacturing, and testing. Each phase
returns `要求事項`, `確認事項`, and `進め方`, with change reasons and evidence.
Status, result, open items and handoff remain within these three sections.

Four individual Skills are available at trial maturity:

- `investigation_flow` scopes a change investigation and records its evidence.
- `requirements_flow` drafts requirements and preserves explicit differences.
- `design_flow` prepares review-ready design and test handoff.
- `db_current_state_analysis` documents existing database and persistence behavior.

Compatibility requires XRefKit >=0.7.10,<0.8.0 and Python >=3.11.
The manifest requirement >=2.0.0 <3.0.0 names the Core protocol.
The installed-package tests exercise discovery, contract inheritance, native
Skill governance, and Knowledge resolution.

Directly required Knowledge fragments are included. Their further
XID links remain lookup handles for the host's knowledge provider; this package
does not bundle the entire repository corpus or a project's system evidence.
The deterministic checks do not certify AI judgments or business-specific
execution of all five phases.

## Understanding revisions and Project Management

The deterministic helper compares **explicit structured records**, including
added/removed scope and changed evidence, approvals and artifact revisions. It
does not infer semantic understanding from arbitrary text, search Knowledge,
execute an investigation or decide whether evidence is true or sufficient.
The technical investigator records those judgments and their owners explicitly.

```console
python -m pip install "xrefkit-skills-brownfield[project-management]==0.3.0"
xrefkit-brownfield-understanding current.json --previous previous.json
xrefkit-brownfield-understanding current.json --previous previous.json --json --save project-records
```

The first analysis command displays the three standard sections. `--json` returns the
analysis/notification contract. The optional `--save` writes exact current and
previous inputs plus analysis to `understanding-rNNN.json` at the explicitly
selected destination. Identical retries are idempotent; changed content at an
existing revision is rejected. A complete temporary file is published with an
exclusive same-directory hard link; the filesystem must support that operation.
This evidence file does not certify upload or shared visibility. Use the
destination, permissions and delivery completion rules confirmed for the project.

`examples/understanding-r001.json` in the installed package is synthetic input:

```python
from xrefkit_skills_brownfield import package_root
example = package_root() / "examples/understanding-r001.json"
```

The JSON schema identifier is `brownfield.understanding/v1`. Unknown fields are
rejected so misspelled evidence or approval fields cannot silently disappear.

| Record | Required fields |
| --- | --- |
| Snapshot | `schema`, `project_id`, positive integer `revision`, timezone-aware `recorded_at`, `reason`, `evidence_refs`, `decision_refs`, `approval_refs`, and the five lists below |
| `requirements`, `confirmations`, `approach` items | `id`, `text`, `status`, `owner`, `reason`, `requirement_xids`, `evidence_refs`, `decision_refs`, `approval_refs`, `artifact_refs`, `affected_task_ids` |
| `artifacts` items | `id`, `ref`, explicit string `revision`, `requirement_xids`, `evidence_refs` |
| `knowledge_requirements` items | `id`, `requirement_xids`, `question`, `query`, `needed_for`, `status`, `knowledge_refs`, `evidence_refs`, `decision_refs`, `owner`, `reason`, `method`, `expected_evidence`, `decision_ref`, `resolution_point` |

IDs use letters, digits, hyphens and underscores. Requirement XIDs use 12 uppercase
hexadecimal characters. Reference fields are unique string lists. Every linked
XID must occur in the snapshot's requirements; every `artifact_refs` entry resolves
to a versioned artifact in that snapshot. Empty evidence lists remain explicitly
unrecorded, not proof. A requirement may be `candidate`, `confirmed`, `withdrawn`;
a confirmation `open`, `answered`, `conflict`; an approach `proposed`, `approved`,
`completed`, `hold`. Confirmed/approved states require approval references;
answered/completed states require evidence. These references record the stated
authority; they do not cryptographically verify a human's decision.

Knowledge Requirement states are `open`, `satisfied`, `stale`, `conflict`.
`satisfied` requires both Knowledge and evidence references. Open requirements
produce explicit gaps and proposed Holds with owner and resolution point.
`method`, `expected_evidence`, `decision_ref` may be null when not known; any
missing value prevents activity derivation. The helper never invents work duration,
dependency, test expectation, migration method or acceptance approval.

```python
from xrefkit_skills_brownfield.understanding import analyze_understanding
from xrefkit_skills_project_management.schedule import assess_impact

analysis = analyze_understanding(current, previous)
impact = assess_impact(plan, analysis["notification"])
```

The optional extra installs Project Management `>=0.1.0,<0.2.0`. Brownfield works
without that extra and saves a notification for a named receiving owner.
Project Management owns notification validation, direct/dependent impact analysis,
schedule/actual/baseline separation, CPM, Mermaid and immutable plan history.
Notifications contain stable identity, revision comparison, change reasons,
requirement XIDs, Evidence, decisions, approvals, affected task IDs, proposed
Decision investigations and open Holds. Acceptance does not modify the plan or
grant work-start/quality permission. An authorized owner must approve a revised
plan through existing progress rules. No Core contract or maturity change is made.

Package regression tests run independently; cross-package tests are in
`integration/brownfield_project_management/tests` in the repository and run against
installed distributions. Publication uses the existing inspected-artifact and
Trusted Publishing workflow. See `CHANGELOG.md` for this release's changes.
