---
schema_version: 1
skill_id: brownfield_workflow
xid: E1A7C4D9B260
summary: carry a brownfield change through traced phase outputs while preserving evidence, unknowns, and human decisions
applies_when:
- an existing codebase or system must be changed and upstream work items must be re-organized into phase outputs without guessing missing behavior
exclusions:
- do not create untraced work or approve human-owned requirements, design, release, or residual-risk decisions
inputs:
- request, current-system evidence, upstream phase items, constraints, risks, decisions, and optional existing Knowledge paths or source artifacts
outputs:
- summary-first phase results, traced work items, policies, post-reconciliation detail plans, evidence references, knowledge basis, existing-pattern decisions, knowledge-import results, existing-Requirement validation results, current-specification/new-requirement reconciliation results, protected invariants, design deltas, compatibility and downstream impacts, scope-adjusted DFD views, Entity change-point and lifecycle mappings, file-edit integrity records, round-trip verification, concurrency revision checks, specification-alignment decisions, bounded historical conflict investigations, uncommitted-state classifications, scoped same-extension code-rule majority decisions, new-file extension conformity decisions, testability gates, AI-generated test-case candidates, test-definition gaps, test-case traceability, unknowns, gates, and handoffs
criteria:
- id: traceability
  statement: Every phase item remains tied to its upstream item and records target, result, state, basis, impact, next action, and owner.
  verification: Inspect the phase output for complete item fields and one upstream reference per item.
- id: brownfield_integrity
  statement: Existing behavior is treated as evidence; edits preserve encoding, BOM, newlines, revision checks, and uncommitted work.
  verification: Check the integrity record, compare-and-swap revision result, and round-trip bytes before accepting an edit.
- id: unknown_and_authority
  statement: Missing evidence stays unknown with impact and resolver, and human-owned decisions remain handoffs.
  verification: Inspect unresolved items, owners, decision basis, and handoff artifacts for every material gap.
- id: coverage_and_tests
  statement: Scope, deterministic inventories, testability, and coverage limits are explicit before claiming completion.
  verification: Confirm each in-scope bucket is done, not_applicable, or unknown with evidence and next action.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: service_catalog
  query: service catalog ownership and responsibility boundary
  required_when: Required before requirements become design when service ownership is in scope.
  seed_xids:
  - 7A2F4C8D2201
- id: service_interaction_data_flow
  query: service interaction and data-flow viewpoints
  required_when: Required before implementation-facing design when cross-service or persistence flow is in scope.
  seed_xids:
  - 7A2F4C8D2301
- id: knowledge_ontology_management
  query: domain knowledge ontology and reuse rules
  required_when: Required when importing, refreshing, registering, or publishing existing Knowledge artifacts.
  seed_xids:
  - 5803607419B9
control_refs: []
aliases:
- A17C4E8B2D91
- 9B3D7A1C4E20
---
<!-- xid: E1A7C4D9B260 -->
<a id="xid-E1A7C4D9B260"></a>

# Brownfield Workflow

Carry one brownfield change through requirements, planning, design,
manufacturing, testing, and closure. Preserve the upstream item as the
traceability anchor; do not create an independent task catalogue. Search the
applicable Knowledge fragments before each phase judgment and classify the
relationship to existing patterns as `follows`, `adapts`, `introduces`, or
`unknown`.

## Phase method

1. Confirm the upstream item, target scope, current behavior, desired behavior,
   acceptance, decision owners, evidence, and phase. If any material input is
   absent, record an impact-bearing `unknown`.
2. In requirements, separate purpose, evidenced current behavior, desired
   behavior, acceptance, normal/error/boundary conditions, scope, and decisions.
3. In planning, define impacted targets, work units, dependencies, execution
   order, compatibility/data/release/rollback policy, tools, fixtures, gates,
   and handoffs. Prepare test tools and testability inputs here.
4. In design, reconcile current specification, evidenced current behavior, and
   new requirement. Define only the traced structural delta, protected
   invariants, contracts, state, transaction/idempotency/concurrency,
   compatibility, observability, and design-to-test handoff.
5. In manufacturing, implement only approved design items. Before editing an
   existing file, record encoding, BOM, newline convention, strict decode,
   original bytes or hash, approved spans, and a compare-and-swap revision
   token. Abort on concurrent changes, unclear specification alignment, or
   protected overlapping work. Use atomic replacement only after alignment is
   confirmed, then verify byte round-trip and semantic alignment.
