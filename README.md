# XRefKit

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/xrefkit?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/xrefkit)

**Spend less effort keeping track of AI-assisted work, and focus on the decisions that need you.**

XRefKit is designed to reduce the cognitive load of working with AI: remembering
instructions, finding the relevant rules, reconstructing progress, and interpreting
results. Reusable procedures, linked evidence, and familiar reports give that
information a place outside your head, so you can focus on what needs judgment.

## Why AI-assisted work can become mentally demanding

Producing an answer is only part of the work. Someone still has to supply the
rules, follow progress, interpret the result, and decide what to accept. XRefKit
addresses recurring sources of that effort:

- **Instructions have to be remembered and repeated.** When the process lives in
  chat history, you have to reconstruct the steps and check what you forgot to
  explain. A reusable **Skill** keeps the procedure, inputs, outputs, and criteria
  available for the next task.
- **Relevant rules and evidence are scattered.** You have to find the right
  material and reconnect it to the task. Separate **Knowledge** records and stable
  document identifiers (**XIDs**) let a Skill resolve the material it needs and
  record references for review.
- **A new session or handoff loses the immediate context.** You have to work out
  what happened, what remains open, and where to resume. Explicit work items,
  progress, concerns, and handoff records provide a starting point without
  requiring everyone to reconstruct the conversation.
- **A completion message leaves the scope of checking unclear.** You have to
  determine which requirements were checked and which decisions remain yours.
  Workflow-record verification and closure checks expose missing records and
  unfinished items; reports distinguish those checks from output-quality review.
- **Reports change shape or leave their reasoning implicit.** You have to locate
  the conclusion, connect it to evidence, and discover its limits each time.
  Decision-oriented reporting and optional approved report profiles make those
  relationships and locations explicit, as described below.

For example, a recurring review can present its conclusion, relevant criteria,
evidence, and open questions in familiar places. The reader can focus on what
changed and what needs a decision, with supporting detail available when needed.

XRefKit checks the completeness and consistency of recorded work. People remain
responsible for judging whether the output is correct and suitable for its purpose.

## How does it fit with modern agent harnesses?

**XRefKit focuses on the human effort required to direct, understand, and review
agent work.** Reusable methods and reviewable records serve that purpose.

Modern harnesses already do much more than call a model. Anthropic's
[Managed Agents architecture](https://www.anthropic.com/engineering/managed-agents)
separates execution, durable sessions, and sandboxes. Its
[application-development harness](https://www.anthropic.com/engineering/harness-design-long-running-apps)
uses explicit evaluation criteria, independent evaluators, and structured handoffs.
OpenAI's [harness engineering approach](https://openai.com/index/harness-engineering/)
uses repository knowledge, execution plans, and automated constraints. These
examples overlap with XRefKit's goals.

XRefKit brings reusable procedures, separately maintained knowledge, explicit work
records, and reporting criteria into a shared working structure. Repository files
and Skill Packages preserve these assets; CLI/MCP interfaces expose them to
compatible clients. This gives the team a common basis for directing and reviewing
work when tasks, sessions, or supported clients change.

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

## Reports that reduce the effort of understanding

A report should help the reader form an accurate picture with less mental effort:

- **When the point is buried, the reader has to decide what matters.** Lead with
  the conclusion and what it means for the agreed decision, followed by the next
  action. Let the task determine the appropriate report shape.
- **When evidence and limits are detached, the reader has to rebuild the
  reasoning.** Link summary findings to supporting detail and place material
  uncertainty beside the conclusion it qualifies. Keep necessary conditions
  visible and supporting detail accessible.
- **When layout and detail vary, the reader has to relearn how to read each
  report.** For recurring outputs, opt into a target-specific **Knowledge quality
  profile** that preserves approved examples, sample inputs, headings, table
  structure, information placement, required detail, and criteria. Use that
  baseline for subsequent reviews, including after model or session changes.
- **When a familiar layout contains weak reasoning, the reader must still detect
  the gap.** Structural checks flag format differences; independent review checks
  meaning, readability, and whether the evidence supports the conclusion. A
  format pass must not stand in for that review.

Consider a recurring change-review report: readers can find the affected area,
finding, evidence, impact, and next action in the agreed places each time. If this
run lacks evidence for a conclusion, that limit belongs beside the conclusion;
passing the format check does not make it acceptable.

Feedback can then be directed to the part that needs attention: the current
output, missing inputs, unclear criteria, or the reusable procedure. Approved
examples and criteria remain the baseline; changing a procedure requires explicit
authorization. This connects **execution → evidence → report → human judgment →
authorized improvement**. Reader feedback can identify explanations, layouts, or
missing context that made a decision harder, and guide a scoped correction for the
next run.

Workflow-record completion, report format, substantive quality, and human
acceptance remain separate judgments. The controls support repeated review against
known conditions. Lower cognitive load is the design goal; its effect on readers,
decision quality, and rework still needs evaluation in actual use.
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
