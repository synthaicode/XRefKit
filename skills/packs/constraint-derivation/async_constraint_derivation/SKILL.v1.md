---
schema_version: 1
skill_id: async_constraint_derivation
xid: 9A4C7E1D2B60
aliases:
  - F6580A1C2344
  - F6580A1C2345
summary: derive concurrency and asynchronous execution constraints from explicit design or code structure
applies_when:
  - source structure for this Skill may leave requirements implicit
exclusions:
  - Generic runtime possibilities without explicit structural evidence are outside this Skill
  - Implementation policy is not decided unless explicitly requested
inputs:
  - source material required by this Skill
outputs:
  - derivation basis table
  - confirmation items and remaining gaps
  - written output path
criteria:
  - id: evidence_boundary
    statement: Every derivation is grounded in explicit structural evidence and unsupported business meaning remains unresolved
    verification: Review each item against its source structure and record unresolved gaps
  - id: output_closure
    statement: The derivation output exists at the declared path and reports confirmation items and remaining gaps
    verification: Check the output path and closure report before handoff
knowledge_needs:
  - id: constraint_derivation_framework
    query: constraint derivation framework
    required_when: Required for this Skill's derivation and classification
    seed_xids:
      - 81A6C4E2B190
  - id: async_constraint_derivation_catalog
    query: async constraint derivation catalog
    required_when: Required for this Skill's derivation and classification
    seed_xids:
      - 72ECA94D1B35
control_refs:
  - 111D282CA0EA
---
<!-- xid: 9A4C7E1D2B60 -->
<a id="xid-9A4C7E1D2B60"></a>

# Skill: async_constraint_derivation

## Purpose

Derive requirement confirmation gates from asynchronous and batch execution
structure before restart and recovery behavior becomes implicit.

## Inputs

- queue designs, job definitions, batch specs, and schedule rules

## Outputs

- ACD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- rerun or restart matrices where required
- written output path

## Startup

- Confirm the input contains queue, job, batch, or schedule structure.
- Load the framework and the async catalog.
- Identify rerun, duplicate-start, partial-failure, and schedule-boundary surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_async_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate queue, job, batch, schedule, and state-management elements.
2. Apply the async catalog and assign `ACD-` ids.
3. Expand rerun or restart matrices where repeated or partial execution is possible.
4. Group the results by processing unit.
5. Keep unresolved restart, recovery, and schedule behavior explicit.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not assume successful rerun semantics from the platform alone.
- Stop if partial-failure handling or duplicate-start behavior is left unstated.
- Preserve traceability from each ACD item back to the execution structure.

## Closure

- Return the ACD table and grouped unresolved items.
- Highlight any restart, duplicate-run, or schedule gaps blocking implementation.
- Return the written output path.
