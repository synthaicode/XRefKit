# XRefKit

XRefKit is a framework for making AI-assisted work repeatable, reviewable, and
handoff-ready.

It helps teams structure domain procedures and knowledge so that work can
record evidence, preserve human judgment, and apply explicit completion checks.

## Why XRefKit?

Using AI for real work creates recurring operating problems:

![Why XRefKit is needed](human-docs/en/assets/why_xrefkit_needed/whatis_xrefkit.png)

- the AI can act from incomplete context or unsupported guesses
- procedures, domain facts, and judgment criteria get mixed together in prompts
- execution, checking, and handoff collapse into one opaque step
- work becomes hard to continue across agents, humans, or sessions
- outputs may lack evidence, closure discipline, or auditability

XRefKit provides a repository and runtime model for addressing these problems.

## What it provides

- **Skills** — reusable procedures expressed as SkillDefinitions
- **Knowledge** — source-backed domain facts and local rules resolved by XID
  when a Skill run needs them
- **Workflow protocol** — recorded progress, deterministic workflow-record
  verification, and closure checks
- **Evidence and handoffs** — outputs, judgments, concerns, and decisions that
  remain reviewable after the work is done
- **Skill Run Dashboard** — inspect recorded Skill execution state, definition
  identity, runtime binding, referenced XIDs, evidence, judgments, concerns,
  and handoffs
- **XIDs** — stable references for connecting procedures, knowledge, and
  supporting documents

The package includes the resolver, Skill runtime, workflow controls, client
tools, and an optional MCP adapter.

Current Skill authoring targets the one-document `skill_definition_v1` format.
Existing `legacy_split_v1` Skills and unversioned historical run logs remain
readable during migration. `capability`, `tuning`, `responsibility`, and
`execution_mode` are derived for each run and captured in its runtime binding;
they are not fixed properties of a SkillDefinition. Knowledge used by a Skill
remains separate and is resolved from the XID catalog when needed.

The [Skill Run Dashboard](docs/guides/086_skill_run_observation_dashboard_usage.md#xid-4A4763A2DE63)
helps people inspect recorded XID retrieval and use together with the run's
evidence before a human accepts or hands off the result. The Dashboard reports
recorded state and missing observations; it does not accept output quality.

## Quick start

XRefKit requires Python 3.11 or later.

```powershell
python -m pip install xrefkit
xrefkit init
xrefkit --help
```

For local development:

```powershell
python -m pip install -e .
xrefkit init
```

For the optional MCP server:

```powershell
python -m pip install "xrefkit[mcp]"
xrefkit mcp serve --repo . --transport stdio
```

This command starts the optional catalog and runtime MCP adapter. This checkout
does not implement management upload, staging, sealing, review, or adoption of
uploaded SkillDefinition bytes into the active catalog.

## Where to go next

- [Install XRefKit and register Skill Packages](docs/guides/089_xrefkit_package_first_registration.md#xid-4F8C2A7D1E90)
- [Understand the workflow protocol](docs/guides/087_workflow_protocol_sequence_for_humans.md#xid-E8B4D2F19A63)
- [Use an instruction-backed workflow](docs/guides/088_instruction_workflow_protocol.md#xid-9F4C2A7D1B60)
- [Understand Skills and Knowledge](docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Read the SkillDefinition v1 contract](docs/core/contracts/096_skill_definition_contract.md#xid-E6A19D4B72C3)
- [Author a Skill with xref](docs/guides/013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Browse the complete documentation index](docs/000_index.md#xid-56DD6EB68343)

## Security

XRefKit does not require provider API keys to explore or install the package.
Do not commit secrets, API keys, access tokens, `.env` files, or provider
credentials. Authenticate external AI tools through their official provider
mechanisms.
