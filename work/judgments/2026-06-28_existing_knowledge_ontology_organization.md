# Judgment: Existing Knowledge Ontology Organization

- date: `2026-06-28`
- skill_id: `knowledge_ontology_management`
- publication_mode: `apply`
- target: `knowledge/`

## Corpus Assessment

- canonical fragments assessed: `51`
- fragments previously present in `knowledge/000_index.md`: `31`
- fragments previously missing from the index: `20`
- exact duplicate primary titles: `0`
- fragments with explicit typed relations before this run: `1`

## Concept Decisions

- `knowledge/000_index.md`: `extend`
  - reorganize the flat partial list into complete domain and pack groups
  - add all 20 previously omitted canonical fragments
- existing canonical fragments: retain identity and XID
  - no evidence justified `split`, `supersede`, or `reject_duplicate`

## Relationship Decisions

- ten constraint-derivation catalogs/signals are `part_of` the Constraint
  Derivation Framework because the framework routing table and pack structure
  explicitly define them as constituents
- Reader Capability Model is `part_of` Editorial Operations Framework because
  the framework requires reader-capability assumptions in its review operation
- XDDP Supporting Methods `depends_on` XDDP Basics because the page defines
  USDM and PFD specifically as supporting foundations for XDDP

No relationship was added solely from directory proximity. Business-intake and
source-analysis pages were left without new typed edges where a stronger
semantic relationship was not established by the inspected canonical text.

## Protected Existing Edits

The run did not modify the bodies of these pre-existing dirty files:

- `knowledge/csharp/100_csharp_review_spec.md`
- `knowledge/source_analysis/100_common_source_analysis_criteria.md`

They remain indexed but outside this run's content-edit scope.

## Validation Decision

Extend the deterministic validator to require complete public index coverage
and reject exact duplicate primary titles. This preserves the organization
achieved by this run without pretending to validate semantic correctness.
