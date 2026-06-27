# Skill Seed: knowledge_ontology_management

- date: `2026-06-28`
- requested_outcome: use ontology analysis whenever domain knowledge is added
- publication_boundary: public OS Skill under `skills/os/`
- initial_maturity: `trial`

## Boundary

The Skill governs additions and material semantic revisions under `knowledge/`.
It does not run for formatting-only changes, mechanical XID rewrites, or source
file additions that do not create or revise canonical knowledge.

The Skill performs concept identity, duplication, split, replacement, and typed
relationship assessment before canonical publication. It preserves the
repository split by keeping:

- procedure in the Skill
- semantic vocabulary and rules in canonical knowledge
- proposal analysis and judgment history in `work/`
- original evidence in `sources/`

## Initial Trigger Examples

- "Add this regulation as domain knowledge."
- "Convert these source notes into a knowledge fragment."
- "Add a new page under `knowledge/`."
- "Update this knowledge page because the concept boundary changed."

## Excluded Trigger Examples

- Fix a typo in a knowledge page.
- Run `xref fix`.
- Repair only a moved XID link.
- Add a source file without promoting it into canonical knowledge.

## Initial Validation Target

- public routing entries exist
- the Skill passes `fm skill check --level trial`
- XID validation reports no new issues
- controlled ontology relationships are deterministically checkable
