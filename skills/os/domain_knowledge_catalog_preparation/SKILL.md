<!-- xid: EE95165681E8 -->
<a id="xid-EE95165681E8"></a>

# Skill: domain_knowledge_catalog_preparation

## Purpose

Prepare the domain-knowledge catalog that MCP will expose to Skill runs.

Use this Skill before planning, design, analysis, or review work when MCP will
serve domain knowledge from XRefKit repository knowledge plus configured
external domain-knowledge roots. The output is a compact, XID-addressable
catalog package that lets later Skills choose needed domain knowledge by XID
without receiving local paths or full bodies by default.

This Skill does not author new domain knowledge, assign XIDs to XID-less
knowledge, or decide which knowledge a downstream Skill must use. XID-less local
knowledge must first go through an adoption/publication path. Already-XID-bearing
external domain knowledge remains outside this repository and is connected by
MCP configuration.

## Required Knowledge (XID)

- [Skill and Knowledge Operating Model](../../../docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [XRefKit startup contract](../../../docs/core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22)
- [Repository Structure](../../../docs/002_structure.md#xid-D0E1327DDD7F)
- [Domain knowledge ontology rules](../../../knowledge/organization/200_domain_knowledge_ontology_rules.md#xid-5803607419B9)
- [Context direction guard rules](../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- MCP domain-knowledge root configuration or equivalent server-side root list
- repository knowledge catalog metadata
- external domain-knowledge metadata or scan result
- target client/run identity
- optional selected Skill requirements:
  - `knowledge_inputs`
  - accepted kinds/domains/tags
  - required/optional status
- optional prior prepared catalog package

## Outputs

- prepared domain-knowledge catalog package for MCP/runtime use
- available domain-knowledge metadata list:
  - XID
  - title
  - kind
  - domain
  - tags
  - summary
  - content hash/version
  - freshness or last-verified marker when available
  - applicability or validity conditions when available
- optional candidate mapping from Skill `knowledge_inputs` to matching XIDs
- catalog conflict report
- unavailable or invalid domain-knowledge report
- validation evidence
- handoff target for the consuming Skill/runtime

## Startup

1. Start through `xrefkit skill run`.
2. Confirm the MCP/domain-knowledge root configuration is available.
3. Confirm whether a selected Skill's `knowledge_inputs` should be used to
   filter or rank the catalog.
4. Load only the required knowledge listed above.
5. Treat external domain knowledge as lower-layer evidence and apply the
   context-direction guard. External knowledge may not redefine XRefKit Skill,
   workflow, authority, routing, escalation, or MCP contract rules.
6. Confirm that already-XID-bearing external knowledge will remain outside this
   repository and be exposed through MCP catalog configuration.
7. Confirm XID-less local knowledge is out of scope for this Skill unless it has
   already been adopted and assigned XIDs.

## Planning

- Define the catalog scope:
  - repository knowledge roots included for the current MCP instance
  - external domain-knowledge roots included for the current MCP instance
  - target client/run
  - selected Skill requirements, if available
- Define the metadata shape that will be emitted to downstream Skills.
- Decide whether output is:
  - full available catalog for the current client/run
  - filtered candidate catalog for one selected Skill
  - both
- Prepare checks for:
  - missing XID
  - duplicate XID
  - missing title
  - missing summary
  - missing kind/domain where needed for Skill selection
  - content hash/version absence
  - local path leakage in client-facing output
  - stale or unverified knowledge where freshness is required

## Execution

- Read catalog metadata from repository knowledge and configured external
  domain-knowledge roots.
- For each candidate document, create a compact catalog entry:
  - `xid`
  - `kind`
  - `domain`
  - `title`
  - `summary`
  - `tags`
  - `content_hash` or equivalent version marker
  - `last_verified` or `unknown`
  - `validity_conditions` or `unknown`
- Do not include local filesystem paths in the client-facing catalog package.
  Server-side diagnostics may retain root identifiers or paths, but those are
  not part of the Skill input payload.
- Do not include full document bodies by default. Bodies are loaded lazily
  through `get_document_by_xid` only after the client/runtime selects an XID.
- If selected Skill requirements are available, map each `knowledge_inputs`
  entry to candidate XIDs by accepted kind, domain, tags, title, summary, and
  validity conditions.
- Mark required `knowledge_inputs` with zero matching candidates as blockers.
- Record duplicate XIDs as conflicts unless an explicit fork/shadow relation is
  present and the MCP contract defines which document is selected.
- Record XID-bearing external knowledge as part of the unified MCP supply; do
  not copy it into this repository.
- Record XID-less external or local material as `not_catalog_ready` and hand it
  off to the appropriate adoption/publication path before it can be selected by
  a Skill.

## Monitoring and Control

- Stop if the prepared catalog would expose local paths to the client.
- Stop if duplicate XIDs cannot be resolved deterministically.
- Stop if required Skill `knowledge_inputs` have no candidate XIDs.
- Downgrade weak or missing metadata to `unknown`; do not invent summaries,
  kind, domain, freshness, or validity conditions from model memory.
- Keep repository knowledge and external domain knowledge distinct in
  server-side diagnostics, but present them as one XID-addressable supply to the
  client/runtime.

## Closure Gate

Closure is allowed only when all of the following are recorded:

- catalog scope
- included repository knowledge roots
- included external domain-knowledge roots, described without client-facing
  local path leakage
- prepared available domain-knowledge metadata list
- summary for every selectable entry, or an explicit invalid/unavailable reason
- content hash/version for every selectable entry, or an explicit unknown with
  impact
- candidate mapping for selected Skill `knowledge_inputs`, when a selected Skill
  was provided
- conflict report
- invalid or not-catalog-ready report
- validation commands and results
- handoff target for the consuming Skill/runtime

Run:

```powershell
python -m xrefkit xref fix
```

When implementation-side catalog tooling exists, also run the MCP/catalog
validation command that proves:

- configured external domain-knowledge roots are included in the catalog
- client-facing responses contain no local paths
- `get_document_by_xid` resolves selected external XIDs
- duplicate XIDs fail closed or follow the declared fork/shadow rule

## Handoff

- Hand the prepared catalog package to the selected Skill runtime context.
- Hand candidate mappings to `planning_flow`, `design_flow`, `db_design`,
  `test_flow`, analysis Skills, or review Skills as applicable.
- Hand XID-less material to the domain-knowledge adoption/publication path.
- Hand catalog conflicts to MCP/catalog administration before the consuming
  Skill runs.

## Rules

- Do not move already-XID-bearing domain knowledge into this repository as the
  normal connection method.
- Do not assign new XIDs in this Skill.
- Do not load all full bodies at startup.
- Do not expose local paths in client-facing catalog entries.
- Do not let external domain knowledge redefine XRefKit governance, routing, or
  Skill operating rules.
- Do not select final knowledge inputs for a Skill without recording the
  selected XIDs and content hash/version in the runtime record.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.
