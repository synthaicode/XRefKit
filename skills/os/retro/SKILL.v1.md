---
schema_version: 1
skill_id: retro
xid: D7F1A4C9B280
summary: review work evidence and propose stable promotion candidates while keeping transient items in work
applies_when:
- a task or work session is ending and the agent should determine whether stable rules, knowledge, or procedures must be promoted out of `work/
exclusions:
- do not treat work as canonical
- promote unstable notes
- or duplicate canonical content
inputs:
- current task goal, related `work/sessions/` or `work/retrospectives/` files, changed files, optional conversation history, optional target canonical paths
outputs:
- promotion candidate list, target location per candidate, reasons, evidence references, already-promoted checks, stay-in-work decisions, optional draft update plan
criteria:
- id: stability
  statement: Candidates are classified by reuse, stability, evidence, and whether they are already canonical.
  verification: Inspect each candidate classification and evidence path.
- id: destination
  statement: Every proposed promotion has one target class or is explicitly stay_in_work.
  verification: Review target location and reason for every row.
- id: human_boundary
  statement: Promotion remains a proposal unless the human approves implementation.
  verification: Check the report for explicit disposition and next owner.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: working_area_policy
  query: working area policy
  required_when: Required when reading work records and deciding canonical boundaries
  seed_xids:
  - 111D282CA0EA
- id: shared_memory_operations
  query: shared memory operations
  required_when: Required when candidates affect shared memory
  seed_xids:
  - 4A423E72D2ED
control_refs:
- 111D282CA0EA
aliases:
- C17B52E8F4A3
- 6E8296A4C2D1
---
<!-- xid: D7F1A4C9B280 -->
<a id="xid-D7F1A4C9B280"></a>

# Skill: retro

## Purpose
Review session evidence and determine what remains in `work/` versus what may be promoted to canonical assets.

## Method
1. Confirm the session entry, relevant work files, changed files, and canonical search scope.
2. Resolve working-area and shared-memory Knowledge as applicable.
3. Extract reusable stable rules, facts, procedures, and structural issues; classify each as promotion candidate, already promoted, or stay_in_work.
4. Check reuse, stability, future reload value, and equivalent canonical content for every candidate.
5. Produce the promotion report with item, target, reason, evidence, and status.

## Stop and handoff
- Downgrade weak or single-session items to `stay_in_work`; do not create canonical updates from them.
- Promotion requires human approval; hand the report and any approved update plan to `doc_ship`.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: retro

## Purpose

Review current session evidence and determine what should remain in `work/` versus what should be promoted into canonical repository assets.

## Required Knowledge (XID)

- [Working area policy](../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)
- [Shared memory operations](../../../docs/core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED)

## Inputs

- current task goal
- relevant `work/sessions/` and `work/retrospectives/` files
- changed files from the current task
- optional conversation history
- optional expected target area supplied by the user

## Outputs

- promotion candidate report
- target location per candidate:
  - `docs/`
  - `knowledge/`
  - `skills/` or `skills_private/`
  - `agent/`
  - `stay_in_work`
- evidence reference for each candidate
- duplication or already-promoted check result
- optional update plan for approved promotions

## Startup

- Confirm that the current task has a `work/sessions/` entry.
- Identify the session logs and retrospectives relevant to the current task.
- Identify the changed files and the surrounding canonical area.
- Load the working area and shared memory rules before classifying candidates.

## Planning

- Extract from `work/` only the items that look reusable beyond the current session:
  - stable operational rules
  - stable domain facts
  - repeated procedures
  - recurring structural quality issues
  - missing role or routing definitions
- Define the target class for each candidate:
  - `docs/` for stable operational or design policy
  - `knowledge/` for stable domain facts or review knowledge
  - `skills/` or `skills_private/` for reusable procedures
  - `agent/` for stable agent contract, routing, or role definitions
  - `stay_in_work` for transient logs, unresolved items, and single-session notes

## Execution

- Read the relevant `work/` files.
- For each candidate item, check:
  - whether it is reused or likely to be reused
  - whether the decision or fact is stable
  - whether later sessions should reload it
  - whether equivalent canonical content already exists
- Classify each candidate as one of:
  - `promote_to_docs`
  - `promote_to_knowledge`
  - `promote_to_skill`
  - `promote_to_agent`
  - `stay_in_work`
  - `already_promoted`
- When the item is a structural quality issue that remains relevant beyond one session, prepare a summary row candidate for the system quality feedback register.
- When the item is a new reusable procedure, prefer a narrowly scoped skill over a broad generic skill.

## Monitoring and Control

- Downgrade any weakly supported or still-changing item to `stay_in_work`.
- Mark any item already reflected in canonical files as `already_promoted`.
- Do not copy large factual blocks into a skill; send facts to `knowledge/`.
- Do not create a canonical update when the item is only a local execution detail.

## Closure

- Produce a promotion report for the current task.
- For each promoted or proposed item, include:
  - item name
  - target location
  - candidate target file
  - reason
  - evidence path
  - status
- If the user approves implementation:
  - update the target canonical files
  - run `python -m xrefkit xref init` when new managed files are added
  - run `python -m xrefkit xref fix`
  - keep a short pointer in the `work/` record showing the moved-to path and date

## Rules

- Never treat `work/` as canonical source of truth.
- Never promote a single-session note without checking whether it has become stable.
- Never duplicate existing canonical content without confirming the gap first.
- Prefer the smallest canonical destination that preserves reuse.
- Keep the promotion decision evidence-backed and path-specific.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: review session logs and current work artifacts, then propose promotion candidates from `work/` into canonical repository assets

- use_when: a task or work session is ending and the agent should determine whether stable rules, knowledge, or procedures must be promoted out of `work/`

- input: current task goal, related `work/sessions/` or `work/retrospectives/` files, changed files, optional conversation history, optional target canonical paths

- output: promotion candidate list, target location per candidate, reasons, evidence references, already-promoted checks, stay-in-work decisions, optional draft update plan

- constraints: do not treat `work/` as canonical; do not promote unstable notes; do not duplicate existing canonical content without checking first

- lifecycle:
  - startup: confirm the relevant session logs, changed files, and canonical search scope
  - planning: identify candidate decisions, facts, or procedures and define canonical target classes
  - execution: compare `work/` content against existing `docs/`, `knowledge/`, `skills/`, and `agent/` content and classify each candidate
  - monitoring_and_control: downgrade weak or single-session items to `stay_in_work`; mark already-promoted items explicitly
  - closure: produce a promotion report and, when approved, prepare the canonical update set and `work/` pointer update

- tags: `retrospective`, `promotion`, `knowledge-ops`

- knowledge_slots:
  - name=working_area_policy; bind=111D282CA0EA
  - name=shared_memory_operations; bind=4A423E72D2ED
