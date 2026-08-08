<!-- xid: 9B3D7A1C4E20 -->
<a id="xid-9B3D7A1C4E20"></a>

# Skill Meta: brownfield_workflow

- skill_id: `brownfield_workflow`
- summary: organize brownfield change work across requirements, planning, design, manufacturing, and testing while surfacing unresolved items
- use_when: an existing codebase or system must be changed and upstream work items must be re-organized into phase outputs without guessing missing behavior
- input: request, current-system evidence, upstream phase items, constraints, risks, decisions, and optional existing Knowledge paths or source artifacts
- output: summary-first phase results, traced work items, policies, evidence references, knowledge basis, existing-pattern decisions, knowledge-import results, file-edit integrity records, round-trip verification, concurrency revision checks, specification-alignment decisions, bounded historical conflict investigations, uncommitted-state classifications, scoped same-extension code-rule majority decisions, new-file extension conformity decisions, unknowns, gates, and handoffs
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: brownfield_phase_reorganization
- responsibility: preserve traceability from upstream items through requirements, planning, design, manufacturing, and testing while making reusable Knowledge and local-pattern conformity explicit
- os_contract: v1
- constraints: do not treat existing implementation as complete specification; do not hide unknowns; do not add untraced work; preserve confirmed file encoding, BOM, and newline policy during brownfield text edits; require strict decode/encode and byte round-trip verification; compare the pre-edit revision immediately before writing and abort on concurrent changes; require confirmed specification alignment before writing; investigate unresolved alignment conflicts using bounded history without treating history as authority; preserve and classify uncommitted worktree state before writing; do not discard or hide it without authorization; for new files, extract same-extension code-writing rules by coherent scope, use the local representative majority, and stop on weak or conflicting majorities; inspect required registration before creation; produce work policy in planning; prepare test tools in planning and execute tests in testing; do not approve human-owned decisions
- knowledge_slots:
  - name=service_catalog; bind=7A2F4C8D2201
  - name=service_interaction_data_flow; bind=7A2F4C8D2301
  - name=knowledge_ontology_management; bind=5803607419B9
- lifecycle:
  - startup: confirm the available upstream items, current-system evidence, targets, decision owners, candidate Knowledge/pattern references, and any existing service/catalog/flow artifacts to import
  - planning: define phase scope, item schema, work policy, evidence policy, Knowledge reuse plan, tools, gates, and handoffs
  - execution: import existing service/catalog/flow artifacts when present, re-organize each upstream item for the current phase, apply relevant Knowledge, and classify its result and pattern decision
  - monitoring_and_control: downgrade unsupported claims to `unknown` and stop when proceeding requires a guess
  - closure: produce a summary-first output with decisions, unknowns, impact, owners, evidence, and next-phase handoff
- tags: `brownfield`, `requirements`, `planning`, `design`, `manufacturing`, `testing`, `knowledge-reuse`, `pattern-conformity`
- skill_doc: `./SKILL.md`
