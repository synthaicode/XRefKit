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
- Maintain `observation_refs` when updating an existing Skill:
  - append a run log only when that run changed the understanding of the
    Skill (revealed a gap, refuted an assumption, or produced an accepted
    improvement proposal); routine successful runs are not appended.
  - reference the exact run-log filename including any `_N` suffix, so
    same-day runs stay distinguishable.
  - prune or replace refs that a later observation supersedes.
- Require explicit inputs, outputs, closure, and handoff for authored Skills.
- Require explicit inputs, outputs, handoff, sequence, and control rules for
  authored Flows.
- Update public routing indexes when publishing to `skills/`.
- Run `python -m xrefkit xref init --include skills docs knowledge agent capabilities tools`
  when new managed Markdown files are added.
- Run `python -m xrefkit xref fix --include skills docs knowledge agent capabilities tools`.
- Run `python -m xrefkit skill check --meta ... --level <target>`.
- Run `python -m xrefkit skill list` before committing or publishing skill assets;
  violations must be zero. Suppress a reviewed boundary-convention pointer
  only with an inline `private-ref-ok: <reason>` justification.
- Parse-check changed YAML before closure.
- Keep unresolved gaps explicit instead of filling them by guess.