6. In testing, execute the approved change-focused suite, compare pre/post
   behavior, and record expected result, observation source, evidence, and
   residual risk. Generate only traceable test candidates; do not invent
   inputs, expectations, business rules, or evidence sources.
7. In closure, trace every in-scope upstream item to a result, attach evidence
   and Knowledge/pattern basis, classify unknowns, record the next-phase input,
   and prepare the handoff.

## Brownfield file editing integrity

Before replacement, write through an atomically replaced temporary file only after the revision check passes.

Before editing an existing file, record its encoding, BOM, newline convention,
strict Unicode decoding, original bytes or hash, and approved spans. Preserve
the encoding/BOM/newline policy and verify the `after_bytes` round trip after
writing. This verifies encoding validity but does not hide pre-existing
mojibake. Use a compare-and-swap revision token: if the current bytes differ,
abort and do not overwrite concurrent work. Atomic replacement follows only
after the semantic edit contract and `semantic_alignment` are confirmed.

Treat the AI interpretation as a hypothesis, not authority; check the
authoritative specification, Knowledge, local pattern, schema, and tests.
When alignment is unclear, perform a bounded Historical conflict investigation
using Git history, `log`, `show`, `diff`, and `blame`, while
retaining current uncommitted and untracked state. Do not select the newest
revision as authority.

Apply the Uncommitted-file policy classifications
`pre_existing_human_or_unknown`, `ai_owned_current_work`,
`non_overlapping_changes`, and `mixed_or_overlapping`; never reset, checkout,
clean, or stash protected work without authorization. New-file extension conformity:
for new files, inspect same directory and same-extension peers, companion files,
extension-specific
rules, scope, cluster, majority, confidence, and repository-wide fallback.
Stop on a weak margin or unresolved pattern conflict.

## Required item shape

Each phase item records `id`, `upstream_ref`, `target`, `phase_result`, `state`
(`done`, `unknown`, or `out_of_scope`), `basis`, `knowledge_refs`,
`pattern_decision`, `pattern_basis`, `impact`, `next_action`, and `owner`.
Keep current behavior, desired behavior, inference, and human decisions
separate. Import existing service, flow, DB, or test artifacts before new
discovery; classify imports as `create`, `extend`, `refresh`, `split`,
`reject_duplicate`, or `proposal_only` and preserve freshness and conflicts.

## Coverage and stop conditions

Adjust DFD detail to the declared scope and distinguish primary, supporting,
and derived Entities. When in scope, map named change points, state
transitions, approvals, audit evidence, logical deletion, and downstream
propagation. Use deterministic inventories for coverage-critical questions; if
one cannot run, record an `unknown` and do not claim complete coverage.

Stop and hand off when requirement authority, meaning, scope, acceptance,
impact, data, owner, compatibility, or delta-specific execution policy is
missing or conflicting. Do not select history as authority merely because it
is newer. Suspected defects and security findings go to their respective
review Skills. Human owners decide requirements, design, release, and residual
risk; this Skill prepares evidence and questions for those decisions.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

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
- [Existing requirement validation](references/requirements-validation.md):
  validation of an existing Requirement's authority, freshness, consistency,
  testability, and human decision gate;
- [Specification reconciliation](references/specification-reconciliation.md):
  current specification, current behavior, and new requirement comparison
  before design approval;
- [Post-reconciliation detailed planning](references/delta-detail-planning.md):
  refinement of work, data, compatibility, test, evidence, and handoff plans
  from approved specification deltas;
- [IPA reconstruction guide mapping](references/ipa-reconstruction-guide-mapping.md):
  mapping from the human-oriented IPA reconstruction guidance to this Skill;
- [File-edit integrity](references/file-edit-integrity.md): encoding,
  concurrency, specification alignment, history, and new-file conformity;
- [Change test suite](references/change-test-suite.md): scope, white-box
  structure, pre/post comparison, existing data, and regression evidence;
- [Testability gate and AI case generation](references/testability-and-case-generation.md):
  design-time input completeness, traceable case candidates, and definition
  gaps before execution;
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

## Phase-based usage

Use the Skill for the phase that matches the current handoff. Carry the same
upstream item, evidence, unknowns, owners, and decisions forward; do not restart
the work as a new task catalogue.

