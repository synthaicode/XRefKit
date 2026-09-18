---
{
  "schema_version": 1,
  "skill_id": "security_review",
  "xid": "7C4E9A2D1F60",
  "aliases": [
    "3575A687EBCA",
    "1BCE02850126"
  ],
  "summary": "review C# code and evidence for security risks",
  "applies_when": [
    "user needs focused security validation of C# code, design evidence, or an identified security boundary"
  ],
  "exclusions": [
    "Defect-level language and implementation review belongs to csharp_review",
    "Do not suppress security uncertainty or decide remediation policy without evidence"
  ],
  "inputs": [
    "target code",
    "design evidence"
  ],
  "outputs": [
    "security review result",
    "risk findings",
    "unresolved list"
  ],
  "criteria": [
    {
      "id": "evidence_coverage",
      "statement": "Every security judgment cites the inspected code or design evidence.",
      "verification": "Check each finding and conclusion for an evidence path or mark it unknown."
    },
    {
      "id": "security_viewpoints",
      "statement": "Input handling, secrets, authentication, authorization, data protection, dependency risk, and logging safety are considered when applicable.",
      "verification": "Record each viewpoint as done, unknown, or not_applicable with supporting evidence."
    },
    {
      "id": "uncertainty",
      "statement": "Missing or insufficient evidence remains explicit as unknown and is included in unresolved items.",
      "verification": "Review the unresolved list and confirm unsupported conclusions were downgraded."
    },
    {
      "id": "handoff",
      "statement": "Security-scope findings and required follow-up are handed to the next owner with a concrete next action.",
      "verification": "Confirm the report contains a handoff or explicitly records なし when no handoff is needed."
    }
  ],
  "knowledge_needs": [
    {
      "id": "csharp_quality_review_criteria",
      "query": "C# quality review criteria",
      "required_when": "Required when C# review criteria are needed to interpret the target evidence.",
      "seed_xids": [
        "8C4D2A7E5101"
      ]
    }
  ],
  "control_refs": []
}
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
- Do not silently expand a focused security review into defect-level review;
  hand such findings to `csharp_review`.

## Closure

- Finalize the review result and preserve unresolved items.
- Hand security-scope findings and follow-up actions to the next owner.

## Rules

- Every judgment must cite evidence.
- Do not suppress security uncertainty.
- Do not treat an unverified security assumption as a finding or as clearance.
