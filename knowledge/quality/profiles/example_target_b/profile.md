---
schema: xrefkit.target_output_quality_profile/v1
xid: B8E3D0F572C1
profile_id: example_target_b_acceptance
revision: example-1
target:
  id: example_target_b
  revision: example-1
applicability:
  skill_ids: [example_report]
  output_id: acceptance_report
  description: Detailed evidence-first report for fictional Target B readers.
approval:
  status: example
  authority: Fictional illustration only; no real user approval.
  evidence: assets/provenance.txt
exemplars:
  - id: detailed_report
    path: assets/exemplar.txt
    source_locator: Fictional detailed report described in provenance.txt.
input_samples:
  - id: ordinary_input
    path: assets/input.txt
repetitions: 2
knowledge_refs: []
format:
  headings: ["# Verification Record", "## Conditions", "## Observations", "## Assessment", "## Follow-up"]
  tables:
    - section: "## Observations"
      columns: [Case, Input, Expected, Observed, Basis]
  placement:
    - section: "## Conditions"
      required_text: "Environment:"
    - section: "## Assessment"
      required_text: "Assessment:"
    - section: "## Follow-up"
      required_text: "Untested:"
subjective:
  - Explain setup conditions, observed-versus-expected evidence, and the consequence of each untested boundary for the acceptance decision.
---
<!-- xid: B8E3D0F572C1 -->
<a id="xid-B8E3D0F572C1"></a>

# Example Target B Acceptance Quality

This illustrative target requires conditions and observations before the
assessment, a five-column evidence table, and a separate follow-up explanation.
Its granularity criterion differs from compact Target A even though both use
the same hypothetical Skill and output identity.

Attachments are illustrative preserved examples, not evidence that a real owner
accepted this form. The explicit `example` status prevents model qualification
and production correction authority from being inferred from passing structure.

## Knowledge Relations

- narrower_than: [Target Output Quality Profiles](../../130_target_output_quality_profiles.md#xid-D6A9F3B821C4)

## Sources

- source_type: repository_example
- source_path: assets/provenance.txt
- source_locator: fictional Target B detailed report
