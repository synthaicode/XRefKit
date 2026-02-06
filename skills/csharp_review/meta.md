# Skill Meta: csharp_review

- skill_id: `csharp_review`
- summary: review C# code with a manual focus on non-Roslyn-detectable risks
- use_when: user asks for C# review beyond Roslyn/compiler diagnostics
- input: target path, optional scope filters, optional output mode
- output: evidence-based findings for attribute misuse, resource efficiency, synchronization, and lifecycle support
- constraints: exclude Roslyn-detectable issues; do not hard-fail unknown attribute values by whitelist
- tags: `csharp`, `review`, `dotnet`, `quality`
- skill_doc: `./SKILL.md`
- knowledge_refs: `../../knowledge/csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA`
