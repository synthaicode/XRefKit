<!-- xid: 6655C6BD6238 -->
<a id="xid-6655C6BD6238"></a>

# Skill Meta: qa_gate_review

- skill_id: `qa_gate_review`
- summary: execute evidence-based QA across specification, performance, security, and license domains
- use_when: user asks for QA review against design, performance, security, or license expectations, including a focused single-domain review scoped to one quality capability (attribute, performance, or license)
- input: target code paths, design evidence, coding rules, optional performance evidence, optional dependency provenance
- output: per-domain review results, diff-consistency result, findings with evidence, uncertainty list
- maturity: `stable`
- execution_mode: `subagent_required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute evidence-based QA across specification, performance, security, and license domains
- responsibility: user asks for QA review against design, performance, security, or license expectations
- os_contract: v1
- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit; review the intended difference, not the whole implementation by default
- lifecycle:
  - startup: confirm domain evidence exists for specification, performance, security, and license review
  - planning: define review domains, delta-bounded targets, management rows, and subagent split when scope-separated parallel review is safe
  - execution: run `CAP-QA-001`, `CAP-QA-006`, `CAP-QA-007`, and `CAP-QA-008`, with `CAP-QA-005` when attribute analysis is required, while checking delta appropriateness against traced intent, semantic structure evidence, and graph-backed impact candidates when available
  - monitoring_and_control: downgrade unsupported conclusions or unclear delta coverage to `unknown`
  - closure: finalize states, return per-domain findings with evidence, and hand off target-scope cleanup when code review completion is declared
- tags: `qa`, `review`, `quality`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=temporary_traceability_comment_rule; bind=22E4C7AC7063
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=agent_diff_review_gate_design; bind=7A2F4C8D1801
  - name=dotnet_change_analysis_viewpoints; bind=2E7B5A1FD201
  - name=structure_graph_tm_backstop; bind=163AD9936979
- observation_refs:
  - `../../observations/2026-06-18_skill_run_skill_flow_authoring.md`

