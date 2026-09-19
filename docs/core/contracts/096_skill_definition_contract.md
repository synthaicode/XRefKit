<!-- xid: E6A19D4B72C3 -->
<a id="xid-E6A19D4B72C3"></a>

# SkillDefinition v1 and Derived Catalog

This contract defines the candidate format accepted by the implemented
SkillDefinition parser and catalog builder. MCP `get_skill` returns an explicitly
selected repository definition and a definition referenced by a package manifest
in the same single-document format. The existing split YAML format for packages
remains accepted during the migration period. Successful structural validation
does not mean that a Skill is executable, quality-accepted, or fully migrated.

## Authoritative Editing Source and Responsibilities

The authoritative editing source for a Skill is one Markdown file. Its YAML
header contains discovery, applicability, inputs and outputs, required material,
and verification conditions; the method body follows the header. A JSON header
may also be used as a subset of YAML. The catalog is generated from the
authoritative source and must not become a second hand-edited meta source.

`capability` / `tuning` / `responsibility`, model names, and model tiers do not
belong in the header. They are handled by routing based on the current
instruction and by the
[Workflow Runtime Binding](111_workflow_runtime_binding.md#xid-8D50A972BA9F).
Common Workflow, guard, unknown, verification separation, and escalation rules
must not be redefined for each Skill. Skill-specific applicability exclusions,
method, stop conditions, and handoff remain in the body.

## Physical Format

```text
---
<YAML mapping or JSON object>
---
<XID comment / anchor and Markdown method>
```

UTF-8 (a BOM at the start of the file is permitted). The opening and closing
header delimiters must each be on their own line as `---`, followed by a newline.
Preserve method newlines and the trailing content without normalization. The
file `content_hash` is the SHA-256 of the raw bytes, including the BOM and
newlines; regenerate it when the version changes. When a string is passed to the
parser API, hash the UTF-8 bytes of that string.

Required header fields:

| key | Description |
|---|---|
| `schema_version` | integer `1` |
| `skill_id` | identifier consisting of lowercase English letters, digits, and underscore, beginning with a lowercase letter |
| `xid` | the Skill's 12-character uppercase hexadecimal XID; must match the comment/anchor in the method |
| `summary` | short purpose description used for discovery. Keep the detailed Purpose in the method |
| `applies_when` | array of strings describing applicable situations |
| `exclusions` | array of strings describing exclusions. An empty array is allowed |
| `inputs` / `outputs` | arrays of strings describing input/output requirements |
| `criteria` | verification conditions below. At least one is required |
| `knowledge_needs` | Knowledge search requirements below. An empty array is allowed |
| `control_refs` | array of control/policy XIDs that this Skill additionally retrieves. Use an empty array when there are no additions |

The only optional field is `aliases`. It is an array for mapping XIDs such as
old meta files to the same Skill; it must not contain the Skill's own XID or
duplicates. This mapping is used in the generated catalog and does not
automatically register entries with the existing XID resolver or delete old
files.

Each element of `criteria` has non-empty string values for `id`, `statement`,
and `verification`. These express reusable verification conditions. They do not
mean that task-specific criteria or authority have been finalized, nor that all
future Criterion/Decision schemas have been implemented.

Each element of `knowledge_needs` has non-empty string values for `id`, `query`,
and `required_when`, and has a `seed_xids` array. At the required point, the
executor searches the catalog, confirms applicability, and resolves the body by
XID. Seeds preserve known entry points; they do not permit recursive loading of
related documents or embedding Knowledge bodies in the header. Whether a need is
required follows `required_when` and the Skill method; the mere presence of a
search result does not satisfy the condition.

Common controls supplied during initialization, such as Workflow, Reporting,
Logging, and Context Guard, must not be duplicated in `control_refs`.
`control_refs` lists only controls additionally required by that Skill, such as
a working-area policy. A Skill with no additional controls uses
`control_refs: []`.

Reject undefined keys, duplicate mapping keys, duplicate criterion/need IDs,
invalid XIDs, YAML aliases/anchors, and unsafe tags. The document is limited to
512,000 bytes, the header to 64,000 bytes, and the method to 256,000 bytes. A
structural parser does not validate the existence, authorization, or semantic
fitness of referenced XIDs.

## Catalog and CLI

```powershell
python -m xrefkit skill definition-check --path <candidate-SKILL.v1.md> --json
python -m xrefkit skill definition-catalog --path <candidate-A> --path <candidate-B> --json
```

The catalog outputs the validated header, path/hash for the definition, and XID/
alias mappings. It does not include the method body. Generation inspects each
definition file but does not retrieve Knowledge bodies or referenced targets.
Inspect every specified file; reject the request without returning a partial
catalog if Skill ID or XID/alias collisions occur. Output at most 2,048
definitions in `skill_id` order, and make output independent of input order when
the paths and bytes are the same.

The APIs are `load_skill_definition(path)`, `parse_skill_definition(text, source=)`,
and `build_definition_catalog(paths)`. The CLI returns JSON to stdout and does
not overwrite the authoritative source or an existing catalog. It does not
perform catalog search ranking or model evaluation.

## Running an Explicitly Selected Definition

```powershell
python -m xrefkit skill run `
  --definition skills/<skill>/SKILL.v1.md `
  --task "<task>" `
  --capability "<instruction-derived capability>" `
  --tuning "<instruction-derived tuning>" `
  --responsibility "<delegated responsibility>" `
  --execution-mode subagent_required `
  --json
```

`--definition` and `--meta` are mutually exclusive. The definition format does
not store routing results; it requires the Workflow Runtime Binding
`capability` / `tuning` / `responsibility` / `execution_mode` as inputs when the
run starts and fixes them in the run log. Identify the format as
`definition_format: skill_definition_v1`. Without an external governance
record, use `maturity: unassessed` and do not infer promotion to `stable`.
Use `meta: -` and reference the same `SKILL.v1.md` as the sole execution body.

When `--governance <record.json>` is specified, compare the record's
`skill_id`, XID, and raw definition SHA-256, then record the approved maturity
and promotion decision in the run log. `draft` and `deprecated` cannot be run.
The record does not change the definition body and is separate from production
adoption.

The run log records the definition XID, root-relative path, and raw-byte
SHA-256. `workflow bind-execution` does not accept these from the request; it
copies them from the run log into `definition_identity` and confirms that the
three runtime values match the request. The local subagent reader rechecks the
XID and SHA-256 immediately before passing the body and before recording the
receipt. Therefore, a definition changed after the run starts requires a new
run/binding.

## Explicit Enablement through MCP

On an MCP server, target Skills are explicitly enabled at startup rather than
being found by automatic scanning.

```powershell
python -m xrefkit.mcp.server `
  --repo <repository> `
  --skill-definition skills/<skill>/SKILL.v1.md `
  --skill-governance governance/skills/<skill>.json
```

`XRefCatalog.build(..., skill_definition_paths=[...])` and the catalog CLI's
`--skill-definition` use the same boundary. The corresponding governance record
is specified through `skill_governance_paths` / `--skill-governance`. Specified
paths must refer to files inside the repository. Reject duplicate paths and
`skill_id` / XID / alias collisions between definitions. If an old Skill with the
same `skill_id` exists, the explicitly specified definition becomes the active
catalog entry; do not route to both entries. Candidates that are not specified
do not appear in the MCP catalog.

The catalog entry's `definition_format` is `skill_definition_v1`; the old
meta-plus-body format is `legacy_split_v1`. Routing lists contain only metadata
from the header; after selection, `get_skill` returns the method body as one
document. That document has the same SHA-256 as its raw UTF-8 bytes, including
the BOM and newlines. The MCP subagent reader compares
`ExecutionBinding.definition_identity` path / XID / SHA-256 with the catalog
response before receiving the body and recording the receipt. A legacy entry
continues to return meta and body as two documents.

`resolve_skill_knowledge(skill_id, active_need_ids=...)` is called by the parent
after evaluating the instruction and `knowledge_needs.required_when` and
explicitly naming active need IDs. When `active_need_ids` is omitted, return
each need with `activation_state: unresolved`, `required: null`, and
`satisfied: null`; do not treat an unevaluated condition as unnecessary. When
specified, reject unknown and duplicate IDs and mark only active needs as
required. List candidates matching `seed_xids` first, followed by query-ranked
results with duplicate XIDs removed. As before, retrieve selected bodies by XID
and revision, and record them in `ExecutionBinding.references` and the run's
Knowledge observation.

Protocol selection, administrative upload, and the old `--meta` execution path
are unchanged. If `package manifest` `provides.skills[].path` points to a
Markdown definition, validate and catalog it as `skill_definition_v1` after
entry-point discovery. A package pointing to the existing `*.skill.yaml`
continues as `legacy_split_v1`. In both cases, the path must not escape the
package.

The admin profile provides the contribution upload, staging, seal, review, and
adoption path. Each state transition preserves its own authority boundary:
upload success does not make a Skill routable, review acceptance does not publish
it, and adoption does not prove distribution or live availability. The adoption
path validates the immutable review event, approval token, raw-byte hash, XID,
and target ownership before writing through the repository-owned transport. A
newly adopted SkillDefinition becomes routable only after it is included through
the existing explicit-enablement or package-discovery boundary and that active
catalog state is verified.

## Representative Conversion and Cutover Conditions

```powershell
python -m tools.convert_dotnet_skill_definition --root .
```

The representative conversion reads `skills/dotnet_change_analysis` and creates
a candidate and `migration.json` under
`work/skill-definition-candidate/dotnet_change_analysis/`. Preserve the original
body byte-for-byte and map the 9 Closure Gate conditions and 5 Knowledge
requirements into the header. Record every original meta field/value and its
destination in the manifest. Keep dynamic execution items as
`runtime_cutover_pending`, and preserve observation/promotion history and other
items as provenance. Reject overwriting an edited candidate.

The converter output demonstrates the physical format consolidated into one
authoritative source; it does not simplify the meaning because the original body
is preserved byte-for-byte. Separately, place the
[tracked v1](../../../skills/dotnet_change_analysis/SKILL.v1.md#xid-9883EF4E8CA9),
which integrates common controls into references. It preserves the method,
Knowledge requirements, and verification conditions specific to the Skill, and
maps the old body XID `D94E3B3A7C11` and old meta XID `1F4A6D20B8E1` through
`aliases`.

tracked v1 is the recommended target for explicit definition selection. Keep the
old Skill body and meta readable through the legacy path. The existence of
tracked v1 does not mean automatic adoption or maturity promotion. Confirm the
following separately before switching the production default:

- Record human acceptance of the simplified method and verification conditions in the governance record.
- Align the adopted versions of source, catalog, package, administrative upload, and docs.
- Do not delete the old body and meta until the retirement conditions for the legacy path are decided.

[Workflow Protocol](../../guides/088_instruction_workflow_protocol.md#xid-9F4C2A7D1B60)'s
verify/close and human judgment of output quality and adoption remain separate.
