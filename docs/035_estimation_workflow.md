<!-- xid: 8B31F02A4004 -->
<a id="xid-8B31F02A4004"></a>

# Estimation Workflow

This workflow defines how supplier checks, cost estimation, solution-option generation, and assumption classification are orchestrated.

## Purpose

Prepare grounded options and unresolved assumption lists before requirements work begins.

## Sequence

1. Run [CAP-SUP-001 Supplier Four-Condition Check](../capabilities/supply/100_cap_sup_001_supplier_four_condition_check.md#xid-2DC9A90A6508).
2. Run [CAP-SUP-002 Cost Estimation](../capabilities/supply/110_cap_sup_002_cost_estimation.md#xid-754A17D69C7C).
3. Run [CAP-EST-001 Solution Option Generation](../capabilities/estimation/100_cap_est_001_solution_option_generation.md#xid-BDB6B54A3571).
4. Run [CAP-EST-002 Assumption Ambiguity Classification](../capabilities/estimation/110_cap_est_002_assumption_ambiguity_classification.md#xid-B362EA06B9C2).
5. Hand off unresolved assumptions for confirmation.

## Related Skills

- [estimation_flow](../skills/estimation_flow/SKILL.md#xid-FB65EC653F0F)
- [management_table_control](../skills/management_table_control/SKILL.md#xid-D6DDBAC513BF)

