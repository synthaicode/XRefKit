<!-- xid: 466B980B8ED3 -->
<a id="xid-466B980B8ED3"></a>

# Skill: csharp_review

## Purpose

Review C# code for issues that are not already detectable by Roslyn diagnostics.
Check the following domains:

- attribute value misuse (rule-based, not fixed whitelist)
- resource usage efficiency
- synchronization and concurrency correctness
- support lifecycle expiration risks

Use the canonical spec in `knowledge/csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA`.

## Required Knowledge (XID)

- [C# review spec](../../knowledge/csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA)
- [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)
- [C# custom framework analysis criteria](../../knowledge/csharp/110_custom_framework_analysis_criteria.md#xid-30E6A4F6F3AB)

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

## Startup

- Confirm the target path exists.
- Confirm the review scope is defined when filters are supplied.
- Load the C# review spec.
- Record `needs_confirmation` if the repository or project boundary cannot be established cleanly.

## Planning

- Define the review scope:
  - repository
  - solution
  - project
  - directory or file subset
- Define the output mode:
  - `findings-only`
  - `findings-with-fixes`
- Prepare review targets and category buckets for:
  - attribute value misuse
  - resource efficiency
  - synchronization
  - support lifecycle
- If a custom framework is present, identify:
  - framework lifecycle
  - extension points
  - convention rules
  - framework/application boundary

## Execution

- Establish Roslyn baseline:
  - run build or analyzers and collect diagnostics
  - mark diagnostics-covered concerns as out of scope for this skill
- Execute attribute misuse checks for each relevant attribute:
  - resolve library or source of attribute
  - identify required preconditions for the attribute to function
  - verify those preconditions in the project
  - if preconditions are not satisfied, report a finding
- Execute resource efficiency checks:
  - disposable resource lifetime and ownership
  - avoidable allocations and buffering patterns
  - network, file, or database usage patterns that cause unnecessary overhead
- Execute synchronization checks:
  - lock ordering, deadlock risk, race-prone shared state
  - blocking in async paths and context-capture pitfalls
  - cancellation and timeout propagation
- Execute support lifecycle checks:
  - target framework support status
  - package or runtime dependencies with expired or near-expired support
- When a custom framework is present:
  - verify framework lifecycle from local evidence
  - verify framework extension points from base code and existing usage examples
  - treat unsupported assumptions about framework behavior as `needs_confirmation`
- Report findings with concrete evidence and remediation.

## Monitoring and Control

- Check that diagnostics-covered issues are excluded from this skill's findings.
- Downgrade unclear or unverifiable results to `needs_confirmation`.
- Separate:
  - unresolved attribute origin
  - unresolved precondition verification
  - proven misuse
- Preserve missing evidence explicitly in each affected finding.

## Closure

- Return findings with evidence, severity, and remediation.
- Return category summaries for attribute value misuse, resource efficiency, synchronization, and support lifecycle.
- Mark baseline collection failure or unresolved verification as explicit review conditions.

## Rules

- Exclude issues that Roslyn diagnostics already detect.
- Do not use fixed attribute value whitelists as a hard gate.
- For unknown/new attribute values, use `needs_confirmation` unless a hard violation is proven.
- Separate `unresolved attribute origin` from `precondition not satisfied`.
- Include evidence in every finding (file path, config node, project setting, or package reference).
- Do not assume public-framework behavior for an application-specific framework without local evidence.

## Failure Handling

- If Roslyn baseline cannot be collected, continue review and mark output with `baseline_unavailable`.
- If project preconditions cannot be statically verified, output `needs_confirmation` with missing evidence.
- If lifecycle status source cannot be resolved, output `needs_confirmation` and list required source URLs.
