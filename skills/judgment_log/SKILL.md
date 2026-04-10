<!-- xid: 2A9E4C71D5F2 -->
<a id="xid-2A9E4C71D5F2"></a>

# Skill: judgment_log

## Purpose

Write an AI-authored judgment log that records a non-trivial decision, its evidence, its inference boundary, and the next verification step.

Use the canonical schema in `knowledge/organization/121_judgment_log_schema.md#xid-7B4C2D91E621`.

## Required Knowledge (XID)

- [Working area policy](../../docs/014_working_area_policy.md#xid-111D282CA0EA)
- [Shared memory operations](../../docs/015_shared_memory_operations.md#xid-4A423E72D2ED)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)
- [Judgment log schema](../../knowledge/organization/121_judgment_log_schema.md#xid-7B4C2D91E621)

## Optional References

- [Judgment log template](./references/judgment_log_template.md)

## Inputs

- work type or task name
- target
- decision or candidate decision
- evidence paths or evidence summary
- confidence
- optional alternatives
- optional open questions
- optional output path

## Outputs

- judgment log in `work/judgments/` or user-specified path
- normalized evidence and inference boundary

## Startup

- Confirm the target judgment exists.
- Confirm evidence exists or record the judgment as `unknown`.
- Load the judgment log schema.

## Planning

- Separate observed facts from inferred conclusions.
- Classify evidence as:
  - `deterministic`
  - `context_extracted`
  - `inferred`
- Determine whether the decision status is:
  - `proposed`
  - `accepted`
  - `rejected`
  - `unknown`
  - `deferred`

## Execution

- Normalize the evidence into path-specific references when possible.
- Record the decision, decision status, evidence, evidence type, confidence, and context usage.
- Record alternatives when other plausible interpretations exist.
- Record open questions and the next recommended check.
- Write the log by using `references/judgment_log_template.md` or an equivalent structure.

## Monitoring and Control

- Downgrade the decision to `unknown` when evidence is only inferred and no explicit provisional acceptance exists.
- Downgrade weakly supported conclusions to lower confidence.
- Preserve uncertainty instead of compressing it into a confident summary.

## Closure

- Return the written judgment log path.
- Return the final decision status and remaining open questions.

## Rules

- Do not mix session facts and judgment reasoning in the same file.
- Do not hide alternatives that materially change the next step.
- Do not present inferred-only judgments as completed facts.
- Prefer exact evidence paths over broad summary text.

## Failure Handling

- If the target path is not writable, return the normalized content and intended path.
- If evidence is missing, write the record as `unknown` with explicit missing evidence.
