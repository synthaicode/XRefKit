<!-- xid: 6B2D9F4A1C73 -->
<a id="xid-6B2D9F4A1C73"></a>

# Skill Reporting Contract

This contract makes the result of every Skill recognizable to a human and to
the next Skill in a workflow. It uses frontloaded, scan-friendly reporting:
the decision-relevant summary comes first, while detailed evidence remains
available below it. A Skill may add domain-specific sections, but it must keep
the common summary visible in its human-facing report.

## Required Report Shape

Every human-facing Skill report starts with a `## Report` section containing
these headings:

```md
## Report

### Status
`done` / `partial` / `blocked` / `escalated`

### Reason
<required when Status is `partial`, `blocked`, `escalated`, or
`needs-review`; state the concrete condition that caused the status>

### Result
<what was produced or decided, in one or two sentences>

### Evidence
- <output or evidence artifact, source, check, or XID>

### Open Items
- <unknown, risk, judgment, or `なし`>

### Handoff
- Next owner: <role or human>
- Next action: <action or `なし`>
```

Keep the canonical field order stable, but express human-facing headings,
prose, reasons, open items, and handoff text in the user's language. The
canonical English field names may remain alongside a localized label when a
machine-readable bridge is needed, for example `Status / 状態`. If a section
has no content, use the user's equivalent of `なし` instead of omitting the
section. The report is summary-first; detailed domain sections and tables
follow it.

### Japanese human-facing format

When the latest clear user request is in Japanese, the human-facing report
MUST use the following overall form and heading order. This is the display
format for Japanese readers; it does not change Run Log keys, status enum
values, Skill IDs, XIDs, artifact IDs, paths, commands, or schema values.

```md
## 報告

### 結論
<what was found, produced, or decided>

### 状態
完了 / 一部完了 / 停止中 / 判断待ち

### 理由
<required for 一部完了, 停止中, 判断待ち>

### 確認したこと
- <facts, outputs, checks, sources, or XIDs>

### 残っている課題
- <unknown, risk, judgment, or `なし`>

### 次にすること
- 担当: <role or human>
- 作業: <next action or `なし`>
```

Use Japanese labels rather than English labels in the visible report. When a
stable machine value is important, show it beside the Japanese value, for
example `完了 (done)` or `判断待ち (needs-review)`. Keep `理由` immediately
after `状態` when it is required. Translate profile-specific sections as
follows while preserving their meaning: `Gate Verdict` becomes `判定`,
`Checks Performed` becomes `確認したこと`, `Coverage` becomes `確認範囲`,
`Phase Summary` becomes `段階ごとの結果`, and `Artifact Traceability`
becomes `成果物と根拠の対応`.
### Operational checkpoint extension

For multi-step or resumable work, a report may add the following operational
details after the common summary and handoff. These details make the current
execution state visible without changing the common report order:

```md
### 作業境界
- 目的:
- 完了条件:
- 対象範囲:
- 対象外:

### 検証条件
- コマンド or check:
- 期待結果:
- 最新結果:

### 現在の checkpoint
- 現在の step:
- 判断・ブロッカー:
- 次の step:
```

Use this extension only when the work can span meaningful steps, sessions,
agents, or verification gates. It supplements the Run Log and does not replace
XID-backed evidence, work items, artifacts, concerns, phases, `skill verify`,
or `skill close`.

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
state the reason immediately after `Status` (or `状態`). Do not make the
reader infer the reason from a later findings table. The reason must name the
conditions that caused the downgrade, such as an active `major` finding, an
unavailable validation boundary, or an unresolved ownership decision, and may
link to the relevant finding anchors.

## Reporting Profiles

Each Skill selects one reporting profile. The profile changes the detail after
the common summary; it does not remove the common status, result, evidence,
open-item, or handoff fields.

### `summary_first`

Use for ordinary investigation, planning, design, authoring, and operational
work. Put the conclusion and the next action in `Result` and `Handoff`, then
follow with the detailed report.

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

Use for checklist-based review and self-check Skills. In addition to the
common summary, explicitly list every check that was performed, its target,
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

Use for multi-phase workflows. The common `Result` is the overall conclusion;
phase-level summaries follow it and retain their own blockers and handoffs.

### `artifact_traceability`

Use when the main output is a structured design, analysis, traceability map,
or other reusable artifact. The human-facing report has the common summary
first, while the artifact keeps its established title, schema, and detailed
section order. Do not prepend Markdown headings to a binary or machine-readable
artifact; report the summary beside it and link the artifact as evidence.

## Audience And Actionability

Write for the next decision, not for exhaustive narration. When applicable,
make the following explicit in `Result`, `Open Items`, or `Handoff`:

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

## Domain Extensions

Existing domain-specific output shapes remain valid after the common `Report`
section. A gate, review, analysis, or publication Skill may add its own verdict,
tables, or detailed sections after `Handoff`, provided the common status,
result, evidence, open-item, and handoff information remains easy to find.

## Research Basis

This design adopts frontloading, scan-friendly descriptive headings, and
standardized status/risk/next-step fields from the [ONS guidance on structuring
content](https://service-manual.ons.gov.uk/content/writing-for-users/structuring-content)
and the [Atlassian project status report guidance](https://www.atlassian.com/agile/project-management/status-report).
