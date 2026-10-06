---
schema_version: 1
skill_id: auth_constraint_derivation
xid: C8F2A6D1E430
aliases:
  - A7691B2D3457
  - A7691B2D3456
summary: derive requirement confirmation gates from authentication and authorization structure
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
  - id: auth_constraint_derivation_catalog
    query: auth constraint derivation catalog
    required_when: Required for this Skill's derivation and classification
    seed_xids:
      - 8B14D9E70326
control_refs:
  - 111D282CA0EA
---
<!-- xid: C8F2A6D1E430 -->
<a id="xid-C8F2A6D1E430"></a>

# Skill: auth_constraint_derivation

## Purpose

Derive requirement confirmation gates from authentication and authorization
structure before access behavior is completed implicitly.

## Inputs

- auth design docs, role matrices, permission models, and account rules

## Outputs

- AACD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- session or permission matrices where required
- written output path

## Startup

- Confirm the input contains authentication or authorization structure.
- Load the framework and the auth catalog.
- Identify session, role, tenant, client-auth, and account-lifecycle surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_auth_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate authentication, authorization, client-auth, and account-management elements.
2. Apply the auth catalog and assign `AACD-` ids.
3. Expand permission or session matrices where the design exposes those axes.
4. Group the results by auth surface.
5. Keep unresolved security behavior explicit instead of assuming safe defaults.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not infer permission behavior from UI visibility alone.
- Stop if session-expiry, role gaps, or tenant-boundary behavior is left implicit.
- Preserve explicit traceability from each AACD item back to the access structure.

## Closure

- Return the AACD table and grouped unresolved items.
- Highlight any session or permission gaps blocking implementation.
- Return the written output path.
