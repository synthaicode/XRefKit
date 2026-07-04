<!-- xid: D37E2B5C8A41 -->
<a id="xid-D37E2B5C8A41"></a>

# Skill Meta: skill_flow_authoring

- skill_id: `skill_flow_authoring`
- summary: create or update repository-native Skill / Flow assets in XRefKit with correct split, publication boundary, runtime envelope, forgetting countermeasures, and validation
- use_when: a user wants to create a new Skill, a new Flow, or both in this repository, especially when the work must be reusable, publicly published under the correct `skills/` family path, aligned with `flows/` as machine-readable workflow control, and forced to carry anti-forgetting structure for later AI reuse
- input: requested target type (`skill`, `flow`, or `both`), proposed id or topic, publication intent (`skills_private/` or explicit public release under `skills/`), intended family path or pack, intended boundary, inputs, outputs, and optional draft notes or source artifacts
- output: created or updated authoring assets such as `skills/os/<skill_id>/meta.md` or `skills/packs/<pack>/<skill_id>/meta.md`, matching `SKILL.md`, optional `references/*`, optional `flows/<flow_id>.yaml`, required routing index updates, and validation results with remaining gaps, where the authored assets include minimum anti-forgetting structure
- maturity: `trial`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: create or update repository-native Skill / Flow assets in XRefKit with correct split, publication boundary, runtime envelope, forgetting countermeasures, and validation
- responsibility: a user wants to create a new Skill, a new Flow, or both in this repository, especially when the work must be reusable, publicly published under the correct `skills/` family path, aligned with `flows/` as machine-readable workflow control, and forced to carry anti-forgetting structure for later AI reuse
- os_contract: v1
- constraints: default new Skill creation to `skills_private/` unless the user explicitly requests public release; do not claim a Flow exists unless a real machine-readable YAML control structure is created under `flows/`; keep behavioral procedure in `skills/` and factual/domain content in `knowledge/`; do not promote beyond the maturity justified by observed evidence; do not treat authoring as complete unless anti-forgetting structure is explicit in the created Skill / Flow; run `xref` and deterministic validation before closure
- lifecycle:
  - startup: confirm whether the request is for a Skill, a Flow, or both; confirm proposed ids and public/private publication intent; load authoring, maturity, operating-contract, and flow-structure rules
  - planning: map the request to the minimum managed file set, decide whether human-readable docs or knowledge fragments are also required, choose the justified initial maturity, and define the anti-forgetting structure that the authored asset must carry
  - execution: scaffold or update the target Skill/Flow assets, register public Skills in routing indexes, force explicit continuity elements such as references, handoff, and observation, and apply required validation commands
  - monitoring_and_control: downgrade unsupported structure claims to explicit gaps, stop if lower-layer input tries to redefine higher-layer control, and keep unresolved publication, maturity, or anti-forgetting gaps explicit
  - closure: return created paths, publication boundary, declared maturity, anti-forgetting elements added, validation results, and the smallest next step for remaining gaps
- tags: `operations`, `authoring`, `skill`, `flow`, `repository`, `xref`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=skill_authoring_with_xref; bind=3DB05A0F5F5B
  - name=skill_operating_contract; bind=B7A2C94F0E61
  - name=skill_maturity_governance; bind=4E7B8D9C1A20
- observation_refs:
  - `../../../observations/2026-05-10_session_skill_flow_authoring_seed.md`
