<!-- xid: B87A2C3E4568 -->
<a id="xid-B87A2C3E4568"></a>

# Skill: commonality_derivation

## Purpose

Run a secondary pass over completed downward or upward derivation outputs to
identify commonality candidates and scope-boundary checks without deciding
integration automatically.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Commonality derivation signals](../../../../knowledge/packs/constraint-derivation/180_commonality_derivation_signals.md#xid-9C27AE51D648)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Commonality derivation output template](../references/commonality_derivation_output_template.md#xid-B6A11501AD6D)

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
