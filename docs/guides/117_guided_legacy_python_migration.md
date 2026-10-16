<!-- xid: 6D73C9A12E40 -->
<a id="xid-6D73C9A12E40"></a>

# Guided migration of legacy Skills and Python tools

Start with a new XRefKit installation and a connected AI client. Tell the AI:
"Migrate this old XRefKit environment." The AI asks for the source folder when
it is unknown, inspects it without running its code, and prepares the work needed
for migration. You do not need to ask an AI in the old environment first or
write a test suite before starting.

## Preparation and responsibility

Install XRefKit in the client Python environment. The client needs permission to
save files and run Python. Both the HTTP fetch client and server require the MCP extra:

```powershell
python -m pip install --upgrade xrefkit
python -m pip install --upgrade "xrefkit[mcp]"
```

For HTTP, connect the AI client to the server's Streamable HTTP endpoint. A
locally operated reader server can be started with:

```powershell
python -m xrefkit mcp serve --repo C:\xrefkit-server --transport streamable-http --host 127.0.0.1 --port 8000
```

The default endpoint is `http://127.0.0.1:8000/mcp`. A remote server and the
client have separate filesystems: a path on the client is never implicitly a
server path. The reader endpoint serves definitions and resources. Registration
uses the existing administrator contribution route and its human approval
boundary. Administrators retain the loopback-only management profile; remote
clients need an authorized connection to that management endpoint.

MCP does not execute the migrated Python. The existing Python client runtime
materializes and verifies resources locally; no separate client service is
required. Dependencies, configuration, credentials and access to external
systems remain requirements of the individual code.

## What the AI must establish

| Work | Completion evidence |
| --- | --- |
| Inventory | Selected Skills, shared tools/modules, data resources, tests, dependencies and unresolved references are listed |
| Scope and preparation | Required work items have owners and completion conditions in the existing Workflow runtime |
| Safe baseline | Existing tests run only in an approved test environment or safe mode; commands, inputs, results and provenance are recorded |
| Missing coverage | AI prepares missing test code/data where expectations can be established; unknown business expectations remain human questions |
| Migration | Selected definitions are registered and the approved resource bundle preserves relative layout and identity |
| Client verification | Definitions and resources are fetched from MCP, hashes checked, and migrated behavior tested on the client |
| Handoff | Failures, unavailable checks, remaining decisions and recovery steps are explicit |

The AI should reuse existing tests before generating new ones. A scaffold is
preparation, not a passing test. A captured legacy output establishes observed
behavior for those inputs; it is not a business-approved expected result. A
comparison can establish preservation of that behavior without certifying the
business rule. If the old environment is inaccessible, record the baseline as
unavailable and retain the resulting verification gap.

Do not run arbitrary legacy scripts merely because they appear to be tests.
Inspect side effects and establish a test environment or an explicit safe mode
first. Never bundle real credentials, tokens or secret-bearing configuration.
Use sanitized test data and record external dependency requirements separately.
The inventory's credential-name and content checks are heuristics, not a proof
that the selected files contain no secrets. Review the exact file set before
upload. Unsupported non-UTF-8 or binary inputs are listed for separate handling;
they are not silently converted or counted as migrated.

## Registration and distribution boundary

The AI can inspect the client source without executing it:

```powershell
python -m xrefkit mcp migrate inspect --source C:\legacy-xrefkit
```

A fresh Core server provides the existing `legacy_flow_skill_migration`
definition as a bootstrap selection. Its method prepares a trial-first scaffold
with explicit gaps; this distribution does not promote its maturity or certify
the imported Skills. Fetch it with `get_skill`, save the returned definition
bytes on the client, and open the normal Skill runtime envelope before using
its method. Derive capability, tuning, responsibility and execution placement
from the current instruction and host. For example:

```powershell
python -m xrefkit skill run --root C:\client-work --definition C:\client-work\migration.SKILL.v1.md --task "Inspect the old environment and prepare migration tasks" --capability "legacy migration" --tuning "Python resource migration" --responsibility "inventory and prepare migration with explicit gaps" --execution-mode local_default --json
```

Bind the returned `run_id` and `skill_id` through `bind_skill_run`, and run its
returned correlation command against the returned log. Use the actual current
Skill content hash for contribution metadata. A placeholder or invented source
identity cannot satisfy the contribution gate. The AI continues the broader
migration through the concrete preparation work items below.

