<!-- xid: 2D14F88A6C01 -->
<a id="xid-2D14F88A6C01"></a>

# Design Constraint Derivation Catalog

## Derivation Areas

| Design element | Confirm as requirement | Decision class |
|---|---|---|
| collection return | behavior for 0, 1, and N results | requirement |
| nullable field | behavior on `null` path | requirement |
| numeric range | below, at, inside, above boundary behavior | requirement |
| string | empty, max length, overflow, forbidden chars | requirement |
| boolean | both `true` and `false` paths | requirement |
| enum | all values and undefined value behavior | requirement |
| datetime | timezone, date boundary, future, past, precision | requirement |
| PK constraint | duplicate or missing-target behavior by operation | requirement |
| FK constraint | missing reference and delete-chain behavior | requirement |
| UNIQUE constraint | duplicate behavior | requirement |
| NOT NULL constraint | omitted-value behavior | requirement |
| CHECK constraint | violation behavior | requirement |
| DEFAULT value | omitted-value application rule | design |
| version column | optimistic-lock conflict behavior | requirement |
| logical delete | visibility and update behavior for deleted rows | requirement |
| relation and aggregation | zero-related-row behavior and ordering | requirement |
| operation structure | search, register, update, delete, batch behaviors | requirement |
| business pattern such as `status` | transition, rollback, terminal-state behavior | requirement |

## Combination Rules

- Expand matrices when multiple structural axes interact, such as:
  - nullable collection vs zero-result behavior
  - nullable value vs aggregate result
  - status value vs update action
- If the matrix would exceed eight cases, confirm the deciding axes first instead of brute-force listing every case.

## Output Shape

- derivation basis table with `DCD-` ids
- grouped requirement confirmation items
- separate design-time decisions
- explicit combination matrix when structural overlap exists

## Knowledge Relations

- part_of: [Constraint Derivation Framework](110_constraint_derivation_framework.md#xid-81A6C4E2B190)
