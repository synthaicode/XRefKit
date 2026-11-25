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

## Validation

| Evidence | Observed result |
| --- | --- |
| Final added projection, stdio and HTTP tests | 9 passed, 1 skipped, 9 subtests passed |
| Existing MCP catalog, initialization, profile and native-definition regressions | 73 passed, 8 subtests passed, both before and after the change |
| Independent quality review | Accepted final file hashes; two test defects corrected and rechecked |
| Independent raw stdio probe | Invalid requests, resource inspection boundary and post-error survival passed |
| XRef fix | No changed files or issues |
| Structured-format and repository checks | TOML parse, whitespace, Skill structure, pack lint, tracked runtime-log audit and project baseline checks passed |
| Whole-suite run on changed worktree | 1,334 passed, 113 failed, 32 errors, 8 skipped, 117 subtests passed |
| Whole-suite run on original `7303a46d` baseline | 1,326 passed, 113 failed, 32 errors, 7 skipped, 108 subtests passed |

The same 145 failure/error node IDs occur in both whole-suite runs; there are
no new failing node IDs. The whole-repository quality gate therefore remains
non-green. Many failures involve Git-dependent adoption/fixture checks; the
comparison establishes their presence before this change, not their root cause.
The final HTTP test was added after whole-suite collection and passed in the
final focused and independent HTTP runs. Counts overlap and are not additive.

A diagnostic baseline rerun of 146 cached failed nodes returned 144 passes and
two failures, showing that the whole-suite result depends on execution context
or order. The corresponding changed-tree diagnostic rerun was stopped once the
complete same-order baseline comparison was available; it is not pass evidence.

Detailed local evidence:

- `work/sep2640/extension-tests.txt`
- `work/sep2640/postchange-mcp-regression.txt`
- `work/sep2640/review.md` and `review-final-hashes.json`
- `work/sep2640/review-wire-evidence.json`
- `work/sep2640/full-quality-gate.txt`
- `work/sep2640/baseline-full-suite.txt` and `baseline-comparison.json`

## Remaining boundaries

- Actual Windows symlink creation/read behavior was skipped because the account
  lacks symlink creation privileges; path validation was otherwise tested.
- Third-party client UI consumption and production deployment were not tested.
- Full `2026-07-28` protocol support and future SDK releases are not established.
- The existing whole-suite failures remain open outside this scoped change.

Both Project Management runs and the implementation run passed deterministic
verification and closure. Their closure records establish recorded workflow
progression, separately from the independent review and test results above.
See the [work plan](plan.md#xid-9A62E4B817C3) for task-to-evidence mapping.
