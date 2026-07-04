<!-- xid: 6655C6BD6238 -->
<a id="xid-6655C6BD6238"></a>

# Skill Meta: qa_gate_review

- skill_id: `qa_gate_review`
- summary: execute evidence-based QA with XDDP trace-continuity, domain review, and system-impact checks
- use_when: user asks for QA review against XDDP traceability, design, performance, security, or license expectations, including a focused single-domain review scoped to one quality capability (attribute, performance, security, or license)
- input: target code paths, DB manufacturing artifacts when in scope, design evidence, coding rules, optional performance evidence, optional dependency provenance
- output: XDDP trace-continuity result, per-domain review results, diff-consistency and system-impact result, findings with evidence, uncertainty list
- maturity: `stable`
- execution_mode: `subagent_required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute XDDP trace-continuity, domain QA, and system-impact review
- responsibility: user asks for QA review against design, performance, security, or license expectations
- os_contract: v1
- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit; review that XDDP trace links remain connected; include DB manufacturing results when database, persistence, migration, SQL, data correction, or stored-procedure work is in scope; review the intended difference and graph/structure-backed system-impact candidates, not the whole implementation by default; do not force multi-domain or multi-artifact review through one model context when it risks context overflow — split by domain, target, or evidence family and run subagents with explicit merge rules
- lifecycle:
  - startup: confirm XDDP trace basis, DB manufacturing artifacts when in scope, and domain evidence exist for specification, performance, security, and license review
  - planning: define trace-continuity checks, review domains, delta-bounded targets including DB manufacturing outputs, system-impact candidates, management rows, and subagent split by review domain, artifact family, or target boundary before loading broad evidence
  - execution: run `CAP-QA-001`, `CAP-QA-006`, `CAP-QA-007`, and `CAP-QA-008`, with `CAP-QA-005` when attribute analysis is required, while checking that XDDP Why / What / Where / How, TM rows, intended diff, semantic structure evidence, and graph-backed impact candidates remain connected
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

