<!-- xid: D4F83A17B9C6 -->
<a id="xid-D4F83A17B9C6"></a>

# Correction Retrospective Design

Status: **review-ready proposal**, dated 2026-10-10. No automatic watcher,
retrospective trigger, Skill/Flow implementation, active rule, adoption or
personal-memory write is introduced by this document.

## Purpose and Human Boundary

When a result is corrected through dialogue, a separate analyst can reconstruct
the original result, explicit correction and revised result, then distinguish
local handling from a possible reusable improvement. The main assistant may
suggest a retrospective at a meaningful boundary; the human chooses whether,
when and over which scope it runs. Consent to analysis does not authorize
canonical publication or adoption.

Single acknowledgments such as "OK" are not agreement triggers. The proposal
must name its bounded scope and concrete reason. Topic transitions after
substantive corrections, major direction changes and task endings are useful
occasions, not mandatory count-based triggers. The existing QA -> human
corrective direction -> fix -> QA sequence remains unchanged.

## Existing Mechanisms and Proposed Delta

| Existing mechanism | Retained responsibility | Proposed connection |
| --- | --- | --- |
| [Instruction gateway](../guides/094_instruction_gateway.md#xid-E7A2C6109F43) | Explicit attempt/reason/evidence; quality retry versus requirement change; no inferred discontent or approval | Supply explicit correction evidence, not invented intent |
| [Human Evaluation](../core/contracts/082_human_evaluation_protocol.md#xid-7C4E2A91D8F0) | Optional closed-run evaluation and human-confirmed classification | Reuse when eligible; do not force run-boundary evaluation onto an open run |
| [Retro](../../skills/os/retro/SKILL.v1.md#xid-D7F1A4C9B280) | Stability, reuse, existing-source comparison; candidate or `stay_in_work`; human adoption | Reuse its improvement route with bounded correction-analysis inputs |
| [Work record types](../reference/019_work_record_types.md#xid-4F8C21B7D4A2) and [shared memory](../core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED) | Separate factual events, judgments and structural feedback | Link records instead of creating a competing history system |
| [Operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61) | Separate execution/progression/quality/handoff responsibilities | Deterministic progression success is not analysis-quality acceptance |

The proposed delta is a human-controlled suggestion and bounded analysis of
correction history, not a new QA role or automatic approval system.

## Operation and Responsibility

1. The main assistant continues normal work and records explicit corrections
   and changed requirements as facts. It does not launch analysis after every
   correction.
2. At a meaningful boundary it may ask once, with scope and reason, whether a
   retrospective would help. It does not state an uninvestigated cause as fact.
3. Explicit human execution intent establishes scope and timing. A direct
   answer to the scoped proposal can authorize analysis; an unrelated nod,
   standalone acknowledgment, silence or ambiguous reply cannot. Ambiguity
   leaves normal work proceeding without inferred authorization.
4. A separate analyst receives only the selected interval and relevant,
   version-identified materials. It analyzes observable responses and
   corrections, not internal model reasoning or presumed user psychology.
5. The analyst returns evidence-linked cause candidates, scope, alternatives,
   existing-rule comparisons and missing evidence. Unstable, one-off or
   unsupported findings remain `stay_in_work`.
6. The human decides whether any reusable change is adopted. Only that
   decision can start an eligible authoring/reflection route and, if adopted,
   the [shared update gate](113_shared_asset_update_gate_design.md#xid-A93D741E6BC2).

The main assistant owns suggestion timing and bounded preparation, the human
owns execution scope and adoption, the analyst owns evidence-based analysis,
and existing reviewers own output-content acceptance. They remain distinct.
Referenced promotion routes must pass their current runtime eligibility checks;
the draft/refused `doc_ship` at this base is not made executable by this design.

### Deterministic Analysis Entry After Human Consent

The main conversational agent only needs to propose the entry at a meaningful
boundary and submit it after explicit scoped human consent. The proposed
downstream sequence is `scoped consent -> deterministic envelope validation ->
actual host-owned isolated retrospective analyst -> structured result
validation -> human review and separate adoption decision`.

The envelope binds the human instruction, selected interval, task requirements,
material versions and relevant evidence locators. Deterministic validation
checks required inputs and that returned results belong to that same scope and
evidence packet; missing or mismatched execution/result evidence cannot be
treated as completed analysis. The host owns analyst dispatch, not the
deterministic validator. Cause and applicability judgments remain with the
isolated analyst, while the human retains execution timing/scope and adoption.
Declined-scope suppression and the ban on acknowledgment triggers still apply.

This is intended to reduce the main agent's attention burden after entry, but
that reduction is unmeasured. No dispatcher, validator or retrospective Skill
is implemented here; integration should reuse existing eligible mechanisms.

## Minimal State and Repeated-Suggestion Control

Record scope/artifact/run locators, explicit correction evidence, suggestion
reason, suggested interval, factual response, previously analyzed interval and
whether substantive new evidence exists. Physical storage and any integration
schema are implementation decisions; no new deployed CLI status is claimed.

- A declined, deferred or unanswered suggestion is not repeated for the same
  scope and reason. Substantive new correction evidence can justify a new
  suggestion with its changed basis and additional scope stated.
- An explicit later human request can initiate the specified analysis despite
  an earlier decline.
- Record what was analyzed; subsequent analysis distinguishes added intervals.
  Later corrections link to changed findings rather than silently overwriting
  their evidential history.
- Optional retrospective completion does not block normal task closure.
  There is no cross-chat watcher, automatic rule adoption or personal-memory
  save inferred from the interaction.

## Proposed Input and Output

| Input | Required evidence |
| --- | --- |
| Human instruction | Explicit analysis intent, scope and timing |
| Task basis | Goal, initial and changed requirements, scope and acceptance conditions |
| Correction sequence | Original result -> explicit correction -> revised result with message/artifact locators |
| Used materials | Relevant Skill/Knowledge/contract XIDs, versions/hashes and evidence of use |
| Final state | Explicit human evaluation, pending and unverified matters; no approval inferred from silence |
| Existing improvements | Relevant existing sources/candidates; an unsearched area cannot be labeled absent |

An output row carries the sequence, evidence locators, cause candidate and
rationale, applicability and counterexamples, existing XIDs, local action or
common-change proposal, unknowns and next owner/route. Preserve mixed causes
where justified. Missing input remains explicit rather than being reconstructed
as fact.

| Analytical candidate | Evidence basis | Handling |
| --- | --- | --- |
| Existing-rule application failure | Applicable contemporaneous rule compared with result | Investigate loading/execution; avoid duplicate rule additions |
| Requirement clarification/change | Previously unspecified or subsequently changed requirement | Preserve changed scope; do not invent past noncompliance |
| Local condition | Evidence of situation-specific applicability | Keep in work and hand off to the current task |
| Reusable improvement candidate | Existing gap, other uses, counterexamples and evidence | Human adoption decision; insufficient stability stays in work |
| Unknown/incomparable | Missing versions, requirements, use evidence or interval | State needed evidence; no cause certainty or promotion |

These are analytical candidates, not replacements for gateway feedback or Human
Evaluation schema enums. Cause classification, destination and human adoption
are separate decisions. Runtime progress follows the existing owning protocol.

## Recording and Future Placement

Session records hold factual instructions, corrections, suggestions and
responses. Judgment records hold nontrivial reasoning and alternatives.
Retrospective records hold structural feedback and inputs for existing retro.
Do not put the entire raw conversation into a canonical design document.

Future common suggestion/authorization control belongs in the appropriate
core/workflow conversation contract, not duplicated consumer Skill rules.
Extending existing retro is the first implementation option. A separate private
analysis Skill is an alternative if its responsibility needs a separate method;
public release and adoption require their own decisions.

Operational burden is part of the trial: load only the applicable shared
control and bounded analysis packet, rather than the entire rule corpus on
every turn. Reuse existing records and reviewers. Observe unnecessary
analysis, duplicate prompts and missed relevant checks alongside useful
improvements; do not add unrelated approval steps or invent numerical limits.

## Evaluation Plan, Not Executed Results

Fix input intervals/material versions and keep human-defined expected findings
separate from analyst inputs. Use fresh analysis contexts and multiple cases,
including true reusable gaps and valid local exceptions.

| Case | Expected observation |
| --- | --- |
| Standalone acknowledgment or mid-topic understanding | No inferred execution/adoption |
| Topic transition after correction | Brief scoped suggestion with reason; no forced interruption |
| Declined/deferred/unanswered same scope | No repeated identical suggestion |
| Substantive new correction after decline | New evidence and added scope are distinguishable |
| Explicit retrospective request after decline | Requested bounded analysis can run |
| Changed requirement versus existing-rule failure | Correct distinction with contemporaneous evidence |
| Local exception and genuine common gap | Neither indiscriminate promotion nor indiscriminate dismissal |
| Missing evidence/version | Unknown and needed evidence, not invented cause |
| Analysis consent only | No canonical adoption, publication or memory save |

Observe incorrect starts, repeated suggestions, classification disagreement,
unsupported causes, unnecessary promotion and missed reusable candidates.
Retain denominators and unevaluated cases. Acceptance thresholds are not
invented here; humans determine them using trial evidence. Repeated evaluation
observes improvement and side effects, not proof of zero recurrence.

## Open Decisions and Handoff

Unresolved: existing-retro extension versus a private analyst method; common
input/output record shape; safe interval/version capture; host-specific bounded
context transfer and notification; trial scope and human acceptance conditions.
Continuous or cross-chat monitoring requires host integration and is not an
XRefKit-only capability established by this proposal.

The design reviewer and human owner choose the minimal trial after review.
Behavioral evaluations, live-host integration, deployed triggers, runtime
quality of analyses, active contract changes and the shared gate are untested
or unimplemented. Document/link validation does not establish those outcomes.

## Design Provenance

The user requested analysis of correction-to-agreement history, distinguished
common improvement from local handling, rejected automatic acknowledgment
triggers, retained human execution control, and asked the AI to suggest useful
retrospective timing. The Japanese working proposal and conversation decisions
remain in local ignored work records, not published dependencies of this page.
This design is one of exactly two authorized design-only PR proposals.
