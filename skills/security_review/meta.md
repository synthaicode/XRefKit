<!-- xid: 1BCE02850126 -->
<a id="xid-1BCE02850126"></a>

# Skill Meta: security_review

- skill_id: `security_review`
- summary: review C# code and evidence for security risks
- use_when: user needs focused security validation
- input: target code, design evidence
- output: security review result, risk findings, unresolved list
- maturity: `draft`
- execution_mode: `subagent_preferred`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: review C# code and evidence for security risks
- responsibility: user needs focused security validation
- os_contract: v1
- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit
- lifecycle:
  - startup: confirm target and security-relevant evidence exist
  - planning: define review targets and management rows
  - execution: run `CAP-QA-007`
  - monitoring_and_control: downgrade unsupported conclusions to `unknown`
  - closure: finalize review results and preserve unresolved items
- tags: `qa`, `security`, `csharp`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101`
