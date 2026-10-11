<!-- xid: F3A8D602C951 -->
<a id="xid-F3A8D602C951"></a>

# XRefKit Local Client Work Management Operating Model

## Applicability and authority

This implementation-specific fragment describes local schema-v2 client work
management inspected on 2026-10-11. Shared MCP provides reusable context;
the client workspace owns plans, observations and artifacts. Azure is an optional
separate integration, not a dependency of local management. The operation method
belongs to [local_work_management](../../skills/os/local_work_management/SKILL.v1.md#xid-E7C4A916B280).

## Identities, persistence and projection

A registered workspace has schema_version 1, workspace_id, title and portable
workspace_root relative to the selected repository root. Registration lives under
work/workspaces; plans live under the registered workspace's work/plans.
Same-ID changed registration is rejected. Paths are confined to the selected root.

Plan schema_version 2 distinguishes workspace_id/plan_id/plan_revision from
observation_revision and report_id. Definition fields, topology and completion
criteria are immutable within a plan revision. The source identifies approved
breakdown; project/change/baseline identify context and versioned before-state.
Writer-owned observation_revision, observation_history and report_sha256 are
computed by record_plan, not fabricated by a submission. New plans require
expected revision 0; new observations require the stored current revision.

record_plan validates, seals history and atomically publishes JSON, then attempts
an adjacent Markdown projection. Projection failure does not roll back saved
JSON; CLI returns failure when projection failed. Same report/content replay
retains the current snapshot and does not advance observation revision. Changed
same-report content or stale revision is rejected. Explicit render reads a stored
plan through plan_markdown.regenerate and does not update observations.
Owned derived Markdown records provenance and definition/snapshot hashes;
conflicting/unowned projections are protected. Markdown is a view, not editable
state authority. Mermaid represents recorded dependencies; compatible local
preview support is required. Optional explicit monitor deployment is separate.

## Work packages: approved planning definition

A work package is a planning unit that groups tasks serving one purpose and
result. The local hierarchy is PBI -> work package -> Task. Packages group by
outcome: design, implementation and test may belong to the same package.
A process stage describes the kind or phase of work and is a separate concept.

Each package has a unique ID and title, purpose, output, member task IDs,
completion criterion, dependencies on other package results and a confirmation
owner. Each task belongs to exactly one package; the approved task set is covered
once. A cross-package dependency does not give a task a second membership.

Package nodes do not add planned steps. Planned/completed/remaining counts use
unique tasks only. All member tasks complete and package criterion verified are
two distinct indicators. Package verification requires its own recorded evidence
and designated confirmation owner; PBI business acceptance remains separate.

Schema v2 optionally stores `work_packages`. Each package requires nonempty
`work_package_id`, `title`, `pbi_id`, `purpose`, `expected_output`,
`completion_criterion`, `review_owner`, a nonempty `step_ids` array and a
`depends_on` array (empty when no dependencies are recorded). `pbi_id` names an
existing PBI. Package IDs and memberships are unique. All current Tasks must
belong exactly once when the field is present; an empty array is valid only
for an empty Task set. Existing Task `pbi_ids`, when declared nonempty, must
include the package parent. `step_ids` is the canonical package membership;
there is no duplicated package ID on each Task. Missing dependencies, duplicate
edges and package cycles are rejected. Packages can span stages.

Optional `verification` is an observation object with `status` (`verified`,
`not_verified` or `revalidation_needed`), optional `reviewer`, timezone-aware
`recorded_at` and `evidence_refs`. `verified` requires a reviewer equal to the
designated `review_owner`, an explicit timestamp and nonempty evidence references.
Validation checks the declaration, not evidence truth or human authorization.
No missing status is invented. Verification observations may change within the
same plan revision; package definition fields and membership require a new
plan revision. Previous verification remains in observation history.

Recording automatically generates package counts and details, a PBI/package/Task
membership Mermaid, a separate explicit package-result dependency Mermaid, and
Task dependencies grouped by package. Membership lines are undirected and do not
imply execution order. Stage counts remain independently visible. All Tasks done
never establishes package verification or PBI acceptance. A retained verified
record with outstanding/reopened Tasks is explicitly marked as historical rather
than current readiness. Packages themselves never increase Task totals.

Omitting `work_packages` preserves existing v2 plans, immutable definition hashes
and stage-grouped diagrams. JSON remains the authority; source Markdown retains
approved planning basis, not a second live package-state ledger. Replay,
conflict protection and explicit regeneration use the current stored snapshot.
The definition basis is the user's approved grouping and implementation request
on 2026-10-11; source behavior and focused tests establish the current contract.

## Status, evidence and counts

Steps have stage, status, completion criterion, dependencies, outputs and exact
run references. artifact_refs and baseline artifacts preserve kind, path, revision, source
and recorded_at; validation_records identify target version, environment,
expected/result evidence and reviewer. judgment_refs/concern_refs link separate
records. The schema accepts recorded references; it does not prove their truth,
automatically ingest client execution logs or advance Skill runtime logs.

Counts use unique step IDs. completed counts status done only when
revalidation_needed is not true; explicit true keeps the step in remaining.
Null/missing revalidation is unrecorded rather than inferred false. Missing
status evidence does not itself reopen work. initial_task_ids distinguishes
initial, added and removed steps; multiple runs do not create extra planned steps.
Counts do not measure effort, remaining days, quality or PBI acceptance.

Confirmations link question, owner/due date, steps and versions. answer and
application are separate records. A test finding can trigger recorded impact and
revalidation while prior observation evidence remains retained. The actual
change/review/acceptance owner supplies decisions. Current design decisions and
separate judgment history are referenced instead of duplicating history in design.
Local PBI acceptance remains separate from task completion and Azure state.

## Boundaries and continuity

work/sessions and local judgment/evidence locations hold execution history;
work/plans holds authoritative JSON and derived Markdown. Work directory names
are actual implemented storage boundaries, not a mandate to copy entire source
trees into them. Baseline and candidate versions must be explicitly referenced.
The recorder is local-only, with no Azure imports, credential lookup or network
execution. Azure-free plans can use empty external_refs. No background executor,
automatic observation capture, external synchronization or automatic acceptance
is implied. Remote sharing of local files is not established.

## Sources and validity

- source_type: repository_source
- source_revision: working tree based on a5e3b354; package extension identified by current source hashes in the linked findings
- source_path: xrefkit/work_management.py; xrefkit/plan_markdown.py; xrefkit/plan_observation.py
- source_locator: register_workspace; validate_plan_v2; plan_definition; record_plan; task_counts; package_task_counts; regenerate; publish_projection
- supporting_tests: tests/test_work_management.py; tests/test_plan_markdown.py; tests/test_work_packages.py
- inspected_at: 2026-10-11
- supporting_structure: [Source findings](../source_analysis/173_xrefkit_python_client_work_structure_findings.md#xid-D4B4C2657A63)
- optional_integration: [Azure operating model](160_azure_devops_client_work_integration.md#xid-C8E2A591D740)

Revalidate after schema, persistence, counts, ownership or projection changes.
Fixture validation establishes bounded local operation, not human approval,
editor rendering in every client, or multi-host locking guarantees.