| Phase | Ask the Skill to do | Main output | Stop when |
|---|---|---|---|
| `requirements` | Validate an existing Requirement or separate purpose, current behavior, desired behavior, acceptance, scope, normal/error/boundary conditions, and unresolved decisions | Requirement validation result, traced items, and decision questions | Requirement authority, meaning, scope, acceptance, or owner is missing or conflicting |
| `planning` | Create the initial work policy, then refine it from approved specification deltas | Initial work policy, post-reconciliation detail plan, impact scope, test inputs, gates, and handoff | Impact, data, owner, or delta-specific execution policy is unknown |
| `design` | Reconcile current specification, current behavior, and new requirement; then define the traced structural delta and contracts | Specification reconciliation, design-to-test handoff, testability result, case candidates, and definition gaps | A material delta lacks class, evidence, protected invariant, impact, owner, or human decision |
| `manufacturing` | Implement only approved design items while preserving file and concurrency integrity | Changed artifacts, integrity evidence, and exposed decisions | Implementation requires guessing or conflicts with the specification |
| `testing` | Execute the approved change-focused suite, collect evidence, compare pre/post results, and classify differences | Test results, evidence, residual risks, and retest needs | Expected result, evidence, or comparison basis is not approved |
| `closure` | Trace upstream items to results, classify unknowns, record decisions, and prepare the next handoff | Summary-first closure and residual-risk decisions | Any material unknown lacks impact, resolver, owner, or decision |

For a phase-specific request, state the phase explicitly, for example:
`Use $brownfield-workflow in planning phase to define the impact scope and
testability inputs for <upstream_ref>.` Load the detailed reference named in
the phase row only when needed.

## Inputs

- user request and upstream work items;
- current-system evidence, source, tests, logs, configuration, and DB data;
- service catalog and service-interaction/data-flow Knowledge;
- constraints, risks, decisions, and decision owners;
- existing architecture, API, event, ERD, DDL, data-flow, or test artifacts.
- design inputs needed to determine testability, including expected results,
  observation sources, fixtures, and owners.

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
and unresolved decisions. When an existing Requirement or equivalent upstream
definition is supplied, load [existing requirement validation](references/requirements-validation.md)
and validate its source, version, authority, owner, freshness, consistency,
and testability before using it for design or test generation. Do not rewrite or
approve business requirements on behalf of the responsible human.

### Planning

Define the initial work policy from the available Requirement and current-system
evidence: impacted targets, work units, dependencies, execution order,
compatibility/data/release/rollback policies, tools, versions, fixtures,
environment, test data, cleanup, result storage, risks, gates, and handoffs.
After specification reconciliation, load [post-reconciliation detailed planning](references/delta-detail-planning.md)
and refine the plan from approved delta rows before manufacturing or test-case
approval. Prepare test tools in planning; run the testability gate and generate
traceable case candidates in planning/design; execute approved tests in testing.

### Design

Define only the traced structural delta, responsibilities, API/message/DB/data
contracts, processing/state, transaction/idempotency/concurrency,
error/retry/timeout/rollback, compatibility/migration, observability, and
design-to-test handoff required by upstream items. After existing Requirement
validation, load [specification reconciliation](references/specification-reconciliation.md)
and compare the current specification, evidenced current behavior, and new
requirement before approving the design delta. Record protected invariants,
compatibility impact, downstream impact, and human decisions.
Confirm that each affected behavior has enough target, condition, expected
result, observation, evidence, and ownership information to define a
reproducible test case. Load [testability gate and AI case generation](references/testability-and-case-generation.md)
for the check and gap report.

### Manufacturing

Implement only approved design items. Preserve existing file conventions and
uncommitted work. Stop an item as `unknown` or `blocked` if implementation
exposes an unresolved requirement, design, compatibility, or data decision.
Load [file-edit integrity](references/file-edit-integrity.md) before editing.

Before replacement, write through an atomically replaced temporary file only
after the revision check passes.

#### Brownfield file editing integrity

Before editing an existing file, record its encoding, BOM, newline convention,
strict Unicode decoding, original bytes or hash, and approved spans. Preserve
the encoding/BOM/newline policy and verify the `after_bytes` round trip after
writing. This verifies encoding validity but does not hide pre-existing
mojibake. Use a compare-and-swap revision token: if the current bytes differ,
abort and do not overwrite concurrent work. Atomic replacement follows only
after the semantic edit contract and `semantic_alignment` are confirmed.

