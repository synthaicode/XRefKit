<!-- xid: F9E58E2BAD21 -->
<a id="xid-F9E58E2BAD21"></a>

# Editorial Operations Framework

## Purpose

This pack exists to turn ad-hoc article prompting into a reusable editorial
operation with explicit routing, review boundaries, and release handoff.

The pack does not treat one agent role name as enough control.
It separates intake, drafting, factual review, reader-perspective review, and
release preparation so unresolved issues remain visible.
Reader-perspective review must include an explicit reader capability assumption,
not only a broad audience label.

## Operating Flow

```text
idea, notes, source links, publication intent
  -> editorial_ops_index
  -> editorial_intake
  -> draft_authoring
  -> fact_review
  -> reader_experience_review
  -> crosspost_release
  -> human final publish decision
```

## Routing Table

| Skill | Target responsibility | Prefix |
|---|---|---|
| `editorial_ops_index` | route editorial requests to the correct pack Skills | `EOR-` |
| `editorial_intake` | scope topic, audience, evidence basis, and release boundary | `EOI-` |
| `draft_authoring` | produce a draft from approved framing and source set | `EDA-` |
| `fact_review` | check claims, numbers, names, URLs, and evidence separation | `EFR-` |
| `reader_experience_review` | surface confusion, drop-off points, and missing context | `ERR-` |
| `crosspost_release` | prepare per-channel release package and unresolved list | `ECR-` |

## Shared Principles

1. Do not let article structure, factual checking, and release decisions collapse into one step.
2. Keep facts, interpretations, and open questions separate.
3. A review output is not final publication approval.
4. Unverified claims stay explicit as `unknown`.
5. Channel-specific adaptation must not silently rewrite source meaning.
6. Reader experience review must state what prior knowledge is assumed before judging omission or clarity.

## Pack Boundary

- This pack governs reusable editorial operation procedure.
- Platform-specific factual rules belong in `knowledge/` when they become durable.
- Human sign-off remains outside the pack.
