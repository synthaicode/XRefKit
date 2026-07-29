<!-- xid: 77F7D4CB9F99 -->
<a id="xid-77F7D4CB9F99"></a>

# Skill: editorial_intake

## Purpose

Turn a loose article idea into a drafting-ready intake record with explicit
topic, audience, reader capability assumption, evidence basis, and publication
boundary.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Reader capability model](../../../../knowledge/packs/editorial-ops/120_reader_capability_model.md#xid-125B6C5E3630)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- idea, memo, or topic prompt
- optional source links or citations
- target audience hints
- optional reader capability assumption
- target channels

## Outputs

- intake record path
- topic focus
- reader capability assumption
- evidence basis
- open questions

## Startup

- Confirm what the article is trying to say.
- Confirm what evidence already exists and what is still missing.
- Confirm the intended audience, assumed prior knowledge, and channels.

## Execution

1. Write the article goal in one or two sentences.
2. Separate confirmed facts from framing assumptions.
3. Capture the intended audience, likely reader question, and channel set.
4. Select or describe the reader capability assumption:
   - default to `zenn_practitioner_web_ai` for Zenn technical articles unless stronger evidence points elsewhere
   - override it when the article clearly targets learners or specialists
5. List the evidence basis and missing evidence.
6. Define the quality checkpoints that later review must cover.
7. Record which explanations may be safely omitted and which must remain explicit for the assumed reader.
8. Write the intake result to the output path and return it.

## Monitoring and Control

- Keep missing source support explicit as `unknown`.
- Do not let preferred tone substitute for topic scope.
- Do not let a vague audience label replace a reader capability assumption.
- Stop short of release approval.

## Closure

- Return the intake record path.
- Return the top open questions.
- State that the next step is `draft_authoring` when the intake is draft-ready.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