After opening the selected Skill Run, it prepares only the selected Skills and
explicitly inventoried resource files. Repeat `--skill` and `--resource` for
additional selections. Keep the output outside the source folder:

```powershell
python -m xrefkit mcp migrate prepare --source C:\legacy-xrefkit --output C:\migration-candidate --skill skills/review --resource tools/review.py --log C:\client-work\work\sessions\migration-run.md
```

Use the exact portable paths returned by the inventory for selections. The
preparation command adds concrete work items to the existing run, including
scope, safety, tests, baseline, expectations, upload, registration and client
verification. Its static test scaffold and empty case data preserve missing
expectations as unknown. The AI must complete those tests and supply justified
test data before claiming behavior verification.

The prepared result supplies metadata for the existing
`create_contribution_upload_session` and `seal_contribution_upload` calls.
Upload and seal the exact prepared file set; follow the returned limits and
session information. After trusted human review and `adopt_contribution_return`,
the administrator calls `register_legacy_bundle(contribution_id)`. Registration
verifies the adopted bytes before converting the contained selected Skills.

Migration preparation and later execution are separate operations. A migration
bundle associates selected Skills with the files they need, including shared
modules outside Skill folders. The manifest records version and content hashes.
The original relative layout is preserved so initial migration does not require
rewriting every import. Multiple Skills may refer to the same shared resources.

Transfer prepared bytes through the existing
[contribution upload, review and adoption process](095_mcp_contribution_return_adoption.md#xid-0E5C778EB6AF).
Upload is inert staging. Human adoption applies to the exact reviewed bytes and
destination; an AI must not invent approval assertions. Registration then makes
the selected converted definitions available for retrieval. Neither upload nor
registration certifies business correctness or promotes Skill maturity.

After selection, the client fetches the required resource version, validates its
content and materializes it in a local cache. Reusing the same version must still
detect changed cached bytes. Run the selected script from the preserved bundle
root so relative paths and imports keep their original meaning. Install declared
dependencies separately in an appropriate environment; resource retrieval does
not install packages or obtain credentials automatically.

`get_skill` returns the registered Skill's `client_resources` association. Use
its namespace and manifest hash when fetching through the Python client:

```powershell
python -m xrefkit mcp migrate fetch --url http://127.0.0.1:8000/mcp --skill-id <registered-skill-id> --namespace <namespace> --manifest-hash <manifest-hash> --cache C:\xrefkit-cache
```

The result reports `cache_root` without executing the code. After the safety
and dependency work items have evidence, use that directory as the working
directory and run the reviewed entrypoint locally with `python -B`. Keep mutable
outputs outside the immutable cache. Repeated fetches validate cached bytes and
the manifest; a modified cache is rejected rather than silently trusted.

## Recovery and completion

Keep the preparation artifacts, runtime log and exact bundle identity. Resume
the same work items after interruption. Preserve failed or unknown results and
do not overwrite customized files to force a retry to pass. Changed bytes are a
new candidate that needs the applicable review and identity checks.

Document-only legacy migration retains its existing retrieval receipts. For a
Python migration, those receipts alone do not establish complete behavior
verification. Report registration, retrieval, client execution, baseline
comparison and business acceptance separately, with evidence for each claimed
result. Unavailable checks are never passing checks.

After the exact manifest-bound migration work items are complete and the
existing Skill Run passes its normal verification and closure, the administrator
can call `register_legacy_bundle` again with the same contribution ID and the
full closed run text in `verification_workflow`. The server rechecks the existing
runtime closure rules and exact work-item criteria before retaining that record.
This is record-level process evidence: it does not read external evidence
artifacts or independently certify their business conclusions. Pending,
escalated or unknown migration items do not satisfy normal completion. Migrated
definitions retain the importer's draft readiness until the applicable existing
authoring/readiness gates are satisfied; resource adoption does not promote them.

See [package installation and registration](089_xrefkit_package_first_registration.md#xid-4F8C2A7D1E90),
[Workflow runtime](087_workflow_protocol_sequence_for_humans.md#xid-E8B4D2F19A63)
and [Core/Skill release compatibility](112_core_skill_release_compatibility.md#xid-0C41A7D389B2).
