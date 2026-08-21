# XRefKit

XRefKit is a framework for making AI-assisted work repeatable, reviewable, and
handoff-ready.

It helps teams turn domain procedures and knowledge into work that can be
performed with explicit evidence, human judgment, and completion checks.

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

- **Skills** — reusable procedures for a defined kind of work
- **Knowledge** — source-backed domain facts and local rules
- **Workflow protocol** — recorded progress, deterministic verification, and
  closure checks
- **Evidence and handoffs** — outputs, judgments, concerns, and decisions that
  remain reviewable after the work is done
- **Skill Run Dashboard** — inspect Skill execution status, referenced XIDs,
  evidence, judgments, concerns, and handoffs to improve the auditability of
  results
- **XIDs** — stable references for connecting procedures, knowledge, and
  supporting documents

The package includes the resolver, Skill runtime, workflow controls, client
tools, and an optional MCP adapter.

The [Skill Run Dashboard](docs/guides/086_skill_run_observation_dashboard_usage.md#xid-4A4763A2DE63)
helps people trace how a Skill run used its referenced XIDs and recorded its
evidence before accepting or handing off the result.

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

## Where to go next

- [Install XRefKit and register Skill Packages](docs/guides/089_xrefkit_package_first_registration.md#xid-4F8C2A7D1E90)
- [Understand the workflow protocol](docs/guides/087_workflow_protocol_sequence_for_humans.md#xid-E8B4D2F19A63)
- [Use an instruction-backed workflow](docs/guides/088_instruction_workflow_protocol.md#xid-9F4C2A7D1B60)
- [Understand Skills and Knowledge](docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Author a Skill with xref](docs/guides/013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Browse the complete documentation index](docs/000_index.md#xid-56DD6EB68343)

## Security

XRefKit does not require provider API keys to explore or install the package.
Do not commit secrets, API keys, access tokens, `.env` files, or provider
credentials. Authenticate external AI tools through their official provider
mechanisms.
