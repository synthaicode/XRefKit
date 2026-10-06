<!-- xid: 5F21C8A41001 -->
<a id="xid-5F21C8A41001"></a>

# Common Source Analysis Criteria

This page defines language-neutral viewpoints for analyzing an existing codebase before planning, design, or review.

## Core Viewpoints

| Viewpoint | What to confirm |
|------|------|
| Entry points | where execution starts and how requests, jobs, or events enter the system |
| Responsibility split | how behavior is divided across layers, modules, services, or components |
| Dependency direction | which components depend on which others, and whether the direction is intentional |
| Extension points | where new behavior is naturally added without violating the current structure |
| Data boundary | where input, output, persistence, and mapping boundaries exist |
| Configuration boundary | where settings are loaded, overridden, and consumed |
| Error boundary | where failures are handled, translated, retried, or surfaced |
| Security boundary | where authentication, authorization, secret handling, and sensitive-data controls apply |
| Performance-sensitive paths | where expensive or high-frequency execution occurs |
| Operational hazard paths | where source-visible execution can amplify load, partially commit across boundaries, lose work ownership, hide failures, or expand blast radius |
| State and determinism boundary | where mutable state, state transitions, side effects, and deterministic replay assumptions are owned |
| Uncertainty and escalation path | where uncertain classification, parsing, prediction, threshold, or confidence outcomes become explicit unknowns or escalation handoffs |
| Contract and schema resilience | where external, model, message, or serialized formats are accepted, rejected, versioned, or treated as unknown |
| Traceability and context propagation | where trace ids, causality, source context, and structured execution metadata cross async, job, message, or agent boundaries |
| Test boundary | how unit, integration, regression, and edge-case tests are organized |
| Application/framework boundary | what belongs to reusable framework mechanisms versus application-specific code |

## Planning Rule

Planning should use these viewpoints to produce a modification policy that follows the current codebase structure by default.

## Unknown Rule

- If a core viewpoint cannot be confirmed, record `unknown`.
- Do not invent a cleaner target structure unless the current structure and deviation reason are both explicit.

## On-Demand Review Criteria

This XID retains the common criteria entry point. The structural viewpoints and
Planning / Unknown rules above apply before a topic is interpreted. The linked
criteria are separate canonical topics; links and semantic relations are lookup
handles, not recursive load commands. Resolve each required XID once for its
selected revision, and record the loaded scope and any unconfirmed axis.

For a source structure overview, change-location investigation, framework
structure analysis, or planning, use this core. Load a review topic only when
its boundary is needed to explain the current investigation. An error-policy
extraction uses the error-path topic for that axis and hands unrelated defect
judgment to review.

C# and Python review must screen every category required by their active Skill
and language spec using that category's axis. A headline such as synchronization
does not disable other active categories. Load each active axis below before
its disposition; when all ten axes are active, all ten topics are required.
Do not mark an axis pass without its required evidence, or not_applicable merely
because its detailed criteria were not loaded. Preserve existing missing-evidence
and handoff rules. The active Skill owns the report shape.

| Review axis | Canonical criteria (load when this axis is active) |
|---|---|
| resource_efficiency | [Resource Efficiency Review](101_resource_efficiency_review.md#xid-5F21C8A41101) |
| operational_resilience | [Operational resilience, hazard taxonomy and source basis](102_operational_resilience_review.md#xid-5F21C8A41102) |
| synchronization | [Synchronization And Concurrency Review](103_synchronization_concurrency_review.md#xid-5F21C8A41103) |
| required_input | [Required Input Integrity Review](104_required_input_integrity_review.md#xid-5F21C8A41104) |
| error_paths | [Error Handling And Exception Path Review](105_error_exception_path_review.md#xid-5F21C8A41105) |
| time_culture | [Time And Culture Review](106_time_culture_review.md#xid-5F21C8A41106) |
| state_determinism | [State And Determinism Boundary Review](107_state_determinism_review.md#xid-5F21C8A41107) |
| uncertainty | [Uncertainty And Escalation Path Review](108_uncertainty_escalation_review.md#xid-5F21C8A41108) |
| contract_schema | [Contract And Schema Resilience Review](109_contract_schema_resilience_review.md#xid-5F21C8A41109) |
| trace_context | [Traceability And Context Propagation Review](112_trace_context_propagation_review.md#xid-5F21C8A41110) |

Resource consumption and operational resilience additionally require the shared
[Overload and resource-control source basis](113_overload_resource_source_basis.md#xid-5F21C8A41111);
this prerequisite is selected once, not copied into both topics.
