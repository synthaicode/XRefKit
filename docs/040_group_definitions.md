<!-- xid: 8B31F02A4009 -->
<a id="xid-8B31F02A4009"></a>

# Group Definitions

This page defines the groups used by the business-capability model, including their responsibility boundaries, prohibited actions, and typical outputs.

## Common Rule

- Groups evaluate, execute, and record within their assigned boundary.
- Human decision-makers approve, accept risk, and make final release decisions.
- A group must not silently cross into another group's decision boundary.

## Planning Group

### Responsibility

- define value, constraints, priorities, estimates, assumptions, and requirement drafts
- prepare business-facing evaluation for CAB

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

### Typical Outputs

- escalation records
- reassignment requests

## Cross-Group Handoff Rule

- When a group reaches `unknown`, preserve the evidence gap and hand it off explicitly.
- When a group reaches `out_of_scope`, preserve the reason and route it through escalation.
- When a group finishes, closure control must confirm that no `missing` rows remain.

## Related

- [Capability layering](031_capability_layering.md#xid-8D50A972BA9F)
- [Closure workflow](034_closure_workflow.md#xid-8B31F02A4003)
- [CAB workflow](039_cab_workflow.md#xid-8B31F02A4008)
