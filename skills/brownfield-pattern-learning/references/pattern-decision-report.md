<!-- xid: 9E4B7C2A6205 -->
<a id="xid-9E4B7C2A6205"></a>

# Pattern decision report

Create a human-reviewable report for an enhancement. Explain why the selected
pattern is appropriate, why alternatives were not selected, and what
complexity and operational burden the decision creates.

## Overview

State the target service and enhancement, conclusion, `follows`/`adapts`/
`introduces`/`unknown` decision, selected pattern, allowed change boundary,
rejected alternatives, complexity and operational impact, data-lifecycle
impact, evidence, open decisions, and approval owner.

## Detailed evidence

Include representative peers, before/after structure and data flow, candidate
comparison, new classes/services/states/configuration/jobs/monitoring/support
steps, deployment/rollback/diagnosis/recovery impact, data lifecycle and
downstream propagation, and XDDP links from `xddp_row_id` to `pattern_id`,
`work_item_id`, `test_id`, `evidence_id`, and `decision_id`.

Unknowns require reason, impact, resolver, and owner.

| Option | Change method | Complexity | Operational burden | Evidence | Decision |
|---|---|---:|---:|---|---|
| A | follow existing pattern | low | low | `PAT-*` | selected |
| B | adapt existing pattern | medium | medium | `PAT-*` | rejected/conditional |
| C | introduce new pattern | high | high | `PAT-*` | rejected/approved |

End with the plain-language decision, protected invariants, permitted change,
remaining risks, human approvals, and next handoff.
