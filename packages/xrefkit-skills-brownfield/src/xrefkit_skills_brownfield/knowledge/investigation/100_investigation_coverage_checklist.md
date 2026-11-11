<!-- xid: 91E2A7C56101 -->
<a id="xid-91E2A7C56101"></a>

# Investigation Coverage Checklist

This page defines the minimum coverage checklist used to prevent investigation leaks.

## Purpose

Ensure investigation work does not silently miss affected code, dependencies, data, interfaces, or test viewpoints.

## Coverage Areas

Every investigation should explicitly check the following areas.

| Area | What to confirm |
|------|-----------------|
| Service scope | in-scope and out-of-scope services are both recorded |
| Entry points | APIs, UI actions, jobs, batch triggers, or events that start the behavior are identified |
| Source files | changed or affected files are listed explicitly |
| Dependencies | called services, libraries, packages, and shared modules are checked |
| Data impact | database tables, queries, entities, and master data are checked |
| Interface impact | external and internal interfaces are checked |
| Configuration impact | config files, flags, environment variables, and settings are checked |
| Error paths | failure handling and fallback behavior are checked |
| Security impact | auth, authz, secret handling, and sensitive data paths are checked |
| Performance impact | bottlenecks, hot paths, and expensive operations are checked |
| Test viewpoints | unit, integration, regression, and edge-case viewpoints are recorded |
| Unknowns | evidence gaps are recorded explicitly instead of being skipped |

## Leak Prevention Rules

- A coverage area must never be omitted silently.
- If an area is not applicable, record `out_of_scope` with a reason.
- If an area cannot be confirmed, record `unknown` with the missing evidence.
- Investigation is not complete until every coverage area has a final state.

## Recommended Management Rows

Use one row per `(work, target, coverage_area)` when the task is high-risk or broad.

Recommended coverage-area labels:

- `service_scope`
- `entry_points`
- `source_files`
- `dependencies`
- `data_impact`
- `interface_impact`
- `configuration_impact`
- `error_paths`
- `security_impact`
- `performance_impact`
- `test_viewpoints`
- `unknowns`
