<!-- xid: 4B9D2E6F8A10 -->
<a id="xid-4B9D2E6F8A10"></a>

# Pack Manifest: batch-regression

- pack_id: `batch-regression`
- summary: deterministic impact and combination-regression evidence for existing batch systems
- maturity: `trial`
- depends_on:
  - os_contract_version: `1`
- entry: `skills/packs/batch-regression/batch-impact-regression/SKILL.md`
- owns_skills:
  - `skills/packs/batch-regression/batch-impact-regression`
- uses_knowledge:
  - `knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- inputs: source and execution boundary, isolated test DB, combination schema, old/new result artifacts, and explicit business rules
- outputs: impact trace, deterministic comparison report, reduced regression set, full-run procedure, and human decision handoff
