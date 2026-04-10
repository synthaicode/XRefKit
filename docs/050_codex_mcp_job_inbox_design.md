<!-- xid: 77BCEAA247E3 -->
<a id="xid-77BCEAA247E3"></a>

# Codex MCP Job Inbox Design

This page is a design document for a concrete integration.
It is not the OR Team operating model and not a day-to-day usage guide.
For the boundary among operating models, usage guides, and design pages, see [Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583).

## Purpose

This page defines a realistic integration design between the Flow monitoring dashboard and Codex.

The design goal is not to inject text into a specific IDE chat box.

The design goal is to let the dashboard publish work requests as explicit jobs, and let Codex consume those jobs through MCP in a controlled, auditable way.

Related:

- [Workflow](010_workflow.md#xid-7D1E1C0279F1)
- [Manufacturing workflow](033_manufacturing_workflow.md#xid-8B31F02A4002)
- [Flow quality assurance mechanism](042_flow_quality_assurance_mechanism.md#xid-8B31F02A4011)
- [OR Team operating model](048_or_team_operating_model.md#xid-1D7A8E2C5F10)
- [Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583)

## Problem Statement

The current dashboard can present:

- which project and flow ran
- which steps were passed
- which paths were traversed
- whether decisions were recorded
- whether checklists were used

However, the current dashboard cannot directly cause Codex to start work in a robust way.

Direct UI-to-chat injection has the following problems:

- it depends on a specific IDE UI implementation
- it is brittle across product updates
- it is difficult to audit
- it does not define ownership, claim rules, or completion rules

Therefore the integration must be based on explicit work items rather than UI manipulation.

## Design Decision

Adopt an MCP-based job inbox between the dashboard and Codex.

The dashboard publishes jobs.
Codex reads, claims, executes, and completes jobs.

This keeps monitoring, execution request, and execution result as separate but connected concerns.

## Scope

In scope:

- adding a job model to the dashboard backend
- exposing project, flow, and job state through MCP
- defining how Codex checks for pending work
- defining claim, completion, and failure state transitions
- preserving traceability between monitoring evidence and execution jobs

Out of scope:

- typing text into a private IDE chat input
- relying on undocumented VS Code UI behavior
- replacing the existing flow-monitoring screens
- full approval workflow automation across all human decision layers

## Architecture

The target architecture is:

1. Flow Monitor UI
2. Flow Monitor backend
3. MCP server surface
4. Codex client
5. Existing project workspace and flow artifacts under `projects/`

The interaction is:

1. a human selects a project and flow in the dashboard
2. the dashboard creates a structured job
3. the MCP server exposes that job as pending work
4. Codex reads the pending job
5. Codex claims the job before execution
6. Codex performs the requested work
7. Codex completes or fails the job with a result summary
8. the dashboard shows the updated job state together with the flow evidence

## Core Design Principle

The dashboard does not control Codex by UI automation.

Instead, the dashboard becomes a control plane for:

- work discovery
- work claiming
- execution trace linkage
- completion visibility

Codex remains the execution agent.

## Data Model

Each job must contain at least the following fields:

- `job_id`
- `project`
- `flow_name`
- `job_type`
- `status`
- `title`
- `prompt`
- `created_at`
- `created_by`
- `priority`
- `source_run_key`
- `source_paths`
- `source_steps`
- `source_decisions`
- `source_checklists`
- `claim_owner`
- `claimed_at`
- `completed_at`
- `result_summary`
- `result_artifacts`
- `failure_reason`

Recommended additional fields:

- `required_skills`
- `required_inputs`
- `expected_outputs`
- `approval_state`
- `owner_group`
- `boundary_rules`
- `trace_id`

## Job Types

The first version should support a small fixed set:

1. `investigate`
2. `design`
3. `implement`
4. `review`
5. `reobserve`
6. `summarize`

These types are enough to map dashboard findings to the existing flow model.

## Job State Model

The state machine should be:

1. `pending`
2. `claimed`
3. `running`
4. `completed`
5. `failed`
6. `cancelled`

State rules:

- only `pending` jobs may be claimed
- claim must be atomic
- only the current claim owner may mark `running`
- only the current claim owner may mark `completed` or `failed`
- abandoned claims require timeout or explicit release handling

## MCP Surface

The first MCP surface should expose tools such as:

1. `list_projects`
2. `get_project_summary`
3. `get_flow_state`
4. `get_flow_definition`
5. `list_pending_jobs`
6. `get_job`
7. `claim_job`
8. `start_job`
9. `complete_job`
10. `fail_job`
11. `release_job`
12. `append_job_note`

Read-oriented resources may also be exposed for:

- flow definitions
- recent run history
- monitoring evidence by project
- active job queue

## Dashboard Responsibilities

The dashboard must remain responsible for:

- presenting monitoring evidence
- creating jobs from observed flow state
- linking jobs to source runs and source evidence
- presenting job queue status
- presenting completion and failure summaries

The dashboard must not become the execution engine itself.

## Codex Responsibilities

Codex must remain responsible for:

- reading jobs from MCP
- deciding whether the job is executable within its current boundary
- claiming the job before work starts
- executing only within the approved boundary
- writing back completion or failure status
- preserving uncertainty and unresolved items explicitly

Codex must not silently absorb approval gaps or ownership ambiguity.

## Codex Operating Model

The practical Codex behavior should be:

1. read `AGENTS.md`
2. check pending MCP jobs at session start or task start
3. select one job within current scope
4. claim the job
5. execute
6. complete or fail the job
7. check for the next pending job only when appropriate

This is intentionally a pull model.

The design does not require the dashboard to push text directly into an IDE prompt box.

## Session And Hook Strategy

The design may use Codex hooks and startup instructions to create a pseudo-loop:

- session start: inspect pending jobs
- stop hook: if queue policy says continue, start one more pass
- user prompt submit: inject context such as current claimed job

This creates a controlled inbox-processing workflow without relying on hidden IDE UI APIs.

## Traceability Model

Every job must be traceable back to the monitoring evidence that caused it.

Minimum trace chain:

1. project
2. flow
3. run
4. observed step/path/decision/checklist evidence
5. created job
6. claim owner
7. execution result
8. resulting artifacts

This allows the dashboard to answer:

- why this job exists
- which flow evidence triggered it
- who claimed it
- whether it completed
- what changed after execution

## Boundary Control

The integration must preserve explicit responsibility boundaries.

Examples:

- a monitoring finding does not automatically authorize implementation
- a design job does not automatically authorize manufacturing
- a review job does not automatically approve release

Each job must carry:

- current owner boundary
- approval expectation
- allowed output type
- escalation condition

## Failure Handling

The system must handle at least these failure cases:

1. Codex sees a job but cannot safely execute it
2. claim owner disappears after claim
3. output is incomplete
4. approval is required but missing
5. monitoring evidence is insufficient

For these cases the system must allow:

- `fail_job`
- `release_job`
- explicit unresolved notes
- dashboard visibility of blocked jobs

## Security And Governance

This design is safer than UI injection because:

- the control surface is explicit
- actions are state-based, not keystroke-based
- ownership is visible
- boundary rules can be attached to jobs
- results can be audited

The first implementation should assume local trusted use, but the design should preserve room for:

- authenticated creators
- per-project authorization
- approval-required job classes
- immutable audit logs

## Minimal Implementation Plan

Phase 1:

- add job storage to `flow-monitor-dashboard`
- expose basic MCP tools
- allow Codex to list, claim, complete, and fail jobs
- show job queue in the dashboard

Phase 2:

- add approval state
- add owner boundary and group linkage
- add richer trace links to steps, paths, decisions, and checklists
- add job timeout and reclaim policy

Phase 3:

- add re-observation linkage after completion
- add quality and control dashboards for job outcomes
- add OR Team views for intervention and recurrence tracking

## Why This Design Is Preferred

This design is preferred because it matches the operating model better than prompt-box automation.

Prompt-box automation is only message transport.

The MCP job inbox design provides:

- work definition
- ownership
- claim control
- completion control
- traceability
- boundary visibility

That is the level needed for brownfield flow monitoring and controlled AI execution.
