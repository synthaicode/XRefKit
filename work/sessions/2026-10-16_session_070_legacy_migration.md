## 2026-10-16: Guided legacy Python migration release intake

### Event
The task requested implementation and public release of XRefKit 0.7.0 with guided migration of custom Skills and shared Python tools. The repository startup contract C3A1F78D9B22 was read first. The isolated checkout began clean at 89b21fea69742f7a200acf314658dc0f02415ef5.

The connected MCP reported Core 0.6.3, reader profile, and mcp_only governance. Local runtime selection of python_implementation_flow succeeded with run d31fced1-7364-4379-898b-ec483719ec82; MCP binding and client correlation succeeded, but get_skill returned skill not found. No selected method was executed after this failure.

Read-only source inspection confirmed that legacy migration rejects non-Markdown/text Skill resources, inventories server-visible paths, and considers document retrieval receipts for completion. Existing contribution uploads, review, and adoption provide a possible registration route to investigate.

### Decision
The user explicitly selected repository-native governance for this development chat. The provider mismatch is resolved for this scope. Implementation follows python_implementation_flow with a delegated executor, and independent resource-distribution and release-compatibility work items.

### Human Stated Reason
The requested user experience starts when the connected AI is told to migrate the old environment. The user authorized implementation and public release, and requested separate reporting of real legacy environment verification.

### Deferred
Core implementation and version metadata are prepared for independent review.
Core publication remains pending complete verification. Compatibility PR #162
was merged at dfe9fbd2b5d704b2149942de33fb6e2254913c16 and integrated into the
feature branch. Compatible Skill release workflows are running.

### Open
- Implementation, regression and remote-client tests, review, release publication, and clean-client verification remain outstanding.
- No actual legacy environment path, assets, dependencies, or business-approved expected results were supplied.

## Accepted scope and verification basis

The task instruction is the implementation basis. No actual customer migration is being performed in this release task.

| Requirement | Completion evidence |
| --- | --- |
| New AI starts migration after pip installation and HTTP MCP connection | Startup guidance and clean-client CLI/MCP integration exercise |
| Inventory custom Skills and shared tools without executing them | Representative two-Skill shared-module fixture; inventory and preparation tests |
| Preserve relative paths, shared imports, resources, dependencies and identity | Manifest/hash tests, local cache and cwd/import execution fixture |
| Prepare missing tests without inventing approved outcomes | Scaffold and provenance tests; observed baseline distinct from business expectations |
| Safe execution and explicit unavailable checks | Explicit environment/safe-mode prerequisites; blocked/unknown evidence retained |
| Separate client and server filesystems | Client-produced payload through existing governed ingress, registered assets fetched over MCP |
| No secret bundling or arbitrary server Python execution | Denied-path/resource validation and registration tests; server only serves inert files |
| Durable progress and recovery | Existing runtime workitems/artifacts/concerns; interrupted/repeated operation and changed-byte tests |
| Public release | Reviewed merged commits, successful tag workflows, actual PyPI wheel/hash and clean install |

Baseline: existing tests/test_legacy_migration.py passed 9 tests before implementation.

Published compatibility preflight found brownfield 0.1.5, csharp 0.1.1 and batch-regression 0.4.3 require Core <0.7.0. Compatible official patch releases must precede Core 0.7.0; source-only XDDP remains unpublished. No release gate is waived.

## Review checkpoint

Delegated implementation prepared guided client inventory/preparation, existing
runtime tasks, governed bundle registration, hash-pinned HTTP resource fetching,
verified cache and unchanged packaged migration bootstrap assets. Windows CRLF
byte preservation was corrected in contribution payload reads. The independent
review runtime requires a clean source checkpoint, so this prepared state is
committed before final validation and review; it is not a release acceptance.

Focused worker evidence: resource suite 16 passed; guidance suite 9 passed plus
one subsequent successful workflow-closure test. Parent combined rerun stalled
and was interrupted without a passing claim; verbose diagnostic rerun is active.
XID maintenance reports zero issues. Full quality/build/publication remain open.

## Independent findings and corrections

The independent Python reviewer reproduced reserved-name case alias corruption
and quoted credential-key inclusion, and identified ignored-directory traversal.
The executor fixed all three and added regressions. Reviewer independently
rechecked guidance cases (10 passed) and resource cases (4 passed); no remaining
source finding. The full baseline remains a separate pending review condition.

The stalled stdio test was traced to Git identity subprocess lookup for embedded
bootstrap assets during a Windows live MCP request. Embedded package identity
now avoids Git; the original stdio regression passed. The final focused suite
passed 48 tests in 32.03 seconds. Earlier interrupted runs remain non-passing
evidence and were replaced by this completed run.

Final source wheel and sdist build succeeded. Initial artifact inspection and
Twine metadata checks passed; configured Bandit medium/high gate found no such
findings, and declared dependency audit found no known vulnerabilities. Full
repository quality and exact-final-wheel official compatibility are running.
The three prerequisite official Skill releases are publicly available on PyPI;
their independent installed-public-wheel results are recorded separately.

The full local regression exposed an outdated adoption test that expected an
empty initial Knowledge catalog. Packaged bootstrap Knowledge intentionally
changes that initial state. The test now snapshots the initial XID set, proves
pending review leaves it unchanged, and proves adoption adds exactly ADOPT123.
The targeted test passed (1 test). No adoption implementation change was needed;
the initial full-run failure is retained and final CI must use the corrected test.
