<!-- xid: 271DA9EDBE1A -->
<a id="xid-271DA9EDBE1A"></a>

# Legacy Skill Merge Guide

This page defines how to merge a Skill created on an older XRefKit version into
the current repository.

Use this guide when the source is already a Skill asset, such as a `SKILL.md`,
`meta.md`, Skill folder, or pack-owned Skill copied from an older checkout,
branch, machine, or exported bundle.

This page is about Skill merge.
For broader Flow / Skill migration from early XRefKit structures, see
[Legacy Flow Skill migration guide](062_legacy_flow_skill_migration_guide.md#xid-E3B7D5A18C62).
For deterministic support design, see
[Deterministic legacy Skill merge design](../designs/076_deterministic_legacy_skill_merge_design.md#xid-8D5C74573895).

## Core Rule

Do not copy an older Skill directly into `skills/` as if it were current-ready.

Treat it as an import candidate until its identity, contract, references, and
runtime envelope have been reconciled with the current repository.

## Intake Location

Place the older Skill under an import or working area first, for example:

- `work/inbox/`
- `work/imports/`
- another explicitly scoped temporary import folder

Do not start by overwriting an existing Skill folder.

## Merge Classification

Classify each old Skill into one of the following outcomes:

| Outcome | Meaning | Action |
|------|------|------|
| `adopt` | The old Skill is a distinct Skill that should exist in the current repo. | Bring it forward under the current contract, normally as `trial` first. |
| `merge` | The old Skill is an older or partial version of an existing Skill. | Merge only the useful delta into the current Skill. |
| `archive` | The old Skill is obsolete, redundant, unsafe, or replaced by current OS/core behavior. | Do not promote it; record the reason. |
| `split` | The old Skill mixes procedure, knowledge, workflow, and OS control. | Split into Skill, Knowledge, Flow, docs, or discard OS redefinitions. |
| `escalate` | The correct outcome depends on business or quality judgment. | Record a concern and ask for human decision. |

## Required Inventory

Before making target edits, inventory:

- `SKILL.md`
- `meta.md`
- referenced `knowledge/`
- referenced `capabilities/`
- referenced `flows/`
- pack manifest entries, if any
- XIDs present in the old Skill files
- non-XID path references
- runtime assumptions embedded in prose
- OS/core rules embedded in the Skill body

## XID Decision Rules

Do not change an existing XID as a mechanical merge step.

Use the following rules:

| Situation | XID handling |
|------|------|
| The old Skill is the same meaning and same asset being moved forward. | Preserve the old XID. |
| The old Skill is an older version of an existing current Skill. | Keep the current Skill's XID; merge useful content as a normal edit. |
| The old Skill is similar but has a meaning-changing scope difference. | Create a new XID and record predecessor/successor relationship when appropriate. |
| The old Skill contains copied OS/core rules. | Do not preserve those rules as Skill-local authority; replace with references to current core docs. |
| The old Skill contains business/domain facts. | Move those facts to `knowledge/` and reference them by XID from the Skill. |

If the decision is not clear, record a `judgment` concern and do not decide by
guessing.

## Current Contract Reconciliation

Every imported Skill must be reconciled against the current Skill operating
contract before promotion.

At minimum, check:

- `skill_id`
- `maturity`
- `execution_mode`
- `guard_policy`
- `os_contract.version`
- runtime roles
- startup assumptions
- work item expectations
- artifact and evidence expectations
- unknown/risk/judgment handling
- closure gate
- handoff behavior
- observation or governance references required by maturity

For the current contract, see
[Skill operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
and [Skill maturity governance](../core/contracts/059_skill_maturity_governance.md#xid-4E7B8D9C1A20).

## Merge Procedure

1. Place the old Skill under `work/inbox/` or `work/imports/`.
2. Inventory all old files and references.
   - For deterministic inventory and first-pass classification, run:

```powershell
python -m fm skill merge-plan --source work/imports/<legacy-skill> --json
```

3. Determine whether a current Skill already corresponds to the old Skill.
4. Classify the outcome as `adopt`, `merge`, `archive`, `split`, or `escalate`.
5. Decide XID handling using the XID decision rules above.
6. Remove or replace copied OS/core rules with references to current core docs.
7. Move factual or domain content into `knowledge/` when it is not procedure.
8. Rebuild `meta.md` to match the current Skill operating contract.
9. Put the target Skill into `trial` unless there is enough current evidence to
   justify a higher maturity.
10. Run XRef repair and validation.
11. Run Skill and pack validation.
12. Record the merge judgment in `work/judgments/`.

## Minimum Validation

Run:

```powershell
python -m fm xref fix
python -m fm skill check --scope all
python -m fm pack lint
python tools/run_quality_gate.py fm
```

When the imported Skill belongs to a pack, also confirm the pack manifest owns or
uses the imported assets correctly.

## Required Merge Record

Every non-trivial merge should produce a judgment record with:

- source location and source version, if known
- target Skill id
- merge classification
- XID decision
- files adopted, merged, split, or archived
- OS/core rules removed or replaced
- knowledge extracted
- unresolved concerns
- validation commands and results

## Deterministic Boundary

The merge process can be partially deterministic:

- file inventory
- XID extraction
- current Skill match candidates
- reference validation
- missing contract fields
- duplicated ownership checks
- stale path checks
- validation command execution

The following remain judgment-bearing:

- whether an old Skill is semantically the same as a current Skill
- whether domain facts are still valid
- whether a business-specific behavior should be preserved
- whether maturity can be promoted beyond `trial`
- whether similar Skills should be merged or kept separate

When a deterministic check cannot decide, it should produce an `escalate`
classification rather than guessing.

The current deterministic command is report-only:

```powershell
python -m fm skill merge-plan --source work/imports/<legacy-skill> --json
```

It inventories the source, extracts XIDs, finds exact current Skill candidates,
audits references, reports contract gaps, and proposes a conservative
classification. It does not apply semantic merges.

## Related

- [Skill authoring with xref](013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Legacy Flow Skill migration guide](062_legacy_flow_skill_migration_guide.md#xid-E3B7D5A18C62)
- [Skill operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Skill maturity governance](../core/contracts/059_skill_maturity_governance.md#xid-4E7B8D9C1A20)
- [Flow Capability Skill Knowledge model](../core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
