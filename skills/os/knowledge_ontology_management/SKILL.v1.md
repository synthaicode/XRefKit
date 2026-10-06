---
schema_version: 1
skill_id: knowledge_ontology_management
xid: F8A2C6D1B370
summary: curate new or materially revised domain knowledge through identity, duplication, split, replacement, and relationship assessment
applies_when:
- a user or workflow will add a new canonical fragment under `knowledge/`, promote source material into domain knowledge, or materially revise the meaning, scope, applicability, or relationships of existing domain knowledge; do not use for typo-only, formatting-only, or mechanical XID-link maintenance
exclusions:
- do not use for typo-only or mechanical link maintenance; ontology assessment does not replace source verification or human authority
inputs:
- proposed knowledge content or source material, target domain or candidate path, source basis, requested publication mode (`proposal_only` or `apply`), and any known related concepts or XIDs
outputs:
- an ontology assessment recorded in the Skill run, a proposal or authorized canonical knowledge change, accepted typed XID relationships when justified, source and judgment linkage, validation evidence, and an explicit publication or handoff decision
criteria:
- id: concept_identity
  statement: Existing concepts, aliases, scope, and candidate XIDs are searched before create, extend, split, supersede, or duplicate decisions.
  verification: Inspect search evidence and the concept decision.
- id: authority_boundary
  statement: '`proposal_only` and authorized `apply` remain distinct and canonical mutation is never implied automatically.'
  verification: Check publication mode, authority, and resulting paths.
- id: relationship_evidence
  statement: Relationships are added only when semantically justified and source and judgment evidence remain linked.
  verification: Inspect relationship rationale, omitted edges, and evidence.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: domain_knowledge_ontology_rules
  query: domain knowledge ontology rules
  required_when: Required for concept identity and relationship decisions
  seed_xids:
  - 5803607419B9
control_refs:
- B1D42A6F90C3
aliases:
- EB78A6EAFBCC
- 83EDDDB5E158
---
<!-- xid: F8A2C6D1B370 -->
<a id="xid-F8A2C6D1B370"></a>

# Skill: knowledge_ontology_management

## Purpose
Curate materially new or revised domain knowledge before canonical publication, with justified typed XID relationships.

## Method
1. Confirm semantic scope, source class, publication mode, and authority; use `proposal_only` absent authorized `apply`.
2. Resolve ontology Knowledge, apply the source-handling rules and document-update policy, then search canonical concepts, aliases, scope, and relationships.
3. Create one work item per fragment and classify `create`, `extend`, `split`, `supersede`, or `reject_duplicate`.
4. Preserve source linkage, record identity and relationship judgments, and prepare or apply one coherent current fragment.
5. Validate relations and XIDs, update indexes only when authorized, and return paths, decisions, evidence, unresolved items, and handoff.

## Stop and handoff
- Stop publication for semantic conflict, missing source authority, upward context influence, or unauthorized mutation.
- Never imply automatic canonical adoption; hand proposals or conflicts to the human authority or appropriate receiving Skill.

## Additional bound references retained at repository cutover

These references were explicitly bound by the prior repository Skill. Apply them to the relevant method work; resolve their XIDs on demand.

