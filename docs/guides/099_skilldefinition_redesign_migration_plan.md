<!-- xid: C8E4B6F20D31 -->
<a id="xid-C8E4B6F20D31"></a>

# SkillDefinition redesign migration plan

This plan moves from a legacy split Skill to a one-document SkillDefinition in
stages. It prioritizes consistency of the new conceptual model over preserving
compatibility, but does not implicitly replace the active source or existing
MCP transport before the cutover.

## Target model

| Concern | Canonical owner |
| --- | --- |
| method, applies_when, I/O, Skill-specific criteria/stop/handoff | one-document SkillDefinition |
| capability, tuning, responsibility, execution_mode | Workflow Protocol's Workflow Runtime Binding; ExecutionBinding transfers these values |
| facts, rules, evidence basis | Knowledge catalog; XID resolution on demand |
| phases, roles, logging, unknown/risk, common escalation, closure | Workflow Protocol |
| package delivery | `xrefkit.skill_packages` plus manifest path |
| upload candidate delivery | existing management transport; staging outside active catalog |
| quality and production adoption | human review and explicit adoption record |

The runtime field meanings and derivation in this table are owned by the
[Workflow Runtime Binding contract](../core/contracts/111_workflow_runtime_binding.md#xid-8D50A972BA9F).
This migration plan records the ownership boundary and compatibility impact;
it does not redefine `capability`, `tuning`, `responsibility`, or
`execution_mode`.

Workflow Protocol continues. Removing duplicated common controls from the Skill
body does not remove the runtime worklist, check separation, unknown/risk,
escalation, closure, or handoff. Workflow Protocol owns common escalation;
SkillDefinition retains only Skill-specific stop, out-of-scope, and specialist
judgment handoff conditions. Workflow, Reporting, Logging, and Context Guard
supplied during initialization are not duplicated in `control_refs`; use an empty
array when there are no additional Skill-specific controls.

## Migration order

1. **Runtime read boundary** — fix the definition path/XID/hash and runtime routing fields from the run log in `ExecutionBinding`, then read the exact document when the subagent starts.
2. **Catalog and Knowledge** — limit the routing list to header-derived metadata and pass the method only after selection. The parent decides the active IDs in `knowledge_needs` and resolves candidate bodies by XID when needed.
3. **Representative complex Flow** — retain the specific method while removing duplicated common controls, then verify parent routing, subagent execution, checks, escalation, and handoff in one run chain.
4. **Distribution** — make the package manifest point to the one-document path and retain the raw hash. Mark legacy YAML packages explicitly as migration targets.
5. **Management adoption** — observe upload, validation, staging, seal/review, adoption, and maturity assessment/proposal/review/apply as separate states. This checkout has an MCP-owned upload and adoption path for the admin profile, so verify the repository implementation's state transitions. Hand off live verification of external identity, secret management, production publication, and long-term operation to the owning service or operating environment.
6. **Docs and bulk conversion** — align canonical docs to the new model and choose conversion units after observing representative runs. Retire the legacy meta validator and split source last.

Here, bulk conversion separates definition migration, which adds tracked v1
alongside legacy, from adoption, which switches the production default source.
The former can proceed one verified conversion unit at a time. Do not perform
the latter or delete legacy until management adoption, human acceptance, and
usage observations are available.

## Current definition migration status

| Skill | tracked v1 | coverage | active-source boundary |
| --- | --- | --- | --- |
| `dotnet_change_analysis` | [9883EF4E8CA9](../../skills/dotnet_change_analysis/SKILL.v1.md#xid-9883EF4E8CA9) | complex analysis method, Knowledge, Skill-specific handoff | explicit `--definition`; legacy kept |
| `code_constraint_derivation` | [7C4E9A1B2D60](../../skills/packs/constraint-derivation/code_constraint_derivation/SKILL.v1.md#xid-7C4E9A1B2D60) | Knowledge selection, unsupported business meaning stop | explicit `--definition`; legacy kept |
| constraint-derivation family | [A4C9E2B7D160](../../skills/packs/constraint-derivation/constraint_derivation_index/SKILL.v1.md#xid-A4C9E2B7D160) | 11/11 Skills, family routing, domain-specific stop conditions | explicit `--definition`; legacy kept |
| `security_review` | [7C4E9A2D1F60](../../skills/security_review/SKILL.v1.md#xid-7C4E9A2D1F60) | evidence, security viewpoints, unknown, handoff | explicit `--definition`; legacy kept |
| `editorial_intake` | [7C4E9A2D6F81](../../skills/packs/editorial-ops/editorial_intake/SKILL.v1.md#xid-7C4E9A2D6F81) | context boundary, reader capability, publication stop | explicit `--definition`; legacy kept |
| editorial-ops family | [C8E1A6D3B270](../../skills/packs/editorial-ops/editorial_ops_index/SKILL.v1.md#xid-C8E1A6D3B270) | 6/6 Skills, evidence review, reader review, human publication authority | explicit `--definition`; legacy kept |
| simple top-level batch | [D4A7C91E2B60](../../skills/requirements_flow/SKILL.v1.md#xid-D4A7C91E2B60) | 8/8 Skills, review/planning/traceability, human decision boundaries | explicit `--definition`; legacy kept |
| artifact and short OS batch | [D5A8C1E6B740](../../skills/import_skill/SKILL.v1.md#xid-D5A8C1E6B740) | 8/8 Skills, artifact verification, judgment and promotion boundaries | explicit `--definition`; legacy kept |
| medium OS batch | [F8A2C6D1B370](../../skills/os/knowledge_ontology_management/SKILL.v1.md#xid-F8A2C6D1B370) | 5/5 Skills, goal continuity, migration, research, canonical publication boundaries | explicit `--definition`; legacy kept |
| implementation and review batch | [D7B4E9A2C610](../../skills/implementation_flow/SKILL.v1.md#xid-D7B4E9A2C610) | 7/7 Skills, bounded implementation/test, language review, QA gate, report composition boundaries | explicit `--definition`; legacy kept |
| design planning and business-intake batch | [6A4F8C2D1E70](../../skills/design_flow/SKILL.v1.md#xid-6A4F8C2D1E70) | 6/6 Skills, planning/design approval, goal-first learning, provisional scoping, evidence-bound conversation analysis | explicit `--definition`; legacy kept |
| final brownfield DB catalog batch | [E1A7C4D9B260](../../skills/brownfield-workflow/SKILL.v1.md#xid-E1A7C4D9B260) | 9/9 Skills, source/DB evidence, safe deterministic regression, catalog publication, Skill/Flow authoring boundaries | explicit `--definition`; legacy kept |

Each tracked v1 has a new own XID and retains the old body XID and old meta XID
in `aliases`. Because there is no external governance record, maturity is
`unassessed` for explicit execution.

## Low-level model work packets

Limit work items passed to low-level models such as Luna to one judgment boundary
and deterministic completion conditions.

- list the XIDs to read, target paths, and files that may be changed;
- state prohibited actions in one sentence, such as writing runtime fields back into SkillDefinition;
- make the output one kind, such as a parser, catalog projection, test, or document section;
- make the exact command and expected result the completion criterion; and
- return transport changes, production adoption, and meaning changes across multiple contracts to the parent.

The parent AI owns requirements, routing, work-item decomposition, integration,
and full verification. The subagent performs its assigned work and does not own
the adoption decision or responsibility for the entire job.

## Gates

Each stage passes through the Workflow Protocol's `verify` and `close`. It must
also meet the following conditions.

- definition XID and raw-bytes SHA-256 match across the parser, catalog, and runtime.
- Unevaluated Knowledge activation is retained as `unresolved` rather than treated as unnecessary.
- Legacy and v1 formats are distinguishable in the catalog and the same active Skill is not routed twice.
- Reader/admin protocol selection, management upload, staging, seal, review, adoption,
  and maturity transport do not regress.
- A candidate before human adoption is not treated as the production active source.
- The docs XID check and related tests pass.

Switching the production default source in bulk requires usage observations for
representative complex Skills, live verification of the management adoption
path, operational observation of an external v1 maturity/promotion record, and
a human decision to switch the active source. Until then, continue adding and
explicitly executing tracked v1 for validation, and do not delete the legacy
path.
