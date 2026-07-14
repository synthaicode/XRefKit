<!-- xid: 32B512763C78 -->
<a id="xid-32B512763C78"></a>

# Knowledge Observation and Improvement Platform Design

## Status

This page defines the current product direction and an initial design boundary.
It does not claim that the platform, OTel adapters, or the analysis Skills are
implemented.

## Direction

XRefKit is intended to evolve from a Knowledge distribution and governance base
into a Knowledge observation and improvement platform.

The platform assumes that AI agents can emit standard execution traces, such
as OpenTelemetry traces. Collection, propagation, storage, and visualization
remain the responsibility of the existing tracing ecosystem. XRefKit adds the
Knowledge-level semantics needed to interpret those traces and return the
result to Knowledge configuration management.

The objective is the smallest sufficient Knowledge for correct judgment. Token
consumption is a proxy for deviation from that objective, not the product goal.

```text
Knowledge
    -> distribution through XRefKit MCP
AI agent
    -> execution trace
Knowledge analysis
    -> improvement proposal (AI work)
Knowledge improvement
    -> adoption decision (CAB work)
Knowledge (revised)
```

## Boundary And Responsibility

XRefKit does not become an independent tracing or APM product. Its boundary is
the meaning of Knowledge assets in an execution trace.

| Concern | Responsibility |
|---|---|
| Trace collection, propagation, storage, and visualization | OTel and existing observability infrastructure |
| Knowledge discovery and delivery | XRefKit MCP |
| XID-level trace normalization | XRefKit's thin, volatile host adapters |
| Trace interpretation and improvement proposal generation | XRefKit analysis Skills |
| Adoption of a canonical change | Human CAB or equivalent accountable authority |
| Canonical Skill / Knowledge modification | Approved repository change path |

The MCP boundary is both a distribution boundary and an audit boundary. A
Knowledge retrieval call such as `get_document_by_xid(xid=...)` already exposes
the asset identity as structured call data. The design therefore does not
introduce a second proprietary monitoring protocol.

## Observation Subject

The observation subject is the Knowledge asset, not the MCP server or tool.
Infrastructure metrics remain useful, but they answer a different question.
XRefKit answers which Knowledge was selected, loaded, and used in a judgment.

The minimum Knowledge-level observation model distinguishes these states:

- referenced or offered
- resolved by the distribution boundary
- loaded into agent context
- used as evidence or judgment basis
- missing from the record

Candidate measurements include:

- use counts by XID
- resolved or loaded Knowledge that has no recorded use
- repeated retrieval of the same XID within one execution
- XIDs frequently retrieved together
- token and cache observations attributed by XID where the host trace supports it

Missing records must remain distinct from non-use. An absent `loaded` or `used`
event is an observation gap until the client and host recording contract proves
otherwise.

## XID And Trace Mapping

XID is the stable identity for following a Knowledge asset across distribution,
execution, and improvement cycles. The intended mapping is a small extension on
top of the applicable MCP semantic conventions:

```text
xrefkit.xid = <Knowledge XID>
```

Host-specific logs are normalized into spans or span-linked records by thin
adapters. Adapter implementations are volatile because VS Code, Claude Code,
Codex, and other hosts may change their log shapes. The XID semantic contract
must remain stable while adapter code can be replaced independently.

The mapping must preserve the distinction between retrieval, context loading,
and actual application. It must also carry enough correlation data to join the
agent execution trace with the MCP audit record without making an inference
about the agent's private reasoning.

## Initial Analysis Scope

The first analysis Skills are limited to findings that can be detected from
trace evidence and lead directly to a concrete improvement candidate:

1. **Retrieved but unused Knowledge**: an asset was made available or loaded,
   but no use/application record connects it to the execution. This is
   analogous to linker garbage collection, while remaining subject to the
   missing-record rule above.
2. **Duplicate retrieval**: the same Knowledge was retrieved repeatedly in one
   execution or across an otherwise continuous retrieval path. This is a
   signal for missing includes, ineffective caching, or an unsuitable asset
   boundary.

The initial scope excludes causal claims about business success. It also does
not treat frequency rankings as quality rankings. Frequently used Knowledge is
not automatically good Knowledge, and low token use is not automatically a
correct result.

Token metrics are asymmetric: excess, duplication, and deep retrieval paths
can appear in token usage, while insufficient Knowledge generally appears as a
failed or unsafe outcome. Any tuning process must therefore prevent token
reduction from becoming a proxy objective that systematically removes needed
Knowledge.

## Knowledge Tuning Loop

An analysis Skill may produce proposals concerning:

- oversized or underspecified Knowledge
- duplicate retrieval
- deep retrieval paths
- cache effectiveness
- Knowledge granularity and includes
- XID structure and attribution
- routing, loading, or application recording

Proposal generation is AI work. Changing a canonical Skill, Knowledge page,
catalog, or routing rule is business work and therefore crosses a write path.
The write path requires a closure gate:

1. collect and normalize trace evidence;
2. generate a bounded improvement proposal;
3. record evidence, unknowns, affected XIDs, and expected verification;
4. obtain CAB or equivalent human adoption judgment;
5. apply the approved canonical change through the repository workflow;
6. validate and redistribute the revised version;
7. observe the next executions.

AI must not rewrite canonical Knowledge directly from a dashboard finding.
Evidence supports a decision; it is not itself an instruction for automatic
revision.

## Domain Scope

The abstraction is not limited to software development. Any domain that
distributes referenceable formal Knowledge and has structured agent execution
can use the same model, including policies, operating manuals, compliance
documents, support Knowledge bases, and onboarding material.

In regulated or otherwise accountable domains, the human adoption gate is a
required control. It is not an optional product feature.

## Category Position

The strategic differentiation is semantic rather than infrastructural:

- distribution control: what Knowledge may be referenced;
- audit evidence: what Knowledge was referenced and at which stage;
- freshness control: how observed use returns to Knowledge maintenance.

The intended category position is a Knowledge operations layer for AI agents,
using existing trace infrastructure and exposing stable vocabulary and
contracts such as XID identity, inert Knowledge boundaries, trace mapping, and
human adoption gates.

## Not In Initial Scope

- building an OTel collector, storage backend, or visualization product;
- replacing existing MCP semantic conventions;
- inferring agent intent or private reasoning from traces;
- claiming outcome causality from Knowledge usage alone;
- automatic canonical Knowledge rewriting;
- a universal host-log parser with a stable implementation promise.

## Open Design Decisions

The following are implementation decisions, not settled facts of this page:

- the exact `xrefkit.*` attribute and event vocabulary;
- the correlation contract between host spans, MCP audit records, and XRefKit
  run records;
- the definition and evidence requirements for `used` or `applied`;
- the token and cache attribution fields available from each host;
- the first host adapters and their replacement/versioning policy;
- the analysis Skill contracts and the CAB handoff schema.

These decisions must be resolved through the repository's normal design,
evidence, verification, and human acceptance paths before implementation is
treated as canonical platform behavior.

## Related

- [XRefKit v2 MVP](../xrefkit-v2-mvp.md#xid-E179D62EA4F4)
- [Skill Run Observation Dashboard Usage](../guides/086_skill_run_observation_dashboard_usage.md#xid-4A4763A2DE63)
- [Workflow Protocol Sequence For Humans](../guides/087_workflow_protocol_sequence_for_humans.md#xid-E8B4D2F19A63)
- [Skill and Knowledge Operating Model](../core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Document Update Policy](../policies/074_document_update_policy.md#xid-B1D42A6F90C3)
