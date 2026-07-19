<!-- xid: 9B3D7A1C4E20 -->
<a id="xid-9B3D7A1C4E20"></a>

# Skill Meta: brownfield_workflow

- skill_id: `brownfield_workflow`
- summary: organize brownfield change work across requirements, planning, design, manufacturing, and testing while surfacing unresolved items
- use_when: an existing codebase or system must be changed and upstream work items must be re-organized into phase outputs without guessing missing behavior
- input: request, current-system evidence, upstream phase items, constraints, risks, and decisions
- output: summary-first phase results, traced work items, policies, evidence references, unknowns, gates, and handoffs
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: brownfield_phase_reorganization
- responsibility: preserve traceability from upstream items through requirements, planning, design, manufacturing, and testing
- os_contract: v1
- constraints: do not treat existing implementation as complete specification; do not hide unknowns; do not add untraced work; produce work policy in planning; prepare test tools in planning and execute tests in testing; do not approve human-owned decisions
- lifecycle:
  - startup: confirm the available upstream items, current-system evidence, targets, and decision owners
  - planning: define phase scope, item schema, work policy, evidence policy, tools, gates, and handoffs
  - execution: re-organize each upstream item for the current phase and classify its result
  - monitoring_and_control: downgrade unsupported claims to `unknown` and stop when proceeding requires a guess
  - closure: produce a summary-first output with decisions, unknowns, impact, owners, evidence, and next-phase handoff
- tags: `brownfield`, `requirements`, `planning`, `design`, `manufacturing`, `testing`
- skill_doc: `./SKILL.md`
