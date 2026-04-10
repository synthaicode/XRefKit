<!-- xid: 8C1F3DA2B6E4 -->
<a id="xid-8C1F3DA2B6E4"></a>

# Skill: external_definition_change_analysis

## Purpose

Analyze an application whose behavior or structure is driven by external definitions such as XML, YAML, JSON, properties files, or framework-specific configuration files, and produce a Markdown change-analysis note for later design or implementation changes.

Use the canonical viewpoints in `knowledge/source_analysis/130_external_definition_change_analysis_viewpoints.md#xid-4D91A26BE301`.

## Required Knowledge (XID)

- [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)
- [External-definition change analysis viewpoints](../../knowledge/source_analysis/130_external_definition_change_analysis_viewpoints.md#xid-4D91A26BE301)

## Optional References

- [External-definition change analysis template](./references/change_analysis_template.md)

## Inputs

- target path (repository root, application root, or configuration root)
- change request or analysis objective
- optional scope filters (module, config file, directory, feature, file pattern)
- optional output path for the generated Markdown

## Outputs

- Markdown change-analysis note
- definition-to-code mapping list
- impacted boundary list
- unresolved dependency list
- check results by viewpoint

## Startup

- Confirm the target path exists.
- Confirm the change request or analysis objective exists.
- Confirm the review scope is defined when filters are supplied.
- Load the external-definition change-analysis viewpoints.
- Record `unknown` when configuration ownership or load order cannot be established cleanly.

## Planning

- Define the analysis scope:
  - repository
  - application
  - module
  - configuration file subset
- Define the output path:
  - user-specified path
  - default working Markdown path when no path is supplied
- Prepare viewpoint buckets for:
  - configuration definition inventory
  - load order and override rules
  - definition-to-code mapping
  - entry points and framework activation
  - routing, flow, and transition control
  - dependency and extension points
  - logging and operational policy
  - concurrency and execution timing
  - performance and resource efficiency
  - test boundary
  - change impact and unresolved items
- If the scope can be separated by application or config family without cross-scope consistency risk, decompose the read-only investigation by scope and execute through subagents.

## Execution

- Identify the external definition files that control structure or behavior.
- Record file type, role, ownership boundary, and load order.
- Trace override, include, import, merge, and inheritance rules between definition files.
- Map each meaningful external definition element to the consuming code, framework component, or runtime behavior.
- Confirm the activation condition for each mapped element:
  - loader
  - bootstrap sequence
  - framework registration
  - runtime switch
  - environment condition
- Record routes, action mappings, transitions, validators, interceptors, handlers, and other flow-control definitions when present.
- Record logging policy, sensitive-data handling, and operational monitoring impact.
- Record concurrency, scheduling, retry, and transaction boundaries affected by external definitions.
- Record performance-sensitive paths and resource lifetime/ownership points affected by external definitions.
- Record test boundaries and the tests that should detect the intended change.
- Generate the Markdown note by using the template structure from `references/change_analysis_template.md` or an equivalent structure.

## Monitoring and Control

- Treat every viewpoint as recorded only when it has a state:
  - `done`
  - `unknown`
  - `not_applicable`
- Treat unrecorded viewpoints as analysis leaks.
- Downgrade weakly supported conclusions to `unknown`.
- Separate:
  - observed external definitions
  - confirmed consuming mechanisms
  - inferred change impact
  - missing evidence
- Preserve the evidence path for every non-trivial conclusion.

## Closure

- Return the Markdown change-analysis note.
- Return the definition-to-code mapping list, impacted boundaries, and unresolved items.
- Mark every uncertain or out-of-scope conclusion with its missing evidence or reason.

## Rules

- Do not decide implementation policy unless the user explicitly asks for it.
- Do not assume an external definition is active only because the file exists.
- For each meaningful definition, confirm:
  - definition location
  - consuming code or framework component
  - activation condition
  - change impact
- Treat unmatched definitions and unmatched consuming code as separate findings.
- Include load order, override priority, and environment-dependent activation when relevant.
- For logging, concurrency, performance, and resource analysis, include both code-side and external-definition-side controls.
- Use subagents only when scope boundaries stay explicit and cross-scope reasoning is not required.

## Failure Handling

- If configuration load order cannot be resolved, continue and mark `unknown`.
- If framework internals or external library source is unavailable, record the unresolved dependency and continue.
- If the Markdown output path is not writable, return the content and the intended path without deleting any existing files.