Treat the AI interpretation as a hypothesis, not authority; check the
authoritative specification, Knowledge, local pattern, schema, and tests.
When alignment is unclear, perform a bounded Historical conflict investigation
using Git history, `log`, `show`, `diff`, and `blame`, while
retaining current uncommitted and untracked state. Do not select the newest
revision as authority.

Apply the Uncommitted-file policy classifications
`pre_existing_human_or_unknown`, `ai_owned_current_work`,
`non_overlapping_changes`, and `mixed_or_overlapping`; never reset, checkout,
clean, or stash protected work without authorization. New-file extension conformity:
for new files, inspect same directory and same-extension peers, companion files,
extension-specific
rules, scope, cluster, majority, confidence, and repository-wide fallback.
Stop on a weak margin or unresolved pattern conflict.

### Testing

Create or refresh the test suite before the implementation change. Confirm the
testability gate and human decisions, then execute approved case candidates.
Confirm that changed behavior meets the approved specification and that
in-scope existing behavior is not unintentionally broken. Load [change test
suite](references/change-test-suite.md) for scope, data, structure, selection,
comparison, and reporting rules.

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

### Original Skill-specific declarations

- summary: organize brownfield change work across requirements, planning, design, manufacturing, and testing while surfacing unresolved items

- use_when: an existing codebase or system must be changed and upstream work items must be re-organized into phase outputs without guessing missing behavior

- input: request, current-system evidence, upstream phase items, constraints, risks, decisions, and optional existing Knowledge paths or source artifacts

- output: summary-first phase results, traced work items, policies, post-reconciliation detail plans, evidence references, knowledge basis, existing-pattern decisions, knowledge-import results, existing-Requirement validation results, current-specification/new-requirement reconciliation results, protected invariants, design deltas, compatibility and downstream impacts, scope-adjusted DFD views, Entity change-point and lifecycle mappings, file-edit integrity records, round-trip verification, concurrency revision checks, specification-alignment decisions, bounded historical conflict investigations, uncommitted-state classifications, scoped same-extension code-rule majority decisions, new-file extension conformity decisions, testability gates, AI-generated test-case candidates, test-definition gaps, test-case traceability, unknowns, gates, and handoffs

- constraints: do not treat existing implementation as complete specification; do not hide unknowns; do not add untraced work; adjust DFD detail to declared scope and decision purpose; distinguish primary, supporting, and derived Entities; map named change points, status transitions, human approvals, audit evidence, logical deletion, and downstream propagation when in scope; preserve confirmed file encoding, BOM, and newline policy during brownfield text edits; require strict decode/encode and byte round-trip verification; compare the pre-edit revision immediately before writing and abort on concurrent changes; require confirmed specification alignment before writing; investigate unresolved alignment conflicts using bounded history without treating history as authority; preserve and classify uncommitted worktree state before writing; do not discard or hide it without authorization; for new files, extract same-extension code-writing rules by coherent scope, use the local representative majority, and stop on weak or conflicting majorities; inspect required registration before creation; produce work policy in planning; prepare test tools and confirm testability in planning/design; generate only traceable test-case candidates; do not invent missing test inputs, expectations, business rules, or evidence sources; execute tests in testing; do not approve human-owned decisions

- knowledge_slots:
  - name=service_catalog; bind=7A2F4C8D2201
  - name=service_interaction_data_flow; bind=7A2F4C8D2301
  - name=knowledge_ontology_management; bind=5803607419B9

- lifecycle:
  - startup: confirm the available upstream items, current-system evidence, targets, decision owners, candidate Knowledge/pattern references, and any existing service/catalog/flow artifacts to import
  - planning: define phase scope, item schema, work policy, evidence policy, Knowledge reuse plan, tools, gates, and handoffs
  - execution: import existing service/catalog/flow artifacts when present, re-organize each upstream item for the current phase, apply relevant Knowledge, and classify its result and pattern decision
  - monitoring_and_control: downgrade unsupported claims to `unknown` and stop when proceeding requires a guess
  - closure: produce a summary-first output with decisions, unknowns, impact, owners, evidence, and next-phase handoff

- tags: `brownfield`, `requirements`, `planning`, `design`, `manufacturing`, `testing`, `knowledge-reuse`, `pattern-conformity`, `dfd`, `entity-lifecycle`

Original source description: Structure brownfield change work across requirements, planning, design, manufacturing, and testing while surfacing unresolved items. Use when an existing codebase or system must be changed without treating its current implementation as the complete specification.
