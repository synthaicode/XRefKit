<!-- xid: D6A9F3B821C4 -->
<a id="xid-D6A9F3B821C4"></a>

# Target Output Quality Profiles

## Concept and scope

A target output quality profile is versioned Knowledge describing what counts
as an acceptable output for one identified target and output kind. It owns the
target's format, information placement, reporting granularity, accepted exemplar
references and provenance, and representative input samples. The same reusable
Skill can apply different profiles to different targets without acquiring a
separate copy of their quality criteria.

This concept does not replace domain content criteria such as
[Test design criteria](110_test_design_criteria.md#xid-8C4D2A7E5102), nor general
[Quality feedback return rules](../organization/190_quality_feedback_return_rules.md#xid-7A2F4C8D1901).
Profiles describe target-specific acceptance meaning. Shared workflow authority,
generation/review procedures, and corrective authorization are not Knowledge
profile fields; their procedure remains under the
[Fixed Output Quality Protocol](../../docs/core/contracts/112_fixed_output_quality_protocol.md#xid-F9C2A8D471B0).

## Profile data meaning

The portable representation is an XID-bearing Knowledge Markdown document with
YAML front matter using `schema: xrefkit.target_output_quality_profile/v1`.

| Field | Meaning |
| --- | --- |
| `xid`, `profile_id`, `revision` | Stable Knowledge identity, named profile identity, and explicit assessed revision. |
| `target.id`, `target.revision` | Exact target identity and applicability version, independent of Skill identity. |
| `applicability.skill_ids`, `output_id`, `description` | Methods/output kind for which the target criteria apply and a human-readable scope explanation. |
| `approval.status`, `authority`, `evidence` | `approved`, `proposed`, or `example`, the recorded source authority, and a portable evidence attachment. An example is never evidence of real acceptance. |
| `exemplars` | Preserved output artifacts with stable local IDs, attachment paths, and source locators linking them to the acceptance/provenance record. |
| `input_samples` | Representative input attachments with stable local IDs. |
| `format` | Target-owned fixed heading sequence, table column/order, and information placement markers. |
| `subjective` | Target-owned reporting-granularity/readability criteria that remain independently reviewed. |
| `repetitions` | Approved sampling condition for optional model qualification; no universal count is imposed. |
| `knowledge_refs` | Additional applicable quality Knowledge XIDs and packaged resolved copies; their bytes remain part of this profile's assessment identity. |

All machine-read attachment paths are relative to the profile directory and
contained in that package. Approval evidence, exemplars, and inputs travel with
the profile. Original absolute filesystem locations are not profile identity.
Profile identity includes declared target/revision, Knowledge XID/revision,
metadata, document bytes, and attachment hashes. Identical packaged bytes retain
the same identity after relocation; changed applicability, criteria, source
provenance, exemplars, samples, or referenced Knowledge invalidate it.

## Applicability and approval meaning

An applicable profile matches the identified target, Skill, and output kind;
target revision can disambiguate a versioned target. A supplied XID identifies
a profile, not permission to apply it to another target. Multiple applicable
profiles are ambiguous until an explicit applicable XID/revision is selected.
Missing or mismatching Knowledge is not resolved by using the most recently
selected profile or the Skill's default folder.

`approved` is a recorded acceptance claim requiring actual authority/evidence;
parsing a file cannot prove that claim. `proposed` and `example` remain nonaccepted
even when all mechanical format checks pass. A structural example can illustrate
expected formatting without granting qualification or corrective edit authority.

## Examples

The illustrative profiles for
[Target A](profiles/example_target_a/profile.md#xid-A7D2C9E461B0) and
[Target B](profiles/example_target_b/profile.md#xid-B8E3D0F572C1)
apply to the same hypothetical `example_report` Skill and `acceptance_report`
output, but require different report formats and granularity. Both are marked
`example`; neither is a real user's accepted report or a production profile.

## Sources

- source_type: repository_design
- source_path: ../../docs/core/contracts/112_fixed_output_quality_protocol.md
- source_locator: target-specific Knowledge ownership authorized by the user in this task
- source_type: repository_example
- source_path: profiles/example_target_a/assets/provenance.txt
- source_locator: fictional sample provenance, not real acceptance
