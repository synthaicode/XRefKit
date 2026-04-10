<!-- xid: 9D64B2F18E44 -->
<a id="xid-9D64B2F18E44"></a>

# Judgment Log Usage

This page defines how to use the judgment-log mechanism and the `judgment_log` skill.

This page defines the reasoning-log pattern only.
For the role split across record types, see [Work record types](019_work_record_types.md#xid-4F8C21B7D4A2).

## Purpose

Use judgment logs when later reviewers or future sessions need to know not only what happened, but why a non-trivial judgment was made.

## Storage

- location: `work/judgments/`
- filename: `YYYY-MM-DD_judgment_<topic>.md`

## Difference From Session Logs

- `work/sessions/`: factual execution history
- `work/judgments/`: decision, evidence, alternatives, uncertainty, next verification step

## When To Use

Write a judgment log when:

- a scope or impact decision is non-trivial
- the judgment includes inference
- alternatives were compared
- confidence is mixed
- the next step depends on understanding the reasoning path

## Request Template

```text
Use `judgment_log` to record this decision.
Work: `<work>`
Target: `<target>`
Decision: `<decision>`
Evidence: `<evidence>`
Confidence: `<confidence>`
Output path: `<output_path or work/judgments/...>`
```

## Example Requests

### Example 1: .NET impact judgment

```text
Use `judgment_log` to record this decision.
Work: `dotnet_change_analysis`
Target: `order approval flow`
Decision: `approval branching is controlled in application service, not controller`
Evidence: `src/App.Web/Controllers/OrderController.cs`, `src/App.Application/Orders/ApprovalService.cs`
Confidence: `4`
Output path: `work/judgments/2026-04-10_judgment_order-approval-control-point.md`
```

### Example 2: external-definition activation judgment

```text
Use `judgment_log` to record this decision.
Work: `external_definition_change_analysis`
Target: `struts approval transition`
Decision: `the XML transition is active only under legacy approval mode`
Evidence: `struts-config.xml`, `ApprovalModeSelector.java`, related bootstrap config
Confidence: `3`
Output path: `work/judgments/2026-04-10_judgment_struts-approval-transition-activation.md`
```

## Required Content

A judgment log should include:

- decision
- decision status
- evidence
- evidence type
- confidence
- alternatives
- open questions
- next check

## Related

- [Work record types](019_work_record_types.md#xid-4F8C21B7D4A2)
- [Working area policy](014_working_area_policy.md#xid-111D282CA0EA)
- [Shared memory operations](015_shared_memory_operations.md#xid-4A423E72D2ED)
- [Change analysis skill usage](054_change_analysis_skill_usage.md#xid-C5A8F13D7E21)
