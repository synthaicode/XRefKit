<!-- xid: D93FA1068B27 -->
<a id="xid-D93FA1068B27"></a>

# Ontology assessment evidence sidecar

`validate_ontology_assessment.py` reads UTF-8 JSON evidence of the assessment
required by ontology contract XID `5803607419B9`. This is an authoring check,
not a report template, semantic inference engine, or publication authorization.
It never writes, merges, or removes Knowledge. Existing relationship validation
continues to check the resulting canonical Markdown separately.

Required fields map to the contract's assessment record:

- `target_knowledge_path`: repository-relative Markdown path under `knowledge/`.
- `proposed_primary_concept`: the concept proposed for that fragment.
- `aliases_or_competing_terms_searched`: nonempty list of actual search terms.
- `candidate_existing_xids`: resolved repository XIDs; explicit empty
  list when no existing candidate was found.
- `concept_decision`: `create`, `extend`, `split`, `supersede`, or `reject_duplicate`.
- `source_basis`: the source evidence pointer.
- `accepted_relationships`: explicit list of objects with `type`, `target_xid`,
  and evidence-backed `rationale`; only the contract's relation types are valid.
- `no_relation_reason`: required when accepted relations are empty.
- `rejected_relationship_candidates`: explicit list, with `reason` on each
  recorded non-obvious rejection.
- `unresolved_semantic_conflicts`: explicit list of conflict descriptions.
- `publication_or_handoff_decision`: the recorded authority or next-owner decision.

`concept_comparison` records the author's review, with `classification` as
`new_concept`, `synonym`, `specialization`, or `different_conditions`, plus
`rationale`, `applicability`, `version`, `constraints`, and `source_authority`.
These labels help review a proposed decision; they do not replace the contract's
concept-decision vocabulary or prove semantic identity. Record supported absence
or unknown explicitly instead of inventing a version or condition.

Optional `runtime_load_dependencies` is a separate list of operational load
references. It never creates a semantic edge. The same XID may legitimately
occur in both lists only when an independent semantic rationale exists.

Without `--for-publication`, conflicts can be recorded in a structurally valid
proposal. With that flag, unresolved conflicts reject publication readiness.
The JSON result always states `semantic_acceptance: not_verified`. Passing
does not certify source evidence, semantic correctness, or human approval;
source gaps and disputed judgments remain subject to the existing contract.
