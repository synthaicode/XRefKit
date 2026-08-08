<!-- xid: 9E4B7C2A6201 -->
<a id="xid-9E4B7C2A6201"></a>

# Skill Meta: brownfield_pattern_learning

- skill_id: `brownfield_pattern_learning`
- summary: learn existing implementation and operational patterns before a brownfield change and prepare a complexity- and operability-aware pattern decision
- use_when: a brownfield change may introduce a new design pattern, depart from a local convention, or increase operational complexity
- input: bounded change request, target service and source scope, current implementation and test evidence, service/data-flow Knowledge, operational constraints, and decision owners
- output: pattern inventory, representative examples, pattern evidence, operational baseline, complexity delta, follows/adapts/introduces/unknown decision basis, deviation options, risks, owner, and handoff
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: brownfield_pattern_and_operability_learning
- responsibility: make existing patterns and operational limits explicit before selecting or introducing a design approach
- os_contract: v1
- constraints: do not treat one example as a repository rule; do not infer business truth from code; do not approve a new pattern or release; do not optimize abstract elegance over the demonstrated operational baseline; record weak/conflicting pattern evidence as unknown
- lifecycle:
  - startup: confirm target scope, change difference, current evidence, operational owner, and Knowledge candidates
  - planning: identify representative peers, extract patterns, compare complexity and operation, and prepare decision options
  - monitoring_and_control: stop on weak majority, stale evidence, conflicting conventions, or unowned operational impact
  - closure: hand off pattern basis, deviation rationale, complexity/operability risks, and decision owner
- tags: `brownfield`, `pattern`, `operability`, `complexity`, `architecture`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=common_source_analysis_criteria; bind=5F21C8A41001
  - name=custom_framework_common_criteria; bind=5F21C8A41002
  - name=service_catalog; bind=7A2F4C8D2201
  - name=service_interaction_data_flow; bind=7A2F4C8D2301
  - name=ipa_release_activity_catalog; bind=7B3E5D1A6101
