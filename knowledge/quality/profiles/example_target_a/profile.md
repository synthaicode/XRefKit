---
schema: xrefkit.target_output_quality_profile/v1
xid: A7D2C9E461B0
profile_id: example_target_a_acceptance
revision: example-1
target:
  id: example_target_a
  revision: example-1
applicability:
  skill_ids: [example_report]
  output_id: acceptance_report
  description: Compact acceptance report for fictional Target A readers.
approval:
  status: example
  authority: Fictional illustration only; no real user approval.
  evidence: assets/provenance.txt
exemplars:
  - id: compact_report
    path: assets/exemplar.txt
    source_locator: Fictional compact report described in provenance.txt.
input_samples:
  - id: ordinary_input
    path: assets/input.txt
repetitions: 2
knowledge_refs: []
format:
  headings: ["# Acceptance Report", "## Decision", "## Results", "## Unknowns"]
  tables:
    - section: "## Results"
      columns: [Item, Outcome, Evidence]
  placement:
    - section: "## Decision"
      required_text: "Verdict:"
    - section: "## Unknowns"
      required_text: "Scope:"
subjective:
  - Give one concise reason for the verdict and enough evidence to distinguish checked from unchecked behavior.
---
<!-- xid: A7D2C9E461B0 -->
<a id="xid-A7D2C9E461B0"></a>

# Example Target A Acceptance Quality

This illustrative target values a compact report with decision first, one
results table, and explicit untested scope. The profile owns that target's
format and reporting-granularity criteria; `example_report` owns only the
reusable generation method.

The exemplar and ordinary input are portable attachments beside this Knowledge.
They demonstrate acceptance-time preservation but were authored as fictional
fixtures. `approval.status: example` prevents treating them as real acceptance,
model qualification, or production corrective authority.

## Knowledge Relations

- narrower_than: [Target Output Quality Profiles](../../130_target_output_quality_profiles.md#xid-D6A9F3B821C4)

## Sources

- source_type: repository_example
- source_path: assets/provenance.txt
- source_locator: fictional Target A compact report
