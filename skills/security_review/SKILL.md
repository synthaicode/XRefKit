<!-- xid: 3575A687EBCA -->
<a id="xid-3575A687EBCA"></a>

# Skill: security_review

## Purpose

Execute `CAP-QA-007` and review C# code and evidence for security risks.

## Required Capability Definitions (XID)


## Required Knowledge (XID)

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Inputs

- target code
- design evidence

## Outputs

- security review result
- risk list
- unresolved list
- execution metrics log

## Startup

- Confirm target and security-relevant evidence exist.
- Record `unknown` if required evidence is missing.

## Planning

- Define security review targets and management rows.

## Execution

- Review input handling, secrets, auth, data protection, dependency risk, and logging safety.

## Monitoring and Control

- Preserve explicit evidence gaps.

## Closure

- Finalize review results and preserve unresolved items.

## Rules

- Every judgment must cite evidence.
- Do not suppress security uncertainty.

## Reporting Contract (共通報告)



- reporting_profile: checklist_verdict

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
