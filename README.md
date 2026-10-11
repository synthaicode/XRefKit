# XRefKit

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/xrefkit?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/xrefkit)

**Give your AI a repeatable way to work—and give people a clear way to review the result.**

XRefKit helps you reuse your team's procedures and knowledge, keep evidence with
the work, and carry unfinished tasks into the next session. Use it when AI-assisted
work needs to be checked, repeated, or handed to someone else.

## What you can do with XRefKit

| When you need to… | How XRefKit helps |
| --- | --- |
| Stop explaining the same process in every chat | Keep a reusable procedure in a **Skill**, with domain rules and reference material stored separately as **Knowledge**. |
| Review the basis for a result | Keep outputs, references, judgments, and unresolved concerns in the work record so a reviewer can inspect the evidence. |
| Get a report you can make a decision from | Connect conclusions to criteria, evidence, limitations, and next actions; reuse an approved report format when consistency matters. |
| Continue in another session or hand work to a colleague | Record progress, remaining items, and handoff information that the next person or AI can load. |
| Check whether work is ready to finish | Use workflow-record verification and closure checks to identify missing records and unfinished items before accepting the result. |
| Keep references usable as documents move | Use stable document identifiers (**XIDs**) to find the procedures and knowledge a task needs. |

For example, a recurring review can use the same procedure each time, load the
relevant criteria, and leave a record of findings, evidence, and open questions.
The reviewer can then decide what to accept and what needs more work.

XRefKit checks the completeness and consistency of recorded work. People remain
responsible for judging whether the output is correct and suitable for its purpose.

## How does it fit with modern agent harnesses?

**Use XRefKit to make the conditions behind successful work reusable—and make
the next result easier for people to judge.**

