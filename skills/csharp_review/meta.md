<!-- xid: 218463E0F3ED -->
<a id="xid-218463E0F3ED"></a>

# Skill Meta: csharp_review

- skill_id: `csharp_review`
- summary: review C# code with a manual focus on non-Roslyn-detectable risks
- use_when: user asks for C# review beyond Roslyn/compiler diagnostics
- input: target path, optional scope filters, optional output mode
- output: evidence-based findings for attribute misuse, resource efficiency, synchronization, and lifecycle support
- constraints: exclude Roslyn-detectable issues; do not hard-fail unknown attribute values by whitelist
- lifecycle:
  - startup: confirm target path and review scope, then load the review spec
  - planning: define review scope, output mode, category buckets, custom-framework analysis targets, and subagent split when scope-separated parallel review is safe
  - execution: establish Roslyn baseline and execute category-specific checks with local-evidence-first handling for custom frameworks
  - monitoring_and_control: exclude diagnostics-covered issues and downgrade unclear findings to `needs_confirmation`
  - closure: return findings, category summaries, and explicit review conditions
- tags: `csharp`, `review`, `dotnet`, `quality`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../knowledge/csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA`
  - `../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001`
  - `../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002`
  - `../../knowledge/csharp/110_custom_framework_analysis_criteria.md#xid-30E6A4F6F3AB`
