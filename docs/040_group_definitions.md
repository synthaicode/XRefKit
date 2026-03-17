<!-- xid: 8B31F02A4009 -->
<a id="xid-8B31F02A4009"></a>

# Group Definitions

This page defines the groups used by the business-capability model, including their responsibility boundaries, prohibited actions, and typical outputs.

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

### Typical Outputs

- technical clarification inputs
- execution-plan drafts
- dependency and sequencing decisions

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

### Typical Outputs

- code changes
- unit test results
- unresolved list

## Quality Group

### Responsibility

- evaluate outputs against higher-level evidence
- detect leaks, missing records, and unsupported judgments
- provide quality-gate evaluations for CAB
- perform quality-side self-check on review completeness and evidence traceability before returning or handing off judgments
- detect recurring or structural quality degradation across workflows and emit system-level quality feedback

### Must Not Decide

- final release approval
- implementation policy
- business-priority decisions

### Typical Capabilities

- code review
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
- Coordinator routes reassignment when the corrective action crosses boundaries.
- Human decision-makers approve major corrective direction when business, release, or risk posture is affected.

## Related

- [Capability layering](031_capability_layering.md#xid-8D50A972BA9F)
- [Closure workflow](034_closure_workflow.md#xid-8B31F02A4003)
- [CAB workflow](039_cab_workflow.md#xid-8B31F02A4008)
