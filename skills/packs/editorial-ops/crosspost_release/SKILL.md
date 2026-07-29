<!-- xid: A3FD70D101B7 -->
<a id="xid-A3FD70D101B7"></a>

# Skill: crosspost_release

## Purpose

Prepare a reviewed article for channel-specific release without collapsing
review findings, unresolved blockers, and final human sign-off into one step.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- latest draft
- fact-review result
- reader-experience review result
- target channels

## Outputs

- release package path
- channel adaptation notes
- unresolved blockers
- final checklist

## Startup

- Confirm the latest draft and both reviews exist.
- Confirm the target channels and any known metadata needs.
- Confirm whether the task is packaging only or includes publish execution.

## Execution

1. Read the unresolved items from both reviews.
2. Prepare per-channel adaptation notes without changing core meaning.
3. Build the final checklist with blockers and owner-visible confirmations.
4. Write the release package to the output path and return it.

## Monitoring and Control

- Do not treat packaging as approval.
- Do not remove factual blockers because a channel is less strict.
- Keep final human sign-off explicit.

## Closure

- Return the release package path.
- Return the unresolved blockers.
- Return the final sign-off handoff.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
