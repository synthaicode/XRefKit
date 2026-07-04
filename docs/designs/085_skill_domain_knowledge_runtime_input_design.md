<!-- xid: BC6C6D89E4E1 -->
<a id="xid-BC6C6D89E4E1"></a>

# Skill Domain Knowledge Runtime Input Design

Status: proposal.

This note summarizes the agreed boundary for Skill startup, judgment criteria,
and brownfield domain knowledge when XRefKit is consumed through MCP.

## Problem

Brownfield work needs target-service facts such as service structure, module
boundaries, API catalogs, database schemas, screen flows, batch flows, external
integrations, roles, state transitions, and source-structure findings.

Those facts are domain knowledge for the target service. They may be built
locally outside the XRefKit repository and supplied to an MCP client as
XID-addressable knowledge. A client that consumes XRefKit through MCP must not
depend on local repository paths. It can only list and load material through MCP
tools and XIDs.

The Skill selection path is separate:

1. startup loads the repository-defined MCP startup context
2. semantic routing selects the target Skill
3. deterministic runtime opening happens through the Skill operating contract
4. the selected Skill uses only the context supplied to that run

The open question is where the domain knowledge list belongs.

## Decision

Do not store the available domain knowledge list in the Skill definition.

The Skill definition declares what kind of domain knowledge it can accept or
requires. The MCP/runtime supplies the available domain knowledge catalog for
the current run. The client selects entries from that catalog by XID and loads
full bodies on demand by XID.

The model is:

```text
Skill meta
  -> declares judgment criteria refs
  -> declares domain knowledge input requirements
  -> does not carry target-service domain knowledge XIDs

MCP runtime context
  -> exposes the selected Skill
  -> exposes available domain knowledge catalog entries
  -> exposes only XID-addressable metadata and bodies

Run/session/artifact records
  -> record which domain knowledge XIDs were selected
  -> record which domain knowledge XIDs were actually used
```

## Terminology

### Judgment refs

Judgment refs are fixed references to decision criteria, extraction criteria,
review criteria, operating contracts, or method catalogs that a Skill uses to
perform its work.

Examples:

- C# review criteria
- constraint derivation catalogs
- document update policy
- Skill operating contract
- source-analysis criteria

These refs may be fixed XID links because they are part of the repository's
method and judgment basis.

### Domain knowledge inputs

Domain knowledge inputs are task-specific or brownfield facts supplied to a
Skill run.

Examples:

- target service structure
- module map
- API catalog
- database schema
- screen flow
- batch flow
- external integration map
- local business rules
- locally extracted source-structure findings

These inputs must not be fixed in the Skill definition. They are selected for a
run from the available domain knowledge catalog.

## Skill Meta Shape

A Skill should separate fixed judgment criteria from runtime domain knowledge
inputs.

```yaml
judgment_refs:
  - name=design_constraint_derivation_framework; bind=81A6C4E2B190
  - name=design_constraint_derivation_catalog; bind=2D14F88A6C01

knowledge_inputs:
  - name=target_service_structure
    required=true
    accepts=service-map,module-map,api-catalog,database-schema,screen-flow,batch-flow,external-integration-map
    purpose=design-context
```

`judgment_refs` are fixed repository criteria. `knowledge_inputs` are input
requirements and do not name concrete target-service XIDs.

## MCP Runtime Shape

MCP should provide the selected Skill context without exposing local paths to
the client.

Expected tool responsibilities:

- `list_skills` / `rank_skills_for_purpose`
  - support semantic Skill routing
- `get_skill_requirements`
  - return fixed `judgment_refs`
  - return `knowledge_inputs`
- `list_domain_knowledge`
  - return available domain knowledge metadata
  - include XID, title, kind, domain, tags, summary, and hash/version metadata
  - do not include full bodies by default
- `prepare_skill_context`
  - combine selected Skill requirements with available domain knowledge
  - return candidate entries or recommended selected input sets
- `get_document_by_xid`
  - load the full body for any selected XID

Example response shape:

```json
{
  "skill_id": "design_flow",
  "judgment_refs": [
    {
      "name": "constraint_derivation_framework",
      "xid": "81A6C4E2B190"
    }
  ],
  "knowledge_inputs": [
    {
      "name": "target_service_structure",
      "required": true,
      "accepts": [
        "service-map",
        "module-map",
        "api-catalog",
        "database-schema"
      ],
      "purpose": "design-context"
    }
  ],
  "available_domain_knowledge": [
    {
      "xid": "LOCAL-SERVICE-MAP-001",
      "kind": "service-map",
      "title": "Target service structure",
      "summary": "Service boundaries, major modules, and external integrations"
    },
    {
      "xid": "LOCAL-DB-SCHEMA-001",
      "kind": "database-schema",
      "title": "Database schema overview",
      "summary": "Major tables, relationships, and state columns"
    }
  ]
}
```

The client selects from `available_domain_knowledge` by XID. If it needs the
body, it calls `get_document_by_xid`.

## Runtime Record Shape

The runtime record should preserve the difference between available, selected,
and actually used knowledge.

