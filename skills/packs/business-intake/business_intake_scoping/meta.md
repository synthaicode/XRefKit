<!-- xid: 4E9B2C18D740 -->
<a id="xid-4E9B2C18D740"></a>

# Skill Meta: business_intake_scoping

- skill_id: `business_intake_scoping`
- summary: discover and scope one business task into a boundary-visible responsibility unit even when the user only knows partial materials or structure
- use_when: a user wants to import business work into this repository, but only knows fragments such as a task name, one owner, one artifact, one trouble point, or a partial handoff and needs the AI to build the first usable scope
- input: one or more seeds such as target business task, current owner, known artifact, repeated trouble point, partial handoff, optional source documents, or optional business rules
- output: discovery-first scoped intake note with known facts, provisional boundary, previous side, current responsibility, next side, the seven first-pass fields, and explicit missing confirmation points
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: discover and scope one business task into a boundary-visible responsibility unit even when the user only knows partial materials or structure
- responsibility: a user wants to import business work into this repository, but only knows fragments such as a task name, one owner, one artifact, one trouble point, or a partial handoff and needs the AI to build the first usable scope
- os_contract: v1
- constraints: do not require a complete business map before helping; do not jump to detailed implementation steps before business and responsibility levels are explicit; do not hide missing business rules; mark unresolved ownership, rule interpretation, or handoff conditions as unresolved; partial scoping is valid when clearly labeled
- lifecycle:
  - startup: confirm the visible seed, such as task name, owner, artifact, or bottleneck, then load scoping rules and template
  - planning: define a candidate business level and current responsibility hypothesis from partial information and identify missing scope information
  - execution: produce a discovery-first scoped intake record with known facts, assumed boundary, previous side, current responsibility, next side, and seven required fields where available
  - monitoring_and_control: downgrade scope claims that are missing boundary visibility; keep ambiguity explicit; preserve provisional fields instead of forcing certainty
  - closure: return the scoped output, open questions, recommended next confirmation points, and the smallest next information needed
- tags: `operations`, `intake`, `scoping`, `business`, `planning`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../../../knowledge/packs/business-intake/110_business_intake_scoping_rules.md#xid-7B3E5D1A6102`
  - `../../../../docs/packs/business-intake/060_business_intake_scoping_guide.md#xid-C91F7D2A6B40`
- observation_refs:
  - `../../../../observations/2026-05-01_session_business_intake_scoping_skill_seed.md`
