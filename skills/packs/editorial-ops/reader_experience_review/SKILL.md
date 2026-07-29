<!-- xid: D84028E6F515 -->
<a id="xid-D84028E6F515"></a>

# Skill: reader_experience_review

## Purpose

Review a draft from the declared reader perspective so confusion, missing
context, and likely drop-off points are visible before release.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Reader capability model](../../../../knowledge/packs/editorial-ops/120_reader_capability_model.md#xid-125B6C5E3630)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- article draft
- intake record
- target reader definition
- reader capability assumption
- optional channel assumptions

## Outputs

- reader-experience review path
- friction points
- capability-mismatch findings
- revision priorities

## Startup

- Confirm the draft and intake record exist.
- Confirm the intended reader, reading context, and assumed prior knowledge.
- Confirm whether the review is for restructuring, tone adjustment, or release gating.

## Execution

1. Walk the article in reader order.
2. Compare each major jump in the article to the assumed reader capability.
3. Note where a reader would likely pause, doubt, or leave.
4. Separate comprehension issues from factual issues.
5. Flag capability mismatches such as:
   - unexplained low-level concept jumps
   - missing component-role clarification
   - abstraction leaps beyond the assumed tolerance
6. Rank the friction points by likely reader impact.
7. Write the review result to the output path and return it.

## Monitoring and Control

- Do not present empathy-based feedback as factual validation.
- Do not default to generic style preference when reader context is unclear.
- Do not infer clarity without stating what the reader already knows.
- Keep missing audience evidence explicit.

## Closure

- Return the review path.
- Return the top friction points.
- Return the author revision handoff.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
