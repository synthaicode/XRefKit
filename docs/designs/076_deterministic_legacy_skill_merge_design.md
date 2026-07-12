<!-- xid: 8D5C74573895 -->
<a id="xid-8D5C74573895"></a>

# Deterministic Legacy Skill Merge Design

This page defines which parts of legacy Skill merge can be made deterministic
and which parts must remain explicit judgment.

## Problem

Older Skills created on a previous XRefKit version may lack current operating
fields, may include stale references, and may mix procedure, domain knowledge,
and OS/core rules.

Manual merge is possible but costly and error-prone. Fully automatic merge is
unsafe because it can silently discard business behavior or incorrectly treat a
meaning-changing Skill as the same Skill.

The target is a deterministic planner that creates a merge report and applies
only mechanically safe transformations.

## Inputs

The deterministic merge planner takes:

- source Skill folder or import bundle
- current repository root
- optional target Skill id
- optional source version label
- optional mode: `plan`, `apply-safe`, or `report-only`

## Outputs

The planner should emit a structured report with:

- source inventory
- discovered XIDs
- candidate current Skill matches
- reference map
- contract gap list
- ownership and pack-manifest impact
- proposed classification: `adopt`, `merge`, `archive`, `split`, or `escalate`
- safe transformations available
- judgment-required items
- validation commands to run after apply

The report should be saved under `work/` first. Promotion to canonical files is
a separate step.

## Deterministic Stages

| Stage | Deterministic action | Output |
|------|------|------|
| Inventory | Enumerate files, hashes, XIDs, headings, Skill ids, and meta fields. | source manifest |
| Current match | Compare `skill_id`, folder name, XID, title, pack ownership, and referenced capabilities. | ranked candidates |
| Reference audit | Parse Markdown links, path-bearing XID refs, and non-XID local refs. | valid, stale, missing, unmanaged |
| Contract audit | Compare `meta.md` against current required fields by maturity. | missing/invalid fields |
| Ownership audit | Check whether source assets overlap with current pack ownership. | ownership conflicts |
| OS/core leakage audit | Detect copied phrases and references that restate current core contracts. | replacement candidates |
| Knowledge split audit | Detect large factual sections, source lists, criteria, or domain rules inside Skill body. | extraction candidates |
| Safe patch planning | Propose only mechanical updates. | patch plan |

## Safe Automatic Transformations

The following can be applied automatically in `apply-safe` mode:

- add missing XID blocks to new files through `xrefkit xref init`
- rewrite stale XID-bearing paths through `xrefkit xref fix`
- normalize path-bearing XID references
- add missing `trial`-level provisional metadata when the value is mechanical
- update pack `uses_*` references when the target asset is clearly shared and
  already exists
- create a merge report under `work/`

The tool must not automatically:

- change an existing XID
- merge two Skill bodies
- delete old behavior
- promote maturity beyond `trial`
- decide that domain behavior is obsolete
- decide that two similar Skills are the same semantic asset
- move factual content into `knowledge/` without recording the extraction target
  and requiring review when meaning changes

## Classification Rules

The deterministic planner may classify without human judgment only when the
evidence is structural.

| Classification | Deterministic condition |
|------|------|
| `adopt` | No current Skill has the same `skill_id` or XID, required fields can be scaffolded to `trial`, and no ownership conflict exists. |
| `merge` | The source and current Skill share the same `skill_id` or XID and the diff is limited to contract-field additions or reference repair. |
| `archive` | The source has no runnable Skill file or is an exact duplicate of current content by hash. |
| `split` | The Skill body contains detectable sections that match procedure plus knowledge or OS/core rule patterns. |
| `escalate` | Any semantic equivalence, business validity, maturity promotion, or behavior deletion decision is required. |

When multiple classifications match, choose the safest result in this order:

1. `escalate`
2. `split`
3. `merge`
4. `adopt`
5. `archive`

## Candidate Matching Signals

Rank candidate current Skills using:

- exact `skill_id`
- exact XID
- folder name match
- title match
- referenced capability overlap
- referenced knowledge overlap
- pack ownership overlap
- normalized heading similarity

Only exact `skill_id` or exact file-own XID may produce a deterministic
`merge`. XIDs that appear only as outbound references are recorded for audit,
but they do not identify the Skill itself and must not create merge candidates.
Similarity alone produces `escalate`.

## Merge Report Schema

The report should contain:

```yaml
source:
  path: "<import path>"
  source_version: "<optional>"
  files: []
identity:
  source_skill_id: "<id or missing>"
  source_xids: []
  candidate_targets: []
classification:
  proposed: "adopt|merge|archive|split|escalate"
  reasons: []
safe_transformations: []
judgment_required: []
contract_gaps: []
reference_issues: []
ownership_issues: []
validation:
  commands: []
```

## CLI Direction

The initial deterministic command is:

```powershell
python -m xrefkit skill merge-plan --source <path> --json
```

This belongs under `xrefkit skill` because the output is a Skill merge plan, not a
general XID operation.

`xrefkit xref` remains responsible for XID indexing and path repair.

`apply-safe` is intentionally not part of the initial implementation. Safe
application can be added after the report-only planner has enough observed use
to define which transformations are truly mechanical.

## Integration With Runtime Logs

When the planner is used inside a Skill-backed task:

1. start with `xrefkit skill run`
2. attach the merge report as an artifact
3. record non-trivial classification as a `judgment`
4. run validation
5. close only after unknown/risk/judgment gates pass

## Non-Goals

- No automatic semantic merge.
- No automatic quality approval.
- No hidden replacement of OS/core contracts.
- No bulk migration without per-Skill report.

## Related

- [Skill operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Skill maturity governance](../core/contracts/059_skill_maturity_governance.md#xid-4E7B8D9C1A20)
- [Context direction security guard](../core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11)
- [Early XRefKit migration design](072_early_xrefkit_migration_design.md#xid-19BC00401A1A)
