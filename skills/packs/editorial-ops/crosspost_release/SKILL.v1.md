---
schema_version: 1
skill_id: crosspost_release
xid: B7D2A9F4C160
aliases: [A3FD70D101B7, E2E73BDF143A]
summary: prepare a reviewed article for per-channel publication with adaptation notes, release blockers, and human sign-off
applies_when:
  - intake, drafting, and required reviews are complete enough for a release package or crosspost plan
exclusions:
  - release packaging is not publication approval
  - unresolved blockers must not be erased during channel adaptation
inputs: [latest draft, fact-review result, reader-experience review result, target channels]
outputs: [release package path, channel adaptation notes, unresolved blockers, final checklist, human sign-off handoff]
criteria:
  - id: review_evidence
    statement: The release package preserves the latest draft and both review results.
    verification: Check the package against the supplied draft and review outputs.
  - id: channel_boundary
    statement: Channel adaptations preserve core meaning and state channel-specific changes.
    verification: Inspect each channel note for explicit adaptation rationale.
  - id: approval_boundary
    statement: Unresolved blockers and final human publication approval remain explicit.
    verification: Check the final checklist and sign-off handoff.
knowledge_needs:
  - id: editorial_framework
    query: editorial operations framework for release and publication boundaries
    required_when: Required for every crosspost release unless applicability is explicitly recorded.
    seed_xids: [F9E58E2BAD21]
control_refs: []
---
<!-- xid: B7D2A9F4C160 -->
<a id="xid-B7D2A9F4C160"></a>

# Skill: crosspost_release

## Purpose
Prepare a reviewed article for channel-specific release without collapsing review findings, unresolved blockers, and final human sign-off into one step.

## Method
1. Confirm the latest draft, fact review, reader-experience review, target channels, and metadata needs.
2. Resolve the editorial framework Knowledge and preserve its selected XID.
3. Read unresolved items from both reviews.
4. Prepare per-channel adaptation notes without changing core meaning.
5. Build the final checklist with blockers and owner-visible confirmations.
6. Write the release package to `work/editorial_ops/` with a date-prefixed filename unless another path is supplied.

## Monitoring, stop, and handoff
- Do not treat packaging as approval or remove factual blockers because a channel is less strict.
- Stop when unresolved factual blockers are being reclassified as acceptable without owner approval.
- Return the release path, blockers, and final sign-off handoff; publication requires explicit human approval.
