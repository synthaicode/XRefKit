# C# Review Entry

Review C# code for language-dependent defects and system-level implementation
risks beyond compiler or Roslyn diagnostics.

This Skill produces findings, evidence, unknowns, used XIDs, and handoff items.

Do not treat compiler-detectable issues as the primary review value.
Do not infer runtime behavior without source evidence.
Do not silently absorb security, XDDP trace, or design-assumption findings;
record them as handoffs.

## Evidence-driven analogous-path check


After a finding is supported by source or runtime evidence, state its violated
condition and the execution structure that made it possible. Use the active
review criteria to identify role-equivalent paths inside the declared scope;
textual resemblance alone does not establish a common defect.

Record a bounded inventory linking the finding to candidate paths and their
owners or boundaries. Inspect each candidate under its own preconditions and
record whether it is an additional manifestation, an existing finding, a
non-match, not yet verified, or an out-of-scope handoff. Preserve evidence and
negative results; do not count the same finding twice or claim a new root cause
merely because another location fails.

When runtime evidence is needed, choose a representative candidate and a
control that distinguishes the suspected mechanism from ordinary failure.
Record the exact intervention, observable state or outcome, and what the test
does not establish. A successful representative test does not verify every
candidate in the inventory.

Before reporting coverage complete, give each inventoried path an evidence-backed
disposition or explicit unverified boundary and next owner. Keep this check
within the declared scope and existing Skill exclusions; proposed scope
expansion remains a handoff rather than an unbounded search.
