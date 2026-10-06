<!-- xid: 6B2D9F4A1C73 -->
<a id="xid-6B2D9F4A1C73"></a>

# Skill Reporting Contract

This contract makes the result of every Skill recognizable to a human and to
the next Skill in a workflow. It uses frontloaded, scan-friendly reporting:
the decision-relevant summary comes first, while detailed evidence remains
available through the task output and its evidence links. This contract defines
shared reporting principles; the active task and Skill own the visible format.

## Applicability

Apply this reporting protocol only when the conversation has an established
decision framework, such as agreed evaluation criteria, completion conditions,
or a review gate for the active task. Loading the protocol or selecting a
reporting profile does not by itself establish that framework.

When the conversation has no decision framework, do not apply this protocol.
Respond in ordinary conversational form without requiring its report headings,
status labels, or reporting profiles. Do not invent criteria or a decision
framework merely to apply the protocol.

This condition governs human-facing reporting only. Existing runtime recording,
verification, closure, and uncertainty obligations remain in force.

## Task-Owned Report Shape

The user's requested format takes precedence. Otherwise the active task and
Skill define headings, order, detail, and artifact type through their outputs,
method, and applicable criteria. A review table, an investigation narrative,
and a design artifact may therefore have different shapes. Do not prepend a
universal `Report` block or force empty sections into every output.

When this protocol applies, make the conclusion, material uncertainty or
blocker, supporting evidence, and any required next action easy to find in the
task's own format. Explain partial, blocked, escalated, or needs-review results
next to the result they qualify; a separate `Reason` heading is optional.
Keep workflow status distinct from a domain verdict when both are relevant.

Use the user's language for headings and prose. Stable runtime field names,
status enums, XIDs, paths, commands, and schema values retain their exact spelling.
There is no mandatory English or Japanese heading sequence.

Generic common-heading scaffolding in legacy Skills is a reporting example,
not a universal display requirement. This does not remove task-specific
checklists, evidence, coverage, acceptance criteria, or handoff obligations.
No declaration in this section changes the machine-readable Run Log format.

### Operational checkpoint details

For resumable work, include the purpose, completion conditions, scope,
validation conditions, current step, blocker, and next step when they help the
reader resume or decide. Their placement follows the task format. These details
supplement XID-backed evidence and Run Log work items, artifacts, concerns,
phases, verification, and closure; they do not replace them.

## Reader Perspective

When this protocol applies, every report MUST attach a brief reader perspective
near the conclusion in the task's format. A short inline label such as
`Perspective:` / `視点:` may be used; no additional heading is required.

Ground the perspective in the user's purpose and the established decision
framework. State which relationship, distinction, or change the reader should
focus on and why it matters for the next judgment. Do not substitute a generic
role label such as "from a technical perspective" for this guidance.

When the perspectives have an established or evidence-supported priority,
include their priority order and a brief reason so the reader knows what to
consider first. Base that order on the user purpose and decision framework.
Do not invent a ranking when no priority is established or supported; preserve
equal priority or an unknown ordering when relevant. Lower priority does not
mean excluded or exempt from required checks.

When relevant, distinguish what the evidence establishes from what still needs
human judgment, and state the condition that would require reconsideration.
Keep supporting detail and evidence reachable without requiring the reader to
reconstruct the main relationship from a file list or evidence table. The
perspective must not imply that an unverified area is safe to ignore, that a
prior evaluation still applies without checking its conditions, or that a
plausible explanation establishes correctness or human understanding.

For example, when reporting a completed procedural check with content quality
still unverified:

> 視点: 今回は、手続記録の検証完了と成果物の品質確認を分けて読んでください。
> この結果が示すのは前者であり、採用には未確認の品質を判断する必要があります。

This is reading guidance, not an additional approval gate or a new evaluation
criterion. If the perspective depends on missing context, name that unknown
rather than inventing the reader's purpose, authority, or decision framework.

## Finding And Checklist Anchors

When a report contains a checklist, category matrix, gate table, or other
summary that points to detailed explanations, every non-pass result must link
to its detail by a stable finding or check ID. Use an explicit anchor in the
detailed section and link to it from the summary, for example:

```md
| Category | Result | 詳細 |
| --- | --- | --- |
| Resource efficiency | `fail` | [CR-001](#cr-001), [CR-002](#cr-002) |

### CR-001 — connection cleanup can remain incomplete
<evidence, impact, and remediation>
```

The anchor ID must be the same stable ID used in the Run Log artifact or
finding record. A bare `fail` without a detail link is incomplete when a
finding or explanation exists. If a category is `pass`, `not_applicable`, or
`needs_confirmation`, link to the coverage note or open-item explanation when
one exists. The anchor is a human-navigation addition; status enum values stay
unchanged.

Category and checklist tables should also expose a short category description
link when the category name alone does not explain the review axis. Link to the
canonical Skill, Knowledge, contract, or other definition URL. Keep this
category-description link separate from the finding-detail link: the former
explains what the category means, while the latter explains why this run got
its result.

## Language Rule

The language of the user's latest clear request is the default report
language. Match the user's terminology and level of formality; do not silently
switch to English because a Skill or artifact was authored in English. When
the user explicitly requests another language, follow that request.

Keep these items stable and unlocalized where they function as machine keys or
exact identifiers:

