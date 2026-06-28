<!-- xid: 4E5B8923C912 -->
<a id="xid-4E5B8923C912"></a>

# Logic Constraint Derivation Catalog

## Derivation Areas

| Design element | Confirm as requirement | Decision class |
|---|---|---|
| branch or if/else | coverage of all branches including implicit else | requirement |
| AND/OR conditions | boundary values and all-false behavior | requirement |
| prioritized conditions | conflict priority when multiple conditions match | requirement |
| nullable flag | behavior when the flag is unset | requirement |
| amount calculation | rounding rule and timing | requirement |
| amount or quantity | zero and minus-value behavior | requirement |
| ratio calculation | divide-by-zero behavior | requirement |
| aggregate | zero-target behavior such as `null` vs `0` | requirement |
| period calculation | same-day, reversed range, leap and timezone behavior | requirement |
| state transition | allowed transitions, reverse transitions, terminal-state behavior | requirement |
| invalid state value | behavior on undefined state | requirement |
| parallel state | whether simultaneous active states are allowed | requirement |
| approval flow | rollback step, cancelability, absent approver, parallel decision behavior | requirement |
| rule or limit | over-limit response such as error, warning, or auto-adjust | requirement |
| duplicate check | precise definition of duplication | requirement |
| expiration | behavior for expired data | requirement |
| lock or exclusivity | access behavior while locked | requirement |

## Matrix Guidance

- Expand a transition matrix whenever current state and action both matter.
- Keep invalid transitions explicit instead of treating them as impossible by assumption.

## Output Shape

- derivation basis table with `LCD-` ids
- grouped confirmation items by logic unit
- explicit transition matrix when required

## Knowledge Relations

- part_of: [Constraint Derivation Framework](110_constraint_derivation_framework.md#xid-81A6C4E2B190)
