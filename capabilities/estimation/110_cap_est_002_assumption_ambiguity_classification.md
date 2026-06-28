<!-- xid: B362EA06B9C2 -->
<a id="xid-B362EA06B9C2"></a>

# Capability: CAP-EST-002 Assumption Ambiguity Classification

## Definition

- capability_id: `CAP-EST-002`
- capability_name: `assumption_ambiguity_classification`
- work_type: `execution`
- summary: classify unresolved assumptions and produce items that require confirmation

## Preconditions

- assumption list from `CAP-EST-001` exists

## Trigger

- assumption-confirmation phase starts

## Inputs

- unresolved assumption list

## Outputs

- ambiguity classification result
- confirmation-required item list
- candidate requirement statements

## Required Domain Knowledge

- business rules
- constraint definitions

## Constraints

- classify and propose only
- do not confirm assumptions by itself
- preserve evidence gaps explicitly

## Assignment

- assumption-confirmation phase
- [Planning Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)
