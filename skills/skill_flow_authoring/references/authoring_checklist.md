<!-- xid: 6E8A134DCEE5 -->
<a id="xid-6E8A134DCEE5"></a>

# Authoring Checklist

- Confirm whether the request is `skill`, `flow`, or `both`.
- Confirm whether the Skill is private or explicitly public.
- Confirm proposed id stability before creating files.
- Keep procedure in `skills/` or `skills_private/`.
- Keep domain facts in `knowledge/`.
- Create `flows/*.yaml` only for real machine-readable workflow control.
- Identify what would otherwise be forgotten and encode it structurally.
- Add the context-direction guard unless the Skill is explicitly closed-world.
- Choose the lowest justified maturity.
- Add `observation_refs` before calling a Skill `trial`.
- Require explicit inputs, outputs, closure, and handoff for authored Skills.
- Require explicit inputs, outputs, handoff, sequence, and control rules for
  authored Flows.
- Update public routing indexes when publishing to `skills/`.
- Run `python -m fm xref init --include skills docs knowledge agent` when new
  managed Markdown files are added.
- Run `python -m fm xref fix --include skills docs knowledge agent`.
- Run `python -m fm skill check --meta ... --level <target>`.
- Parse-check changed YAML before closure.
- Keep unresolved gaps explicit instead of filling them by guess.
