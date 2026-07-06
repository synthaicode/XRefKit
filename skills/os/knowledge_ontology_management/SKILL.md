<!-- xid: EB78A6EAFBCC -->
<a id="xid-EB78A6EAFBCC"></a>

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

1. Start this Skill through `fm skill run` before opening or modifying canonical
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
python -m fm xref search "<primary concept aliases scope>"
python -m fm xref search "<relationship terms and neighboring concepts>"
```

3. Read only the plausible candidate XIDs with `python -m fm xref show <XID>`.
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
python -m fm skill concern --log <run-log> --id <id> --kind judgment --significance non_trivial --status resolved --summary "<decision>" --target <judgment-artifact>
```

7. Run:

```powershell
python -m fm xref fix --include skills docs knowledge agent capabilities
python skills/os/knowledge_ontology_management/scripts/validate_knowledge_relations.py
python -m fm xref check --include skills docs knowledge agent capabilities
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
- Run `fm skill verify` and the runtime closure gate.

## Rules

- Do not create a new concept because wording or filenames differ.
- Do not copy procedural instructions into `knowledge/`.
- Do not put canonical facts in this Skill.
- Do not write `supersedes` relations manually; use `xref deprecate`.
- Do not mutate canonical knowledge in `proposal_only`.
