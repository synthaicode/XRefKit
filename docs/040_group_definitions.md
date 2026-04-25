<!-- xid: 8B31F02A4009 -->
<a id="xid-8B31F02A4009"></a>

# Group Definitions

This page defines the groups used by the business-capability model, including their responsibility boundaries, prohibited actions, and typical outputs.

This page defines role boundaries only.
For the one-page ownership map, see [Flow-to-group matrix](041_flow_to_group_matrix.md#xid-8B31F02A4010).
For within-flow quality control, see [Flow quality assurance mechanism](042_flow_quality_assurance_mechanism.md#xid-8B31F02A4011).
For cross-flow structural correction, see [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012).
For the boundary among these pages, see [Group, quality, and feedback boundaries](021_group_quality_and_feedback_boundaries.md#xid-8E5D31A4C672).

## Common Rule

- Groups evaluate, execute, and record within their assigned boundary.
- Each group is responsible for both execution and self-check within its own responsibility boundary.
- A self-check must verify only the outputs, assumptions, and records that belong to that group's responsibility.
- Human decision-makers approve, accept risk, and make final release decisions.
- A group must not silently cross into another group's decision boundary.
- A capability can be shared across multiple responsibilities; what changes is how that capability is exercised for the business purpose.
- The same expert capability may be exercised differently depending on the responsibility. For example, an accounting expert may use the same accounting capability differently for finance, bookkeeping, and management accounting.

## Group-Internal Work Pattern

Within a group boundary, work follows this pattern:

1. execute the assigned business activity
2. record evidence, assumptions, gaps, and metrics
3. perform self-check against that same responsibility boundary
4. hand off only after the group's own closure conditions are satisfied

The self-check in step 3 is not an independent external review. It is the group's own control step for confirming:

- the work stayed inside scope
- evidence and assumptions were recorded
- unresolved and out-of-scope items were preserved explicitly

## PMBOK Task Pattern

Each group executes its own work inside the responsibility boundary using the same task pattern:

1. Startup
2. Planning
3. Execution
4. Monitoring and Control
5. Closure

Interpretation inside this repository:

- `Startup`:
  - confirm inputs, scope, evidence, and triggers
- `Planning`:
  - define targets, work rows, assumptions, and handoff boundaries
- `Execution`:
  - perform the group's assigned business activity
- `Monitoring and Control`:
  - record status, metrics, gaps, and perform group-internal self-check
- `Closure`:
  - finalize rows and prepare explicit handoff

The self-check owned by a group is part of `Monitoring and Control`, not an external independent review.

## Capability, Tuning, Responsibility

- capability:
  - the reusable base professional ability
  - examples: accounting, software development, design, review
- tuning:
  - specialization applied to a capability
  - examples: construction-industry accounting, C# development, security-focused review
- responsibility:
  - how the tuned capability is exercised inside a group for a business purpose
  - examples: finance, bookkeeping, management accounting, implementation, code review

Example:

- base capability: accounting
- domain tuning: construction industry
- responsibilities:
  - finance
  - bookkeeping
  - management accounting

Another example:

- base capability: software development
- technical tuning: C#
- responsibilities:
  - implementation
  - unit testing
  - manufacturing self-check

## Planning Group

### Responsibility

- define value, constraints, priorities, estimates, assumptions, and requirement drafts
- confirm that test content matches the approved change specification and requirement intent
- prepare business-facing evaluation for CAB
- perform planning-side self-check on assumptions, estimates, and requirement framing before handoff

### Must Not Decide

- detailed implementation policy
- final design structure or execution ordering when that belongs to design work

### Typical Capabilities

- investigation, supplier, estimation, requirements, business evaluation

### Typical Outputs

- change target summary
- solution options
- requirement drafts
- planning test content review result
- value-gate results

## Design Group

### Responsibility

- define realization approach, decomposition logic, and execution order
- support technical clarification for requirements and planning
- perform design-side self-check on technical consistency, sequencing, and boundary assumptions before handoff

### Must Not Decide

- business value, priority, or final release approval

### Typical Capabilities

- investigation support
- performance requirement support
- task decomposition and plan drafting
- solution design
- test planning and test design

### Typical Outputs

- technical clarification inputs
- execution-plan drafts
- dependency and sequencing decisions
- approved design
- test plan and test design package

## Manufacturing Group

### Responsibility

- implement approved scope
- execute unit testing inside the approved design boundary
- record unresolved and out-of-scope items explicitly
- perform manufacturing-side self-check on implementation, unit-test results, and implementation assumption gaps before QA handoff

### Must Not Decide

- design-policy changes
- release approval or timing

### Typical Capabilities

- implementation
- unit testing
- test-method review

### Typical Outputs

- code changes
- unit test results
- unresolved list
- manufacturing test review result

## Quality Group

### Responsibility

- evaluate outputs against higher-level evidence
- detect leaks, missing records, and unsupported judgments
- review test artifacts and test results as product evidence against higher-level evidence
- provide quality-gate evaluations for CAB
- perform quality-side self-check on review completeness and evidence traceability before returning or handing off judgments
- detect recurring or structural quality degradation across workflows and emit system-level quality feedback

### Must Not Decide

- final release approval
- implementation policy
- business-priority decisions

### Typical Capabilities

- code review
- test-result and verification review
- release-plan suitability review
- management-table checks

### Typical Outputs

- review findings
- quality-gate results
- closure-check results

## Operations Group

### Responsibility

- prepare release-plan materials, monitoring definitions, and operational response procedures
- evaluate operational readiness for CAB
- perform operations-side self-check on release materials, readiness evidence, and operational assumption gaps before CAB handoff

### Must Not Decide

- final release approval or timing
- business-priority decisions

### Typical Capabilities

- release planning
- monitoring design
- event-response procedure drafting
- operational readiness evaluation

### Typical Outputs

- release plan draft
- monitoring specification
- event-response procedures
- operational readiness result

## AI Organization Explainer Video Team

This team is the marketing-facing successor name for the Parapara Video Creation Team.
`Parapara` describes the slide-based video format; the responsibility is to explain
the XRefKit AI organization model in an understandable marketing video.

### Responsibility

- define the marketing communication objective, target audience, viewer action, and completion criteria for an AI organization explanation video
- explain that XRefKit is an operating base for AI work, not a model-weight repository
- explain why AI work benefits from responsibility separation, knowledge externalization, workflow control, self-check, handoff, and OR Team improvement
- organize beginner and stakeholder understanding gaps and control explanation level
- read repository structure, documentation, and responsibility boundaries to prepare evidence-backed explanation inputs
- define the message backbone, scenario, chapter order, and one-message-per-slide script
- define slide specifications for what appears on each screen
- prepare narration scripts, estimate timing, generate audio, and tune pronunciation and reading flow
- recognize VOICEVOX Engine Docker as an available tool for audio generation work
- use VOICEVOX Aoyama Ryusei as the default baseline voice unless another voice is explicitly required
- use VOICEVOX No.7 as the next candidate voice when the baseline voice is not suitable
- design diagrams, icons, and visual density for slide presentation
- check content, order, repository-claim traceability, and expression consistency across all deliverables
- check whether the explanation is too difficult for first-time viewers
- control duration, transitions, audio synchronization, final video assembly, and distribution packaging
- include required license or attribution display on the last slide when the selected assets or voices require it
- verify that the message is understandable, aligned, memorable, and suitable for the requested marketing context before release

### Must Not Decide

- business-priority decisions outside the requested video objective
- approval of facts, claims, or policy positions that require an external owner
- official announcement wording unless assigned by the announcement owner
- final acceptance of the video when human sign-off is required

### Typical Capabilities

- project objective control
- audience and completion-criteria definition
- marketing message framing
- viewer-action definition
- learner model structuring
- explanation-level control
- repository reading
- terminology extraction
- claim-source mapping
- issue extraction
- scenario composition
- chapter flow design
- narration script writing
- slide specification design
- speech synthesis and reading adjustment with available tools including VOICEVOX Engine Docker
- default voice selection management with VOICEVOX Aoyama Ryusei as baseline
- fallback voice selection management with VOICEVOX No.7 as the next candidate
- diagram and icon direction design
- visual density control
- consistency review
- beginner-perspective review
- communication validation
- timeline editing
- audio synchronization
- final video packaging

### Typical Outputs

- work instructions
- chapter outline
- completion criteria
- marketing message backbone
- viewer-action definition
- explanation-level definition
- prohibited and supplemental term list
- repository explanation memo
- terminology glossary
- claim-source map
- issue list
- scenario outline
- one-message-per-slide script
- slide specification
- narration script
- duration estimate
- generated audio assets
- visual direction notes
- qa findings
- beginner review findings
- edit timeline
- distributed slide deck
- synchronized draft video
- final license slide
- validation findings

## OR Team

### Responsibility

- observe cross-group operating state using logs, deliverables, diffs, review results, rework history, escalation history, and drift-evaluation results
- present current state and baseline deviation for the AI organization as a whole
- structure problems, prepare cause hypotheses, and design improvement options
- organize approval requirements and decide stop, conditional continuation, or continuation allowed
- execute approved improvements inside the OR boundary and control execution by other responsible groups
- re-observe after change and confirm effect, side effect, and recurrence
- maintain drift-evaluation assets and operate the continuous-improvement loop

### Must Not Decide

- product implementation details that belong to execution groups
- business-priority decisions
- final release approval
- prohibited-judgment or approval-boundary changes without the required business or human approval

### Typical Capabilities

- state presentation
- anomaly detection
- problem structuring
- improvement design
- approval routing
- execution control
- re-observation
- drift evaluation
- evaluation-asset maintenance

### Typical Outputs

- state-presentation report
- problem list
- cause-hypothesis list
- improvement list
- approval-routing sheet
- implementation request
- re-observation report
- drift evaluation report

## Coordinator

### Responsibility

- route out-of-scope items for reassignment
- preserve handoff records

### Must Not Decide

- quality judgment
- scope change approval
- risk acceptance
- final release approval
- system-level quality priority

### Typical Outputs

- escalation records
- reassignment requests

## Cross-Group Handoff Rule

- A group must finish its own self-check before cross-group handoff.
- When a group reaches `unknown`, preserve the evidence gap and hand it off explicitly.
- If `unknown` remains unresolved after the next responsible group cannot resolve it, escalate it to human confirmation or approval.
- When a group reaches `out_of_scope`, preserve the reason and route it through escalation.
- When a group finishes, closure control must confirm that no `missing` rows remain.

## System-Level Quality Feedback Rule

- Quality Group detects structural quality degradation across workflows.
- Planning Group owns prioritization of upstream corrective action.
- OR Team maintains cross-group state presentation, intervention design, execution control, and re-observation for the corrective loop.
- Coordinator routes reassignment when the corrective action crosses boundaries.
- Human decision-makers approve major corrective direction when business, release, or risk posture is affected.

## Related

- [Group, quality, and feedback boundaries](021_group_quality_and_feedback_boundaries.md#xid-8E5D31A4C672)
- [Capability layering](031_capability_layering.md#xid-8D50A972BA9F)
- [Closure workflow](034_closure_workflow.md#xid-8B31F02A4003)
- [CAB workflow](039_cab_workflow.md#xid-8B31F02A4008)
- [OR Team operating model](048_or_team_operating_model.md#xid-1D7A8E2C5F10)
- [AI Organization Explainer Video Team operating model](057_ai_organization_explainer_video_team_operating_model.md#xid-2E8F4A1C9B73)
- [AI Organization Explainer Video Team usage guide](051_parapara_video_creation_team_usage_guide.md#xid-5A7C31D9E842)
