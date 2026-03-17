<!-- xid: 8B31F02A4010 -->
<a id="xid-8B31F02A4010"></a>

# Flow-to-Group Matrix

This page provides a one-page view of workflow ownership and cross-group handoff.

## Matrix

| Flow | Main owner group | Main input from | Main output to | Main handoff artifacts |
|------|------|------|------|------|
| [Application workflow](045_application_workflow.md#xid-8B31F02A4014) | Human decision layer with AI support | framework baseline, project brief, domain materials, stakeholder constraints | all normal workflows, with Investigation workflow as first consumer | domain knowledge injection record, capability tuning record, threshold configuration record, verification result, application completion record |
| [Investigation workflow](032_investigation_workflow.md#xid-8B31F02A4001) | Planning Group | request intake, domain references, technical materials | Planning Group estimation and requirements work, Design Group support | change target list, change viewpoints, test viewpoints, uncertainty list |
| [Estimation workflow](035_estimation_workflow.md#xid-8B31F02A4004) | Planning Group | investigation outputs, supplier and budget context | Planning Group requirements work | supplier comparison result, cost patterns, solution options, unresolved assumptions |
| [Requirements workflow](036_requirements_workflow.md#xid-8B31F02A4005) | Planning Group with Design Group support | estimation outputs, investigation outputs, confirmed assumptions | Design Group planning work, later Manufacturing scope definition | requirement draft, performance requirement definition, unresolved evidence list |
| [Planning workflow](037_planning_workflow.md#xid-8B31F02A4006) | Design Group | approved requirements from Planning Group | Manufacturing Group, management control initialization | task list, dependency map, execution order, group assignment draft |
| [Manufacturing workflow](033_manufacturing_workflow.md#xid-8B31F02A4002) | Manufacturing Group | design and plan outputs, requirement context when needed | Quality Group review, Operations Group release planning | implemented code, unit test results, self-check result, unresolved and out-of-scope lists |
| [Release planning workflow](038_release_planning_workflow.md#xid-8B31F02A4007) | Operations Group | manufacturing outputs, design and requirement materials | CAB workflow | release plan draft, monitoring specification, event-response procedure draft, operational readiness result |
| [CAB workflow](039_cab_workflow.md#xid-8B31F02A4008) | Quality Group, Operations Group, Planning Group in parallel evaluation boundaries | release-planning materials, manufacturing outputs, requirement and design evidence, value definitions | human decision layer | quality-gate result, operational readiness result, value-gate result, unresolved list |
| [Closure workflow](034_closure_workflow.md#xid-8B31F02A4003) | Quality Group for closure checking, Coordinator for reassignment routing | any workflow that produces management rows or unresolved items | responsible execution group, Coordinator routing, final handoff record | leak detection result, return instructions, closure confirmation, escalation record |

## Group Participation View

| Group | Main flows | Typical handoff direction |
|------|------|------|
| Human decision layer | application workflow, final approval, major uncertainty escalation | to Planning Group and all normal workflows through application completion record |
| Planning Group | investigation, estimation, requirements, CAB business evaluation | to Design Group, to human decision layer, to Coordinator for out-of-scope routing |
| Design Group | investigation support, requirements support, planning | to Manufacturing Group |
| Manufacturing Group | manufacturing | to Quality Group and Operations Group |
| Quality Group | QA review, CAB quality evaluation, closure checking | to human decision layer, to responsible execution group for return |
| Operations Group | release planning, CAB operations evaluation | to human decision layer |
| Coordinator | closure escalation, out-of-scope routing | to reassigned responsible group |

## Common Handoff Rule

- Each group completes `execution -> recording -> self-check -> handoff` inside its own boundary.
- Cross-group handoff begins only after the sending group finishes its self-check.
- `unknown` stays explicit across handoff.
- `out_of_scope` goes through Coordinator routing.

## Feedback Loop

- Normal work moves feed-forward across workflows.
- Structural quality degradation moves backward through the [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012).
- That loop is triggered mainly from CAB rejection patterns and closure leak patterns.
