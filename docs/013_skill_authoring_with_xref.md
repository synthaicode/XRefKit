<!-- xid: 3DB05A0F5F5B -->
<a id="xid-3DB05A0F5F5B"></a>

# Skill Authoring with Xref

This page defines how to use `xref` when creating or updating a skill.
Goal: keep skill files small, and load only required domain knowledge on demand.

## Scope Split

- Skill files: behavior, procedure, I/O contract, guardrails.
- Domain knowledge files: factual content and source-backed details.
- Connection rule: skills reference domain knowledge by XID.

## Authoring Flow

1. Define the skill task boundary.
2. Find candidate knowledge fragments:

```powershell
python -m fm xref search "<task or domain query>"
```

3. Read only required fragments:

```powershell
python -m fm xref show <XID>
```

4. In the skill, record required references as XID links (not copied text).
5. If knowledge changed, run consistency check:

```powershell
python -m fm xref fix
```

## Skill Reference Format (recommended)

Inside skill files, keep a compact reference section:

```md
## Required Knowledge (XID)
- [Policy A](../knowledge/xxx.md#xid-<XID>)
- [Runbook B](../knowledge/yyy.md#xid-<XID>)
```

Rules:

- Always include `#xid-...` in cross-file links.
- Do not remove or rewrite existing XID blocks manually.
- Use `xref search/show` for retrieval; avoid guessing missing details.

## Update Pattern

- If only skill behavior changed: update skill file, keep references.
- If domain knowledge changed: update knowledge fragment first, then verify skill references still point to valid XIDs.
- If a concept became semantically different: create a new XID and preserve compatibility via `xref deprecate`.

## Related

- [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
- [Workflow](010_workflow.md#xid-7D1E1C0279F1)
- [Startup xref routing policy](011_startup_xref_routing.md#xid-6C0B62D6366A)