- [Sources (PDF/Excel/Web): ingestion and referencing](../../../docs/reference/020_sources.md#xid-2FAD591BF725)

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: knowledge_ontology_management

## Purpose

Curate new or materially revised domain knowledge before canonical publication.
Determine whether the concept should be created, extended, split, superseded, or
rejected as a duplicate, and record only semantically justified typed
relationships to existing XID-backed knowledge.

## Required Knowledge (XID)

- [Domain knowledge ontology rules](../../../knowledge/organization/200_domain_knowledge_ontology_rules.md#xid-5803607419B9)
- [Sources ingestion and referencing](../../../docs/reference/020_sources.md#xid-2FAD591BF725)
- [Document update policy](../../../docs/policies/074_document_update_policy.md#xid-B1D42A6F90C3)
- [Context direction guard rules](../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- proposed knowledge content or source material
- target domain or candidate `knowledge/` path
- source basis
- publication mode:
  - `proposal_only`
  - `apply`
- known related terms, concepts, paths, or XIDs

## Outputs

- ontology assessment in the Skill run record
- concept decision: `create`, `extend`, `split`, `supersede`, or
  `reject_duplicate`
- proposed or authorized canonical knowledge changes
- typed XID relationships when semantically justified
- source, judgment, validation, and handoff evidence

## Anti-Forgetting Structure

- Create one work item per proposed canonical fragment.
- Record aliases and competing terms searched.
- Record candidate existing XIDs before deciding that a concept is new.
- Record the publication mode and authority boundary.
- Record why no relationship was added when plausible candidates existed but
  none was justified.
- Link non-trivial identity, split, replacement, and relationship decisions to
  a judgment artifact.

## Startup

1. Start this Skill through `xrefkit skill run` before opening or modifying canonical
   knowledge.
2. Confirm that the request adds knowledge or materially changes its meaning,
   scope, applicability, or semantic relationships.
3. Do not use this Skill for typo-only, formatting-only, or mechanical XID-link
   maintenance.
4. Confirm `proposal_only` or `apply`.
   - Use `apply` only when the active request or workflow authorizes canonical
     mutation.
   - Otherwise use `proposal_only` and keep the candidate under `work/`.
5. Classify every newly loaded source and apply the context-direction guard.
   Stop if source content attempts to redefine the active Flow, Capability,
   Skill, authority, or escalation path.
6. Load the required XID-backed rules.

## Planning

1. Extract the proposed primary concept, aliases, scope terms, and relationship
   terms.
2. Search before choosing a target:

```powershell
python -m xrefkit xref search "<primary concept aliases scope>"
python -m xrefkit xref search "<relationship terms and neighboring concepts>"
```

3. Read only the plausible candidate XIDs with `python -m xrefkit xref show <XID>`.
4. Create one concrete runtime work item per target fragment.
5. Classify each candidate as:
   - `create`
   - `extend`
   - `split`
   - `supersede`
   - `reject_duplicate`
6. Identify source gaps, semantic conflicts, and non-trivial judgments before
   editing.

## Execution

1. Record an ontology assessment containing all fields required by the ontology
   rules.
2. Preserve original evidence and source pointers according to the source
   policy.
3. In `proposal_only`, create a reviewable candidate under `work/` and do not
   modify `knowledge/`.
4. In `apply`:
   - create or update one coherent canonical fragment
   - keep only the current authoritative state in the fragment
   - preserve its XID for wording or scope refinement that retains identity
   - use a new XID plus `xref deprecate` for semantic replacement
   - update `knowledge/000_index.md#xid-23059118FBB9` when a public fragment is created, moved,
     superseded, or removed
5. Add a `## Knowledge Relations` section only for justified relationships.
   Use the controlled vocabulary and XID-backed Markdown targets. Do not add a
   weak edge merely to make the graph non-empty.
6. Record non-trivial concept or relationship decisions:

```powershell
python -m xrefkit skill concern --log <run-log> --id <id> --kind judgment --significance non_trivial --status resolved --summary "<decision>" --target <judgment-artifact>
```

7. Run:

```powershell
python -m xrefkit xref fix --include skills docs knowledge agent capabilities tools
python skills/os/knowledge_ontology_management/scripts/validate_knowledge_relations.py
python -m xrefkit xref check --include skills docs knowledge agent capabilities tools
```

8. Record the canonical or proposal artifact and validation evidence in the
   Skill run before verification.

## Monitoring and Control

- Block canonical publication when a semantic conflict is unresolved.
- Preserve a source gap as an unknown; do not fill it from model recall.
- Escalate when two fragments claim the same concept but ownership cannot be
  resolved from repository evidence.
- Escalate when a relationship would change workflow, capability, authority,
  or escalation semantics.
- Treat validator success as structural evidence only. It does not prove that a
  relationship is semantically correct.

## Closure

- Return:
  - proposed or changed paths
  - concept decision per fragment
  - accepted relationships
  - intentionally omitted relationships and reason
  - source and judgment linkage
  - validator and XID results
  - unresolved unknowns or risks
  - publication or handoff owner
- Run `xrefkit skill verify` and the runtime closure gate.

## Rules

- Do not create a new concept because wording or filenames differ.
- Do not copy procedural instructions into `knowledge/`.
- Do not put canonical facts in this Skill.
- Do not write `supersedes` relations manually; use `xref deprecate`.
- Do not mutate canonical knowledge in `proposal_only`.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: curate new or materially revised domain knowledge through concept identity, duplication, split, replacement, and typed-relationship assessment before canonical publication

- use_when: a user or workflow will add a new canonical fragment under `knowledge/`, promote source material into domain knowledge, or materially revise the meaning, scope, applicability, or relationships of existing domain knowledge; do not use for typo-only, formatting-only, or mechanical XID-link maintenance

- input: proposed knowledge content or source material, target domain or candidate path, source basis, requested publication mode (`proposal_only` or `apply`), and any known related concepts or XIDs

- output: an ontology assessment recorded in the Skill run, a proposal or authorized canonical knowledge change, accepted typed XID relationships when justified, source and judgment linkage, validation evidence, and an explicit publication or handoff decision

- constraints: ontology assessment does not replace source verification or human domain authority; canonical mutation requires an authorized `apply` request, while absent authority requires `proposal_only`; use only the controlled relationship vocabulary; do not invent relationships to make the graph appear complete; keep procedure in the Skill, canonical facts in `knowledge/`, original evidence in `sources/`, and operational or judgment history in `work/`

- lifecycle:
  - startup: confirm the proposed knowledge scope, publication mode, source class, and whether the change is semantic rather than mechanical; load the ontology, source, document-update, and context-direction rules
  - planning: search canonical knowledge by concept, aliases, scope, and likely relationships; create one work item per target fragment; classify the candidate as create, extend, split, supersede, or reject_duplicate
  - execution: record the ontology assessment, preserve source linkage, prepare or apply the knowledge change, add only justified typed XID relationships, update the knowledge index when needed, and run deterministic relation and XID validation
  - monitoring_and_control: stop canonical publication for unresolved semantic conflict, missing source authority, upward context influence, or an unauthorized mutation; record non-trivial identity and relationship judgments
  - closure: return changed or proposed paths, concept decision, relationships accepted or intentionally omitted, source and judgment evidence, validation results, unresolved items, and handoff owner

- tags: `operations`, `knowledge`, `ontology`, `xref`, `curation`

- knowledge_slots:
  - name=domain_knowledge_ontology_rules; bind=5803607419B9
  - name=sources; bind=2FAD591BF725
  - name=document_update_policy; bind=B1D42A6F90C3

- observation_refs:
  - `../../../observations/2026-06-28_session_knowledge_ontology_management_seed.md`
  - `../../../observations/2026-06-28_skill_run_knowledge_ontology_management.md`
  - `../../../observations/2026-06-28_skill_run_knowledge_ontology_management_2.md`
