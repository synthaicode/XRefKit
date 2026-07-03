<!-- xid: A9E742B1C6D0 -->
<a id="xid-A9E742B1C6D0"></a>

# Current Source Structure Findings Catalog

## Purpose

This catalog is the canonical knowledge-side index for current source structure
findings used by design and later implementation preparation.

`design_flow` uses this catalog to decide whether an implementation target
already has a current structure basis. If no current entry covers the target,
the target is routed through `dotnet_change_analysis`, and the resulting
candidate is published or refreshed through `knowledge_ontology_management`
before design closure.

## Catalog Rules

- Keep only current source structure findings in this catalog.
- Do not preserve stale entries here; replacement history belongs to Git or
  work records.
- Use the finding XID as the stable identity.
- Do not require `path` when the XID resolves the canonical finding content.
- Do not add `applies_to` metadata for Skill selection. The invoking Skill
  selects entries from target identity, source scope, analysis kind, and
  coverage fields.
- Work artifacts can be source basis evidence, but design closure should
  reference the canonical finding XID after publication.
- A catalog entry is valid only when unresolved verification items are explicit.

## Entry Metadata Contract

| Field | Required meaning |
| --- | --- |
| Finding XID | Stable identity of the canonical current finding. |
| Target identity | Service, package, framework sample, or bounded source target. |
| Source scope | Repository, solution, project, directory, external source bundle, or other bounded source scope. |
| Analysis kind | Example: `dotnet_structure`, `custom_framework_xml_routing`, `test_granularity`, `package_issue`. |
| Current status | Whether the entry is current for the named source scope. |
| Last verified on | Date the source basis was verified for this finding. |
| Coverage summary | Structure pivots, route/usecase traces, implicit bindings, prohibited changes, or explicit not-applicable reasons. |
| Source basis | Evidence used to publish the finding. |
| Producer Skill | Skill that produced the candidate finding. |
| Unresolved verification | Remaining unknowns that must not be guessed by later phases. |

## Current Entries

| Finding | Target identity | Analysis kind | Current status | Coverage summary | Unresolved verification |
| --- | --- | --- | --- | --- | --- |
| [Maverick.NET Friendbook XML-command structure findings](171_maverick_net_friendbook_structure_findings.md#xid-B4F8D2A91C03) | Maverick.NET 1.0 Friendbook sample | `dotnet_structure`, `custom_framework_xml_routing` | Current for the 2026-07-03 source snapshot | Structure pivots, route/usecase traces, implicit runtime bindings, and prohibited changes are recorded. | Build/runtime execution, browser verification, security assessment, and C# defect review remain out of scope. |

## Knowledge Relations

- depends_on: [Dotnet change analysis viewpoints](120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)
- depends_on: [Domain knowledge ontology rules](../organization/200_domain_knowledge_ontology_rules.md#xid-5803607419B9)

## Sources

- source_type: repository_knowledge
- source_path: 171_maverick_net_friendbook_structure_findings.md
- source_locator: section=Status,Structure Pivots,Route / Usecase Trace Coverage,Implicit Runtime Bindings,Prohibited Change Rules
- extracted_at: 2026-07-03
