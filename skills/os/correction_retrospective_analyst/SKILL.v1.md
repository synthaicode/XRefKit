---
schema_version: 1
skill_id: correction_retrospective_analyst
xid: 4BC7E192A6D0
summary: Analyze a human-authorized bounded correction sequence as work evidence without executing general retrospective promotion.
applies_when:
- A configured host dispatches an isolated analyst for a validated correction_retrospective governance packet with explicit scope-bound human analysis consent.
exclusions:
- Do not execute the separate retro Skill or bypass its draft/adoption refusal.
- Do not adopt or apply rules, publish canonical assets, write personal memory, or create human approval or host signatures.
- Do not infer execution from acknowledgments, silence, correction counts, or a dispatch plan.
inputs:
- A frozen xrefkit.governance_entry/v1 correction_retrospective packet, an opened distinct child run, scoped consent and correction materials with versions, and a designated work output path.
outputs:
- A packet-bound JSON analysis body with evidence-linked cause candidates and explicit unknowns, plus actual child run evidence for the trusted host.
criteria:
- id: bounded_consent
  statement: Actual human evidence establishes analysis intent for the selected interval and only that scope is analyzed.
  verification: Compare consent statement, packet scope, selected correction evidence and output.
- id: causal_evidence
  statement: Findings distinguish changed requirements, applicable existing rules and local versus reusable candidates using contemporaneous evidence.
  verification: Inspect original-correction-revised locators, versions, existing-rule searches and counterexamples.
- id: no_adoption
  statement: Findings remain work evidence and human-review proposals without canonical or personal-memory changes.
  verification: Inspect changed paths, dispositions, signatures and handoff.
knowledge_needs:
- id: work_record_types
  query: factual session judgment and retrospective work record separation
  required_when: Recording correction facts, causal judgments or structural feedback.
  seed_xids:
  - 4F8C21B7D4A2
control_refs:
- 111D282CA0EA
---
<!-- xid: 4BC7E192A6D0 -->
<a id="xid-4BC7E192A6D0"></a>

# Bounded correction retrospective analyst

## Boundary

This is a separate narrow public method permitted by
[the correction retrospective design](../../../docs/designs/114_correction_retrospective_design.md#xid-D4F83A17B9C6).
It is not an alias, clone invocation or promotion of the general `retro` Skill.
Use observable correction evidence and proposal-only outcomes; do not call the
refused general Skill or its shipping route. Runtime binding is derived from
the active instruction. Public source authorization is not maturity promotion or canonical adoption.

## Startup and planning

1. Open a distinct isolated child run through the existing runtime. The host
   owns actual dispatch; validators and plans do not create an analyst.
   Follow the existing operating contract for work items, logging, separate
   quality when required, deterministic verification, concerns and closure.
2. Validate `kind=correction_retrospective`, packet identity and the selected
   interval. Bind `parent_run_id` to `packet.binding.run_id`, `root_run_id` to
   `packet.binding.run_snapshot.fields.root_run_id`, and `work_item_id` to
   `packet.binding.work_item_id`. Mismatched correlation is not this analysis.
3. Read the actual scoped consent evidence in frozen materials. Confirm human
   analysis intent, scope and timing. A caller's `intent=execute_retrospective`
   label alone does not establish consent. Standalone acknowledgment, silence
   or ambiguous reply is not execution or adoption authority. Missing consent
   stops analysis and follows the owning handoff without invented approval.
4. Identify original task basis, initial/changed requirements, correction
   sequence and used versions. Resolve only applicable Knowledge/XIDs on demand.
   Keep missing evidence explicit; do not reconstruct it from model memory.

## Execution

1. Reconstruct original result -> explicit human correction -> revised result
   with message/material locators. Compare initial acceptance conditions with
   later clarifications and changed scope. Do not infer past noncompliance
   from a requirement that was not established at that time.
2. Search relevant existing canonical rules and compare their contemporaneous
   applicability and evidence of actual use. An unsearched area cannot be
   described as having no rule. Missing rule version/use evidence limits the
   conclusion. Do not invent internal model reasoning or user psychology.
3. Retain evidence-backed causes, applicability, counterexamples and competing
   explanations. Distinguish `application_failure`, `requirement_change`,
   `local_condition`, `common_candidate` and `unknown`. These are this entry's
   analytical candidates, not Workflow/gateway/Human Evaluation status enums.
4. Keep unstable, one-off, unsupported and local findings in `stay_in_work`.
   `human_review` identifies a candidate for human judgment, not adoption.
   Mixed causes can have multiple separately evidenced rows. A common
   candidate needs relevant other uses, existing-source comparison and
   counterexamples; insufficient evidence is an unknown or stays in work.
5. Record next owner and needed evidence in reasoning. Human-reviewed adoption,
   if requested separately, enters an eligible authoring/application route and
   shared update check. Never apply findings or sign an authority assertion.

## Output

Save a strict JSON body under the designated work path with exactly
`packet_hash`, `findings`, `unknowns`. It excludes its own output pointer to
avoid a self-hash cycle. The host hashes the saved raw bytes and adds
`output:{path,sha256}` to its returned result. Record the JSON path as a `done`
`output` artifact in this child run. Each finding has exactly:

```json
{
  "classification": "common_candidate",
  "reason": "Evidence-backed sequence, applicability, counterexample and next owner.",
  "evidence": ["<frozen packet material path>"],
  "disposition": "human_review"
}
```

Classification is one of the five values above; disposition is only
`stay_in_work` or `human_review`. Reasons are nonempty and evidence paths belong
to packet materials. Detailed locators, existing XIDs, versions and alternatives
belong in reasons or separately linked judgment records. Unknowns are explicit.
An empty finding list means no supported finding was established, never
agreement or approval. Do not change packet identity or add adoption enums.

## Monitoring, closure and handoff

Keep factual correction/consent events separate from nontrivial judgments and
structural feedback using existing work-record destinations. Stop for changed
packet/material, scope/authority conflict or ambient guard anomalies. Producer
cannot waive concerns or perform the protocol's independent quality acceptance.
Run deterministic verification and closure as required; a blocked child cannot
be falsely attested complete. Return actual child log and saved result to the
host, which alone verifies and signs execution provenance. The analyst never
creates a host receipt or human approval signature.

Suggestion state belongs to the conversational entry, not this analyst. It
suppresses unchanged declined/deferred/unanswered scope and reason; substantive
new evidence or an explicit later human request is handled there. This method
does not monitor chats, repeatedly prompt, schedule analysis or block normal
task closure when optional analysis has not completed. Resume only the selected
interval and distinguish added material from prior analyzed evidence.

Return work artifact, evidence, unknowns and next owner. Live host execution and
analysis quality need actual evidence; parser success and local method
initialization establish neither.
