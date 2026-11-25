<!-- xid: 73D8E921C4A6 -->
<a id="xid-73D8E921C4A6"></a>

# SEP-2640 delivery result

The scoped server change is implemented and independently reviewed in
`C:/dev/itsm/XRefKit-sep2640`, branch `codex/sep-2640`. The original worktree's
pre-existing changes were retained. No release or deployment was performed.

## Delivered behavior

- Standard wire-level `skills/list` and `skills/get`, with `resources/read`
  and resource discovery for generated Agent Skills bootstrap files.
- `capabilities.extensions["io.modelcontextprotocol/skills"]` and the Resources
  capability are advertised through the existing initialization lifecycle.
- Each generated `SKILL.md` has matching frontmatter, URI, SHA-256 and UTF-8
  byte size. Its canonical-source fingerprint changes with the source.
- Bootstrap Skills guide clients through existing startup, runtime and canonical
  Skill retrieval. Reading the resource does not unlock native execution.
- Invalid parameters and unknown Skill resources return protocol errors.
  Resource URIs are lookup keys, never arbitrary filesystem paths.

The supported binding is MCP `2025-11-25` with SDK `1.28.0`. This is not a
full `2026-07-28` base-protocol migration. Optional directory reads are not
advertised. Native procedure files and supporting assets are not mirrored;
the published Skill is the bootstrap adapter described in the
[implementation basis](design.md#xid-41E7A8B9C620).

## Validation after test-environment repair

The full repository quality gate now passes. The user requested correction and
verification after the initial failure analysis.

| Evidence | Observed result |
| --- | --- |
| Full `python tools/run_quality_gate.py xrefkit` | Exit 0 |
| Whole pytest suite | 1,481 passed, 8 skipped, 117 subtests passed; no failures or errors |
| Subsequent gate stages | XRef, Skill structure, pack lint, tracked runtime-log audit and project baseline all passed |
| Independent repair review | Accepted final six-file hashes; no unresolved findings |
| Focused Azure/environment tests | 219 passed, 1 skipped, 20 subtests; independently reproduced |
| Package environment | Editable repository install; import from another working directory and `pip check` passed |

The repair replaces 16 process-environment mutations in four Azure test files
with an explicit mapping-only test helper. The regression checks that an
inherited empty native value survives normal and exceptional exits. A negative
control with the previous `patch.dict` behavior fails the regression.
No product code or global Git settings changed for this repair.

The earlier 145 failure/error nodes had two causes: native Windows environment
restoration dropped an empty Git configuration value, causing 144 cascading Git
failures; the isolated environment also lacked an installed XRefKit package,
causing one setup failure. Both are corrected and the complete gate was rerun.
The initial baseline comparison remains historical evidence under `work/sep2640/`.

The full run emitted one upstream SDK Pydantic forward-reference warning.
Eight skipped tests remain outside the observed pass coverage; skip conditions
were not relaxed by this repair.

Detailed local evidence:

- `work/sep2640/repaired-full-quality-gate.txt`
- `work/sep2640/repair-review.md` and `repair-review-hashes.json`
- `work/sep2640/repair-review-focused.txt`
- `work/sep2640/repair-review-negative-control.json`
- `work/sep2640/repair-environment-install.txt`
- `work/sep2640/git-environment-reproduction.json`

## Remaining boundaries

- Actual Windows symlink creation/read behavior was skipped because the account
  lacks symlink creation privileges; path validation was otherwise tested.
- Third-party client UI consumption and production deployment were not tested.
- Full `2026-07-28` protocol support and future SDK releases are not established.

Both Project Management runs, the implementation run and the repair run passed deterministic
verification and closure. Their closure records establish recorded workflow
progression, separately from the independent review and test results above.
See the [work plan](plan.md#xid-9A62E4B817C3) for task-to-evidence mapping.


## Additional existing-XID verification

The user's requested existing-XID regression check passed in the modified
server worktree. Existing focused tests produced **96 passed and 8 subtests**.
An independent actual stdio server probe exited 0 with **27 tool calls plus
ping**, while the Skills extension was advertised under MCP `2025-11-25`.

The probe checked three canonical XIDs through `search_knowledge_catalog`,
`get_knowledge_summary`, `expand_knowledge` and `get_document_by_xid`. Search,
metadata and content agreed with their canonical sources; the existing document
link-normalization behavior was accounted for rather than requiring raw-byte
identity where the API normalizes links. It also verified three cache hits,
three cache misses, three pre-startup refusals, three unknown-XID errors and
successful ping/normal retrieval after those errors.

- `work/sep2640/xid-existing-tests.txt`
- `work/sep2640/xid-wire-results.json`
- `work/sep2640/xid-wire-transcript.json`
- `work/sep2640/xid-verification-report.md`
- Server source SHA-256: `b2e2a9b2c84c896b4c58aaff91e01286c5c0ccd26181cbd46d868ce80c307051`.

This confirms the tested local server/API paths, not third-party client UI
behavior or production deployment. The parent registered six issues on
[GitHub Project 7](https://github.com/users/synthaicode/projects/7); [#301](https://github.com/synthaicode/XRefKit/issues/301) now contains the final
XID evidence and its Done board state was read back by the parent.
[#302](https://github.com/synthaicode/XRefKit/issues/302) is also Done after
deterministic verification and accepted closure of all three QA runs and both
PM runs. The parent read back all six items as Done in the actual board.
These completion states describe the recorded local work, not merge or release.