- Run Log section keys and CLI field names;
- status enum values such as `done`, `blocked`, and `escalated`;
- Skill IDs, XIDs, artifact IDs, file paths, commands, code identifiers, and
  schema values.

Show a localized explanation beside a stable value when the value is shown to
the user, for example `完了 (done)` or `要確認 (needs-review)`. This separates
human readability from runtime parsing and cross-Skill interoperability.

The summary should normally be short enough to scan in one screen. Put the
most important conclusion, uncertainty, blocker, or requested decision first;
do not make the reader reconstruct the result from evidence tables. Use
descriptive headings and concise sentences. Include only evidence needed to
support the current decision, and link to the full artifact or Run Log for
detail.

When the workflow or gate status is `needs-review` / `要確認`, the report must
state the reason next to the affected result or verdict in its task format.
Do not make the reader infer the reason from a later findings table. The reason must name the
conditions that caused the downgrade, such as an active `major` finding, an
unavailable validation boundary, or an unresolved ownership decision, and may
link to the relevant finding anchors.

## Reporting Profiles

Profiles are optional patterns for task authors, not required universal output
formats. Select or adapt a pattern only when it fits the task. The headings and
tables below are examples; required content comes from applicable task criteria.

### `summary_first`

Use for ordinary investigation, planning, design, authoring, and operational
work. Put the conclusion and any next action where the reader can find them
before supporting detail, using the task's headings or prose.

### `gate_verdict`

Use for review and quality Skills. Keep the workflow `Status` separate from
the domain decision:

```md
### Gate Verdict
`proceed` / `needs-review` / `blocked`

### Verdict Reason
<why the gate has this result>
```

Do not collapse a gate verdict into the runtime status.

### `checklist_verdict`

Use for checklist-based review and self-check Skills. Explicitly list every check that was performed, its target,
its result, and its evidence. Do not report only failed items; an omitted
check is indistinguishable from a check that was never performed.

```md
### Checks Performed

| Check ID | What was checked | Target / Scope | Result | Evidence |
| --- | --- | --- | --- | --- |
| CHK-001 | cancellation is propagated | ImportJob.cs | pass | test-123 |
| CHK-002 | timeout behavior | ImportJob.cs | unknown | FND-002 |

### Coverage
- Completed: 1
- Unknown: 1
- Not applicable: 0
- Not checked: 0
```

Use `pass`, `fail`, `unknown`, or `not_applicable` consistently. If a check
was intentionally not performed, record `not_checked` with a reason and owner
instead of silently omitting it. If this profile also produces a gate verdict,
keep that verdict after the checklist and preserve the distinction between
coverage and approval.

### `phase_summary`

Use for multi-phase workflows. Make the overall conclusion easy to find;
phase-level summaries retain their own blockers and handoffs.

### `artifact_traceability`

Use when the main output is a structured design, analysis, traceability map,
or other reusable artifact. The artifact keeps its established title, schema,
and detailed section order; accompanying prose follows the task format. Do not prepend Markdown headings to a binary or machine-readable
artifact; report the summary beside it and link the artifact as evidence.

## Audience And Actionability

Write for the next decision, not for exhaustive narration. When applicable,
make the following explicit wherever the task format presents them:

- what changed or was produced;
- what is at risk or blocked, including impact;
- what decision or confirmation is required;
- who owns the next action and when it is due;
- where the supporting evidence can be inspected.

If a due date or owner is not known, write `unknown` and preserve it as an
open item rather than inventing one.

## Status Meaning

- `done`: the declared output and required checks are complete.
- `partial`: useful output exists, but the declared scope is not complete.
- `blocked`: progress cannot continue because a required input or decision is
  missing.
- `escalated`: the remaining issue requires human judgment or authority.

Do not use `done` to hide unresolved unknowns, risks, or handoff conditions.

## Runtime Record Boundary

The report is the human-facing summary. The Skill Run Log remains the
machine-readable record of work items, artifacts, concerns, phases, checks,
closure, and handoff. A report must point to the relevant artifacts or run log;
it does not replace runtime recording or `skill close`.

## MCP Compatibility

The MCP reporting payload uses version `2` for task-owned display. Existing
`required_sections` and `japanese_sections` keys remain arrays, both empty;
`example_sections` contains optional examples. `format_owner` identifies the
user request and active task or Skill, and `profiles_required` is `false`.
Runtime status values and CLI interfaces are unchanged.

The startup adapter accepts reporting versions `1` and `2`, validates the v2
format ownership fields, and rejects unknown versions. Workflow and prompt-flow
protocols retain their own version `1` restriction. A consumer that accepts only
reporting version `1` must be updated before receiving version `2`; an old
consumer's acceptance is not implied by retaining field names.

## Domain Extensions

Task-specific output shapes are owned by the Skill or artifact schema. Declare
report purpose, audience, output type, and required content in that task's
outputs, method, or criteria. Reference this contract for shared principles
instead of copying a common heading sequence into every Skill.

## Research Basis

This design adopts frontloading, scan-friendly descriptive headings, and
standardized status/risk/next-step fields from the [ONS guidance on structuring
content](https://service-manual.ons.gov.uk/content/writing-for-users/structuring-content)
and the [Atlassian project status report guidance](https://www.atlassian.com/agile/project-management/status-report).
