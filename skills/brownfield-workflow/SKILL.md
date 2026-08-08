---
name: brownfield-workflow
description: Structure brownfield change work across requirements, planning, design, manufacturing, and testing while surfacing unresolved items. Use when an existing codebase or system must be changed without treating its current implementation as the complete specification.
---
<!-- xid: A17C4E8B2D91 -->
<a id="xid-A17C4E8B2D91"></a>

# Brownfield Workflow

Use this Skill to carry one brownfield change through requirements, planning,
design, manufacturing, and testing. Preserve the upstream item as the
traceability anchor; do not create an independent task catalogue.

The Skill is an orchestration contract. Load detailed procedures from the
references only when the current item needs them:

- [Phase workflow](references/phase-workflow.md): phase inputs, outputs, gates,
  and handoffs;
- [Service, data, and impact investigation](references/service-data-impact.md):
  service ownership, DFD, Entity lifecycle, structure, and existing data;
- [File-edit integrity](references/file-edit-integrity.md): encoding,
  concurrency, specification alignment, history, and new-file conformity;
- [Change test suite](references/change-test-suite.md): scope, white-box
  structure, pre/post comparison, existing data, and regression evidence;
- [Reporting and closure](references/reporting-and-closure.md): overview/detail
  reports, evidence, unknowns, decisions, and handoff.

## Core contract

- Preserve the upstream item as the traceability anchor.
- Search applicable `knowledge/` before each phase judgment.
- Compare the change with the target's existing pattern and record
  `follows`, `adapts`, `introduces`, or `unknown`.
- Treat existing code and past Knowledge as evidence, not automatic business
  truth.
- Resolve service ownership and service-interaction/data-flow Knowledge before
  requirements become design.
- Keep current behavior, desired behavior, inference, and human decisions
  separate.
- Record every `unknown` with what is unknown, why, downstream impact, resolver,
  and owner. Do not turn missing evidence into "no impact".
- Do not create untraced work or approve human-owned requirements, design,
  release, or residual-risk decisions.

## Inputs

- user request and upstream work items;
- current-system evidence, source, tests, logs, configuration, and DB data;
- service catalog and service-interaction/data-flow Knowledge;
- constraints, risks, decisions, and decision owners;
- existing architecture, API, event, ERD, DDL, data-flow, or test artifacts.

If a required input is absent, record an impact-bearing `unknown` instead of
inferring it from a namespace, folder, one call site, or current behavior.

## Required item shape

Maintain each phase item with:

| Field | Meaning |
|---|---|
| `id` | Stable item identifier |
| `upstream_ref` | Requirement or plan item realized |
| `target` | Source, DB, API, test, configuration, or operation |
| `phase_result` | Concrete current-phase result |
| `state` | `done`, `unknown`, or `out_of_scope` |
| `basis` | Evidence, source location, or decision basis |
| `knowledge_refs` | XIDs used for the item |
| `pattern_decision` | `follows`, `adapts`, `introduces`, or `unknown` |
| `pattern_basis` | Existing pattern, delta, evidence, and owner |
| `impact` | Downstream effect |
| `next_action` | Confirmation, analysis, implementation, test, or handoff |
| `owner` | Person or role needed for the next decision |

## Phase responsibilities

### Requirements

Separate change purpose, evidenced current behavior, desired behavior,
acceptance conditions, scope, normal/error/boundary conditions, assumptions,
and unresolved decisions. Do not approve business requirements on behalf of
the responsible human.

### Planning

Define impacted targets, work units, dependencies, execution order,
compatibility/data/release/rollback policies, tools, versions, fixtures,
environment, test data, cleanup, result storage, risks, gates, and handoffs.
Prepare test tools in planning; execute tests in testing.

### Design

Define only the traced structural delta, responsibilities, API/message/DB/data
contracts, processing/state, transaction/idempotency/concurrency,
error/retry/timeout/rollback, compatibility/migration, observability, and
design-to-test handoff required by upstream items.

### Manufacturing

Implement only approved design items. Preserve existing file conventions and
uncommitted work. Stop an item as `unknown` or `blocked` if implementation
exposes an unresolved requirement, design, compatibility, or data decision.
Load [file-edit integrity](references/file-edit-integrity.md) before editing.

### Testing

Create or refresh the test suite before the implementation change. Confirm that
changed behavior meets the approved specification and that in-scope existing
behavior is not unintentionally broken. Load [change test suite](references/change-test-suite.md)
for scope, data, structure, selection, comparison, and reporting rules.

## Loading existing artifacts

Import existing service, flow, DB, or test artifacts before new discovery.
Preserve the source, search canonical Knowledge by identity and aliases,
classify `create`, `extend`, `refresh`, `split`, `reject_duplicate`, or
`proposal_only`, attach freshness and conflicts, and update canonical
Knowledge only under an authorized decision. Reuse an XID-bearing file under
`knowledge/` through `xref show`; do not duplicate it.

## Summary-first and closure

Every phase output starts with:

1. phase conclusion;
2. unresolved items ordered by downstream impact;
3. blockers and required decisions;
4. completed items;
5. next handoff;
6. links to detailed evidence.

Before closure, trace every in-scope upstream item to a result, attach evidence
and Knowledge/pattern basis, classify every unknown, record the next-phase input
package, and stop when proceeding would require guessing. Use the shared
[Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73)
with `Status`, `Result`, `Evidence`, `Open Items`, and `Handoff` in that order.
