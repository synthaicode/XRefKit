# Skill: csharp_review

## Purpose

Review C# code for issues that are not already detectable by Roslyn diagnostics.
Check the following domains:

- attribute value misuse (rule-based, not fixed whitelist)
- resource usage efficiency
- synchronization and concurrency correctness
- support lifecycle expiration risks

Use the canonical spec in `knowledge/csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA`.

## Inputs

- target path (repository root, solution, or project)
- optional scope filters (project, directory, file pattern)
- optional output mode (`findings-only` or `findings-with-fixes`)

## Outputs

- findings list with severity (`critical`, `major`, `minor`, `needs_confirmation`)
- for each finding: evidence path, violated condition, and remediation
- summary by category:
  - attribute value misuse
  - resource efficiency
  - synchronization
  - support lifecycle

## Procedure

1. Load review spec: `knowledge/csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA`.
2. Establish Roslyn baseline:
   - run build/analyzers and collect diagnostics
   - mark diagnostics-covered concerns as out of scope for this skill
3. Execute attribute misuse checks for each relevant attribute:
   - resolve library/source of attribute
   - identify required preconditions for the attribute to function
   - verify those preconditions in the project
   - if preconditions are not satisfied, report a finding
4. Execute resource efficiency checks:
   - disposable resource lifetime and ownership
   - avoidable allocations and buffering patterns
   - network/file/DB usage patterns that cause unnecessary overhead
5. Execute synchronization checks:
   - lock ordering, deadlock risk, race-prone shared state
   - blocking in async paths and context-capture pitfalls
   - cancellation and timeout propagation
6. Execute support lifecycle checks:
   - target framework support status
   - package/runtime dependencies with expired or near-expired support
7. Report findings with concrete evidence and remediation.

## Rules

- Exclude issues that Roslyn diagnostics already detect.
- Do not use fixed attribute value whitelists as a hard gate.
- For unknown/new attribute values, use `needs_confirmation` unless a hard violation is proven.
- Separate `unresolved attribute origin` from `precondition not satisfied`.
- Include evidence in every finding (file path, config node, project setting, or package reference).

## Failure Handling

- If Roslyn baseline cannot be collected, continue review and mark output with `baseline_unavailable`.
- If project preconditions cannot be statically verified, output `needs_confirmation` with missing evidence.
- If lifecycle status source cannot be resolved, output `needs_confirmation` and list required source URLs.
