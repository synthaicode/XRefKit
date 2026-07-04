# Repository Layout Zone Base-Sync Worklist

Branch:

- `codex/repository-layout-zones-sync`

Related documents:

- `docs/designs/080_repository_layout_zones_design.md`
- `docs/designs/081_repository_layout_mcp_catalog_design.md`
- `handoff/base_sync/HANDOFF.md`

## Work Items

### XREF-001: Define `ownership.yaml`

Status: done

Create the repository-root zone declaration used by CI, base-sync, fm, and MCP.

Acceptance:

- declares `kernel-code`, `kernel-content`, `shared-packs`, `local-packs`,
  `records`, `derived`, and `delivery`
- identifies owner, catalog eligibility, distribution eligibility, and
  base-sync eligibility per zone
- keeps `packs/local/` local-only and non-distributable

### XREF-002: Add ownership parser/validator in `fm`

Status: done

Add a deterministic parser for `ownership.yaml` and validation checks for path
safety and overlapping zones.

Acceptance:

- fails on paths outside the repository
- reports ambiguous overlaps unless ordered precedence is explicit
- can be reused by base-sync and catalog-related checks

### XREF-003: Make `handoff/base_sync` zone-aware

Status: done

Update `handoff/base_sync/xrefkit_sync_worklist.py` so sync classification uses
the ownership model.

Acceptance:

- excludes `packs/local/` from base-sync work items or reports it separately as
  local-only
- includes shared packs when they are base/shared-pack eligible
- excludes generated/record zones from normal base absorption
- preserves existing XID-keyed `moved_in_base` behavior

### XREF-004: Regenerate base manifest after zone behavior changes

Status: done

Regenerate `handoff/base_sync/base-history-manifest.json` after base-sync
scanning rules are updated.

Acceptance:

- manifest generation uses the same zone universe as local worklist generation
- manifest branch and hash convention remain documented
- sample worklist against a fixture shows no false local-deleted items for
  excluded zones

### XREF-005: Update `HANDOFF.md`

Status: done

Revise the local-side handoff instructions to reference the zone model.

Acceptance:

- names `ownership.yaml` as the path-ownership source
- states that `packs/local/` is local-only and not a base sync item
- keeps the current stop rule for `both_changed` and other human-review kinds
- explains how shared-pack moves are handled by XID and `moved_in_base`

### XREF-006: Add multi-root support to `fm` content indexes

Status: done

Update fm-side Skill, knowledge, flow, and capability discovery to include pack
roots before any content move.

Acceptance:

- root paths include `packs/*/{skills,knowledge,flows,capabilities}`
- local pack roots are handled according to ownership metadata
- existing root behavior remains backward compatible

Progress:

- `flowdoctor` now discovers pack flows, pack capabilities, and pack Skill
  bindings when `ownership.yaml` is present.
- `skill check`, `skill list`, and Skill merge candidate search now discover
  pack Skills.
- `pack lint/list` now discovers top-level `packs/*/pack.md` during the
  transition while preserving legacy `skills/packs/*/pack.md`.
- `xref` default include now includes `packs`.

### XREF-007: Add regression tests

Status: done

Cover the transition behavior before moving real content.

Acceptance:

- base document moved into a pack classifies as `moved_in_base`
- local-only pack content is not a sync item
- generated/record zones are excluded
- XID collision behavior is unchanged

Progress:

- Added ownership parser tests.
- Added base-sync scan tests for local-only pack and excluded generated zones.
- Added fm multi-root discovery tests for pack Skill, flow, capability, pack
  manifest, and XID include defaults.
- Added explicit `moved_in_base` pack-move fixture.

## Verification

Run before closing:

```powershell
python -m fm xref fix
python -m pytest
```

If full tests are too broad for the change, record the narrower command and why
it is sufficient.

Completed:

```powershell
python .\handoff\base_sync\export_base_manifest.py --repo . --branch codex/sync-main-without-mp4-action --out .\handoff\base_sync\base-history-manifest.json
python -m pytest tests/test_ownership.py tests/test_base_sync_ownership.py tests/test_fm_multiroot.py tests/test_flowdoctor.py tests/test_skillmeta.py tests/test_packmeta.py tests/test_xref.py tests/test_cli.py
python -m fm xref fix
```

## Open Items

- Decided: `packs/local/*` appears in local fm catalogs by default when
  `ownership.yaml` marks the local-pack zone as `catalog: true`.
- Decided: generated `skills/_index.md` belongs in this branch. The generated
  compact Skill list is produced by `python -m fm skill index --write`.
