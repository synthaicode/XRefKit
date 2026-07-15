<!-- xid: A0B8B60D3325 -->
<a id="xid-A0B8B60D3325"></a>

# Configuration schema

The JSON template is intentionally declarative. Predicates use `all` or
`any` clauses with `eq`, `neq`, `in`, `not_in`, `exists`, and `missing`.
`forbidden` excludes a candidate; `business_invalid`, `upstream_absent`, and
`uncertain` classify it without pretending to prove the business rule.

Top-level fields:

- `system`: `solution`, `project`, `command`, `test_db`, `old_version`, `new_version`, `timeout_seconds`, `parallelism`, `side_effect_check`
- `combination.elements`: ordered `{name, values}` dimensions
- `combination.constraints`: `{id, kind, when, reason, evidence}`
- `comparison`: `key_fields`, `fields`, `ignore_fields`, `normalize_fields`
- `planned_differences`: `{id, when, fields, relation, evidence}`
- `paths`: `{id, description, csharp, stored_procedures, child_stored_procedures, dynamic_sql, dynamic_sp_name}` for trace links
- `regression_set`: `max_size`, `seed`

Source-table extraction is invoked separately with the source root; it does not
require a comparison result file or a database adapter.

Constraint and expectation predicates are data, not Python or SQL. No example
in this Skill claims an actual business rule; template values are placeholders.
