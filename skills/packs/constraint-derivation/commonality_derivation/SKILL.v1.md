---
schema_version: 1
skill_id: commonality_derivation
xid: E7B3C951A2D0
aliases:
  - B87A2C3E4568
  - B87A2C3E4567
summary: derive cross-cutting commonality candidates from completed primary constraint-derivation outputs
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
  - id: commonality_derivation_signals
    query: commonality derivation signals
    required_when: Required for this Skill's derivation and classification
    seed_xids:
      - 9C27AE51D648
control_refs:
  - 111D282CA0EA
---
<!-- xid: E7B3C951A2D0 -->
<a id="xid-E7B3C951A2D0"></a>

# Skill: commonality_derivation

## Purpose

Run a secondary pass over completed downward or upward derivation outputs to
identify commonality candidates and scope-boundary checks without deciding
integration automatically.

## Inputs

- completed derivation lists from one or more primary Skills

## Outputs

- CD-prefixed commonality candidate table written to a Markdown file
- CB-prefixed scope-boundary check table
- grouped human confirmation points
- written output path

## Startup

- Confirm the primary derivation outputs are available and traceable.
- Load the framework and the commonality signals.
- Verify this is a secondary pass, not a replacement for primary derivation.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_commonality_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Flatten all derivation outputs into one traceable list.
2. Match recurring patterns against the signal catalog.
3. Emit `CD-` items for commonality candidates and `CB-` items for boundary checks.
4. For each `CD-` item, show both the integration benefit and the non-integration risk.
5. Keep the final consolidation decision with the human.
6. Write the result by using `references/commonality_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not merge distinct rules just because their wording looks similar.
- Stop if primary derivation outputs are missing or incomplete.
- Keep source ids visible so later decisions remain traceable.

## Closure

- Return the candidate table, boundary-check table, and next human decisions.
- Highlight any missing primary outputs that reduce secondary-pass reliability.
- Return the written output path.
