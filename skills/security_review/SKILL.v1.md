---
schema_version: 1
skill_id: security_review
xid: 7C4E9A2D1F60
summary: review C# code and evidence for security risks
applies_when:
- user needs focused security validation
exclusions:
- Do not suppress security uncertainty or decide remediation policy without evidence
inputs:
- target code, design evidence
outputs:
- security review result, risk findings, unresolved list
criteria:
- id: evidence_coverage
  statement: Every security judgment cites the inspected code or design evidence.
  verification: Check each finding and conclusion for an evidence path or mark it unknown.
- id: security_viewpoints
  statement: Input handling, secrets, authentication, authorization, data protection, dependency risk, and logging safety are considered when applicable.
  verification: Record each viewpoint as done, unknown, or not_applicable with supporting evidence.
- id: uncertainty
  statement: Missing or insufficient evidence remains explicit as unknown and is included in unresolved items.
  verification: Review the unresolved list and confirm unsupported conclusions were downgraded.
- id: handoff
  statement: Security-scope findings and required follow-up are handed to the next owner with a concrete next action.
  verification: Confirm the report contains a handoff or explicitly records なし when no handoff is needed.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: csharp_quality_review_criteria
  query: C# quality review criteria
  required_when: Required when C# review criteria are needed to interpret the target evidence.
  seed_xids:
  - 8C4D2A7E5101
control_refs: []
aliases:
- 3575A687EBCA
- 1BCE02850126
---
<!-- xid: 7C4E9A2D1F60 -->
<a id="xid-7C4E9A2D1F60"></a>

# Skill: security_review

## Purpose

Review C# code and evidence for security risks. Apply the security review
method selected by runtime routing for the work item; the method is not a
fixed capability declaration in this definition.

## Inputs

- target code
- design evidence

## Outputs

- security review result
- risk list
- unresolved list

## Startup

- Confirm the target and security-relevant evidence exist.
- Record `unknown` when required evidence is missing.

## Planning

- Define security review targets and management rows.
- Identify which security viewpoints are applicable from the target and evidence.

## Execution

- Review input handling, secrets, authentication, authorization, data
  protection, dependency risk, and logging safety.
- Ground every judgment in inspected evidence and preserve the evidence path.
- Resolve the C# quality review criteria Knowledge when required by the review
  scope.

## Monitoring and Control

- Preserve explicit evidence gaps.
- Downgrade unsupported conclusions to `unknown`.

## Closure

- Finalize the review result and preserve unresolved items.
- Hand security-scope findings and follow-up actions to the next owner.

## Rules

- Every judgment must cite evidence.
- Do not suppress security uncertainty.
- Do not treat an unverified security assumption as a finding or as clearance.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

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

### Original Skill-specific declarations

- summary: review C# code and evidence for security risks

- use_when: user needs focused security validation

- input: target code, design evidence

- output: security review result, risk findings, unresolved list

- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit

- lifecycle:
  - startup: confirm target and security-relevant evidence exist
  - planning: define review targets and management rows
  - execution: run `CAP-QA-007`
  - monitoring_and_control: downgrade unsupported conclusions to `unknown`
  - closure: finalize review results and preserve unresolved items

- tags: `qa`, `security`, `csharp`

- knowledge_slots:
  - name=csharp_quality_review_criteria; bind=8C4D2A7E5101
