# Work Log: csharp_review skill creation

## Request

Create a reusable skill for C# review with these constraints:

- exclude Roslyn-detectable findings
- include attribute value misuse checks
- include resource efficiency checks
- include synchronization checks
- include support lifecycle checks

## Decisions

- Created skill id `csharp_review` to match existing repository naming style.
- Implemented attribute checks as rule-based precondition validation (not value whitelist).
- Separated canonical review criteria into `knowledge/csharp/100_csharp_review_spec.md`.
- Linked skill to knowledge fragment by XID.

## Files Changed

- `skills/csharp_review/SKILL.md` (new)
- `skills/csharp_review/meta.md` (new)
- `knowledge/csharp/100_csharp_review_spec.md` (new)
- `knowledge/000_index.md` (updated)
- `skills/_index.md` (updated)
- `skills/index/by_task.md` (updated)
- `skills/index/by_domain.md` (updated)
- `skills/index/by_tool.md` (updated)

## Validation

- Ran `python -m fm xref fix`
- Result: `issues: 0`, `missing_xid: 0`
