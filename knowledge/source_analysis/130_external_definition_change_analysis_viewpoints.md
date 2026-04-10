<!-- xid: 4D91A26BE301 -->
<a id="xid-4D91A26BE301"></a>

# External-Definition Change Analysis Viewpoints

This page defines viewpoints for analyzing an application whose structure or behavior is controlled by external definitions such as XML, YAML, JSON, properties files, or framework-specific configuration files.

## Core Viewpoints

| Viewpoint | What to confirm |
|------|------|
| Definition inventory | which external files define routing, DI, flow control, validation, mapping, logging, scheduling, or other runtime behavior |
| Load order and override rules | how files are loaded, merged, imported, overridden, or conditionally activated |
| Definition-to-code mapping | which code, framework component, or runtime behavior consumes each meaningful definition |
| Entry points and framework activation | where bootstrap, loader, registration, and runtime activation start |
| Flow-control definitions | where routes, action mappings, transitions, validators, interceptors, and handlers are externally declared |
| Dependency and extension points | where external definitions connect application modules, plugins, or extension mechanisms |
| Logging policy | where logging behavior is controlled by definitions and code together, and what sensitive information must not be emitted |
| Concurrency and execution timing | where scheduling, retry, queue, async, timeout, and transaction behavior is controlled by definitions or supporting code |
| Performance-sensitive paths | where external definitions can alter expensive paths, fan-out, retry count, payload size, or other overhead |
| Resource efficiency | where definitions influence connection pools, thread usage, caching, file access, or other resource ownership and lifetime |
| Test boundary | which tests verify definition-driven behavior and where regression coverage is weak |
| Change impact and uncertainty | which targets are directly or indirectly affected and which conclusions remain `unknown` because evidence is missing |

## Mapping Rule

- Identify external files that define runtime structure or behavior.
- Confirm each file's role, load order, include/import relation, and override priority.
- For each meaningful definition element, confirm the consuming code or framework component.
- Confirm the activation condition:
  - loader
  - bootstrap sequence
  - registration
  - environment condition
  - runtime switch
- Mark the element as `unknown` when the consuming mechanism or activation condition cannot be confirmed.

## Logging Policy Rule

- Confirm both code-side logging calls and external-definition-side logging controls.
- Confirm level, sink, format, and environment-specific overrides.
- Confirm whether the change alters audit, monitoring, or alerting behavior.
- Confirm whether sensitive information could be emitted because of code or definition changes.

## Concurrency Rule

- Confirm schedulers, queue handlers, retry policies, timeout settings, transaction policies, and async execution controls that are declared externally.
- Confirm the consuming code paths for those controls.
- Confirm duplicate execution, ordering, and retry amplification risks.

## Performance And Resource Rule

- Confirm externally configurable fan-out, batch size, timeout, retry, caching, and payload controls.
- Confirm whether those settings change heavy-I/O paths, allocation pressure, or resource lifetime.
- Confirm whether long-running processes or externalized retry/schedule controls can retain threads, memory, or connections unexpectedly.

## Output Rule

Produce a Markdown note that records, for each viewpoint:

- state (`done`, `unknown`, or `not_applicable`)
- evidence
- change impact
- unresolved follow-up