Modern harnesses already do much more than call a model. Anthropic's
[Managed Agents architecture](https://www.anthropic.com/engineering/managed-agents)
separates execution, durable sessions, and sandboxes. Its
[application-development harness](https://www.anthropic.com/engineering/harness-design-long-running-apps)
uses explicit evaluation criteria, independent evaluators, and structured handoffs.
OpenAI's [harness engineering approach](https://openai.com/index/harness-engineering/)
uses repository knowledge, execution plans, and automated constraints. These
examples overlap with XRefKit's goals.

The practical distinction is what XRefKit packages for you to reuse:

| Your question | What XRefKit makes explicit | Benefit for your team |
| --- | --- | --- |
| Which procedure and criteria should this task use? | A SkillDefinition records applicability, inputs, outputs, criteria, and knowledge needs. | You can review and reuse the method across recurring tasks. |
| Which rules and evidence informed the work? | Knowledge is maintained separately from procedures and resolved through stable XIDs; runs can record retrieval and use. | You can update reference material separately and inspect the recorded basis for a result. |
| What is complete, and what still needs a decision? | Work items, artifacts, concerns, and handoffs have explicit records; `verify` and `close` check workflow-record requirements. | Reviewers can find missing records and unresolved items without reconstructing the whole chat. |
| Will the report support the same kind of review next time? | Reporting guidance connects conclusions to their basis and limits. Opt-in Knowledge profiles preserve approved output examples, format, granularity, and criteria. | Readers can use a familiar report structure and reviewers can check against an explicit accepted baseline. |
| Can the next person or AI use the same process? | Repository files and Skill Packages preserve methods and knowledge; CLI/MCP interfaces expose them to compatible clients. | You can carry the working materials into another session or supported client, with its setup and execution responsibilities still explicit. |

For example, your coding harness can implement and test a change while XRefKit
records the review procedure, applicable domain criteria, evidence, and remaining
concerns for the next reviewer. The report turns those records into a conclusion
the reviewer can assess, with the evidence and unresolved decisions close at hand.
The client still runs the model and tools.
XRefKit's deterministic checks validate the work record; output quality still
needs appropriate tests and review.

If your existing harness already provides these structures, the overlap may be
enough for your needs. XRefKit is useful when you want to maintain them as explicit,
reusable work assets. This is a comparison of mechanisms, not a demonstrated
quality, cost, or performance advantage over the cited systems.

See the [Skill and Knowledge operating model](docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
and [Skill operating contract](docs/core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
for the boundaries behind this comparison.

## Turn work records into reports people can act on

A useful report tells the reader what the result supports, what remains uncertain,
and what decision or action comes next. Once the task's criteria or review gate are
agreed, XRefKit's reporting guidance makes those relationships explicit. A summary
finding links to its supporting detail so readers can check the basis without
reconstructing the conversation. The task determines the report's shape.

For recurring reports, you can opt into a target-specific **Knowledge quality
profile**. It preserves an approved example, sample inputs, headings, table
structure, information placement, required detail, and review criteria. Give that
baseline to the reviewer on subsequent runs, including when the model or session
changes. Structural checks help detect format differences; independent review
still judges meaning, readability, and whether the evidence supports the conclusion.

Consider a recurring change-review report: readers can find the affected area,
finding, evidence, impact, and next action in the agreed places each time. If this
run lacks evidence for a conclusion, that limit belongs beside the conclusion;
passing the format check does not make it acceptable.

Feedback can then be directed to the part that needs attention: the current
output, missing inputs, unclear criteria, or the reusable procedure. Approved
examples and criteria remain the baseline; changing a procedure requires explicit
authorization. This connects **execution → evidence → report → human judgment →
authorized improvement**, giving the team a way to investigate recurring quality
problems and assess whether a correction helped.

Workflow-record completion, report format, substantive quality, and human
acceptance remain separate judgments. The controls support repeated review against
known conditions; they do not by themselves prove consistent quality or less rework.
See the [reporting contract](docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73)
and [fixed-output quality protocol](docs/core/contracts/112_fixed_output_quality_protocol.md#xid-F9C2A8D471B0).

## Start with one recurring task

Choose a task you already know how to review: a document check, an investigation,
or a development handoff. Start with one procedure and the reference material it
needs, then use the resulting work record to decide what to improve.

### 1. Prepare your workspace

You need Python 3.11 or later. Run these commands in the folder where you want to work:

```powershell
python -m pip install xrefkit
xrefkit init
xrefkit --help
```

Initialization creates the local XRefKit configuration and missing AI startup
files while preserving existing startup files. See the
[installation and Skill Package guide](docs/guides/089_xrefkit_package_first_registration.md#xid-4F8C2A7D1E90)
to add reusable Skills or bring existing material into your workspace.

### 2. Connect your AI tool

For VS Code/Copilot, install the optional MCP integration and generate a setup proposal:

```powershell
python -m pip install "xrefkit[mcp]"
python -m xrefkit mcp setup --repo . --output .xrefkit/setup-review
```

Review the generated files, then apply the setup:

```powershell
python -m xrefkit mcp setup apply --repo . --source .xrefkit/setup-review
```

Open the workspace in VS Code, start the `xrefkit` MCP server, and ask in Copilot chat:

> Call XRefKit's get_startup_context and help me get started.

Then describe the task you want to accomplish. You do not need to know a Skill
name to ask for guidance. Opening VS Code alone does not start the conversation.

For an MCP client that accepts a local server command, the server entry point is:

```powershell
xrefkit mcp serve --repo . --transport stdio
```

### 3. Review the work and decide what comes next

Use the [Skill Run Dashboard](docs/guides/086_skill_run_observation_dashboard_usage.md#xid-4A4763A2DE63)
to inspect recorded progress, referenced knowledge, outputs, concerns, and
handoffs. It shows what was recorded and where observations are missing; you
decide whether the result is ready to use.

The [workflow walkthrough](docs/guides/087_workflow_protocol_sequence_for_humans.md#xid-E8B4D2F19A63)
explains how work moves from a request to verification and handoff.

## Choose your next step

- **Use existing procedures:** [Install and register Skill Packages](docs/guides/089_xrefkit_package_first_registration.md#xid-4F8C2A7D1E90).
- **Organize a task from your own instructions:** [Use an instruction-backed workflow](docs/guides/088_instruction_workflow_protocol.md#xid-9F4C2A7D1B60).
- **Capture your team's way of working:** [Understand Skills and Knowledge](docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8), then [author a Skill](docs/guides/013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B).
- **Explore the details:** [Browse the documentation](docs/000_index.md#xid-56DD6EB68343).

## Optional: explore model fit with Attention Pet

The experimental [Attention Pet](projects/attention-pet/README.en.md) companion
helps Codex users inspect estimates of model suitability and compare lower-cost
candidates using the visible work context. Run it from a Codex terminal in this repository:

```powershell
python -m xrefkit.attention_pet serve --port 8769
```

Open the printed address in the Codex browser panel. The preview follows the chat
that launched it. Its estimates are uncalibrated; it does not measure internal
attention or token usage, and it does not change your model settings.

## Contribute or maintain a deployment

For local development, install this checkout with `python -m pip install -e .`.
The [pipeline dependency reference](docs/reference/125_pipeline_dependency_matrix.md#xid-7E4B19C2A860)
describes CI and publication triggers. Internal authoring and runtime details are
in the [SkillDefinition contract](docs/core/contracts/096_skill_definition_contract.md#xid-E6A19D4B72C3)
and [Workflow Runtime Binding contract](docs/core/contracts/111_workflow_runtime_binding.md#xid-8D50A972BA9F).

XRefKit does not require provider API keys to install or explore the package.
Authenticate your AI tool through its provider's supported methods, and keep
secrets and access tokens out of the repository.