```md
## Available Domain Knowledge

- xid: `LOCAL-SERVICE-MAP-001`
  kind: `service-map`
  title: `Target service structure`
- xid: `LOCAL-DB-SCHEMA-001`
  kind: `database-schema`
  title: `Database schema overview`

## Selected Knowledge Inputs

- target_service_structure:
  - `LOCAL-SERVICE-MAP-001`
  - `LOCAL-DB-SCHEMA-001`

## Used Knowledge Refs

- `LOCAL-SERVICE-MAP-001`
```

Available knowledge is the catalog supplied to the run. Selected knowledge is
what the client/runtime assigned to the Skill input. Used knowledge is what the
Skill actually consulted and should be carried into evidence or handoff.

## XID Boundary

MCP clients must not receive or depend on local repository paths for XRefKit
content or local domain knowledge. Paths may exist inside the MCP server or
repository implementation, but the client-facing contract is XID-based.

Normal path:

```text
metadata list -> choose XID -> get_document_by_xid(XID)
```

If two catalogs contain the same XID, MCP should treat that as a conflict path.
Normal responses do not need to expose catalog origin. Origin/source metadata is
only needed for conflict diagnosis, debugging, or administrative reconciliation.

## Non-MCP Validation Path

The MCP design must be proven through the repository-native deterministic
runtime before it is made MCP-only.

The non-MCP validation target is not "clients can read local paths." It is:

```text
fm can open a Skill run with an XID-only domain knowledge catalog,
record selected knowledge inputs by XID,
and preserve used knowledge refs by XID without requiring MCP.
```

This proves the runtime model independently from MCP transport.

### Required local fixture

Use a local test catalog that contains metadata only and no file paths in the
client-facing entries.

```json
{
  "entries": [
    {
      "xid": "LOCAL-SERVICE-MAP-001",
      "kind": "service-map",
      "title": "Target service structure",
      "summary": "Service boundaries, major modules, and external integrations",
      "tags": ["structure", "service", "integration"]
    },
    {
      "xid": "LOCAL-DB-SCHEMA-001",
      "kind": "database-schema",
      "title": "Database schema overview",
      "summary": "Major tables, relationships, and state columns",
      "tags": ["database", "schema"]
    }
  ]
}
```

The repository-side validation command may read this fixture from a local path,
because this is an internal deterministic test. The generated run record and
the future MCP-facing payload must not expose that path as the knowledge access
mechanism.

### Required fm behavior

`fm skill run` should gain a repository-native input path for this proof, such
as:

```powershell
python -m fm skill run `
  --meta skills/design_flow/meta.md `
  --task "Design target service changes" `
  --domain-knowledge-catalog work/fixtures/domain_knowledge_catalog.json `
  --knowledge-input target_service_structure=LOCAL-SERVICE-MAP-001,LOCAL-DB-SCHEMA-001
```

The resulting run log should include:

- available domain knowledge entries by XID
- selected knowledge inputs by input name and XID
- no client-facing local path as the retrieval mechanism
- a place to record used knowledge refs by XID after execution

The existing `fm skill artifact` command can already record XID targets as
evidence, source, judgment, or output targets. That is enough for used refs, but
not enough for the startup-time available/selected catalog. The startup-time
catalog needs to be part of the initial runtime envelope so the Skill cannot
silently use a different knowledge set later.

### Validation checks

The non-MCP proof should verify:

1. a Skill run can be opened from `fm skill run`
2. the run log records the available domain knowledge catalog as XID metadata
3. the selected knowledge inputs are valid XIDs from the available catalog
4. required `knowledge_inputs` are satisfied before execution proceeds
5. used refs can be recorded by XID during execution
6. `fm skill verify` can validate the run without MCP
7. no generated client-facing section instructs the user to read a local path
   for domain knowledge content

This gives an MCP-independent executable contract. MCP can then implement the
same contract as transport:

```text
local fixture catalog for fm proof
  -> MCP list_domain_knowledge response

fm selected knowledge inputs
  -> MCP prepare_skill_context selected inputs

fm used knowledge refs
  -> MCP/client session evidence refs
```

## Current Gaps

The current repository and MCP implementation still mix these concepts in some
places:

- `knowledge_slots` currently contains both fixed criteria links and dynamic
  knowledge needs.
- Some Skill metas use `bind=<XID>` for criteria-like knowledge.
- MCP currently maps `knowledge_refs` and bound `knowledge_slots` into
  `required_knowledge`.
- `resolve_skill_knowledge` accepts both query slots and pinned `bind` XIDs.
- `fm skill run` does not yet accept or validate an XID-only domain knowledge
  catalog for the run envelope.

Those are transitional shapes. The target model is:

```text
judgment_refs
  fixed repository criteria and method refs

knowledge_inputs
  runtime input requirements for brownfield domain knowledge

available_domain_knowledge
  MCP-supplied XID catalog for the current client/run

selected_knowledge_inputs
  XIDs assigned to Skill inputs for the current run

used_knowledge_refs
  XIDs actually consulted by the Skill
```

## Implications

- Semantic routing decides which Skill runs; it does not select all domain
  knowledge bodies.
- The Skill does not own target-service facts.
- The MCP catalog supplies an XID-addressable list of available domain
  knowledge before or during Skill context preparation.
- Full domain knowledge bodies stay lazy and are loaded only by XID.
- Repository updates should not break local brownfield domain knowledge links,
  because concrete local XIDs are not embedded in Skill definitions.
