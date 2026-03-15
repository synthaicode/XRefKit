<!-- xid: 09B250B1A8FB -->
<a id="xid-09B250B1A8FB"></a>

# Skill: qa_gate_review

## Purpose

Execute `CAP-QA-001` and produce an evidence-based review result.

## Required Capability Definitions (XID)

- [CAP-QA-001 Code Review](../../capabilities/quality/100_cap_qa_001_code_review.md#xid-7E9CCEBEDA2D)

## Inputs

- implemented code or diff
- design evidence
- coding rules

## Outputs

- pass or fail judgment
- finding list with evidence
- uncertainty list

## Startup

- Confirm implemented code exists.
- Confirm design evidence exists.
- Confirm coding rules are available.
- Record `unknown` if required evidence is missing.

## Planning

- Define the review scope and target files.
- Prepare management rows for review targets, findings, and unresolved evidence gaps.

## Execution

- Execute `CAP-QA-001` to compare implementation against design evidence and coding rules.
- Produce findings with concrete evidence.

## Monitoring and Control

- Check that each review target has a recorded result.
- Downgrade unsupported conclusions to `unknown`.
- Preserve explicit evidence gaps.

## Closure

- Confirm all review rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Return the judgment and supporting findings.
- Hand off unresolved review items when further investigation is required.

## Rules

- Every judgment must cite evidence.
- Do not treat unsupported assumptions as facts.
- Do not decide design or implementation policy.

