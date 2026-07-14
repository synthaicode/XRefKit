<!-- xid: B6E4A91C7D2F -->
<a id="xid-B6E4A91C7D2F"></a>

# Copilot Trace Skill Boundary Analysis Design

## Status and decision

This page defines the current design for analyzing GitHub Copilot execution
evidence together with XRefKit Skill Run, MCP, and Knowledge evidence. The
The first deterministic MVP is implemented as
`xrefkit analysis boundary report`: it consumes an exported `dashboard data`
JSON document and emits a proposal-only Markdown/JSON report. Copilot OTel and
Debug Log adapters, richer trace normalization, and generative analysis Skills
remain future implementation phases.

The design extends the platform boundary in [Knowledge observation and
improvement platform design](088_knowledge_observation_and_improvement_platform_design.md#xid-32B512763C78):

- the host produces telemetry;
- a thin host adapter normalizes telemetry into XRefKit evidence;
- XRefKit correlates evidence with Skill XIDs, Knowledge XIDs, MCP sessions,
  and repository state;
- analysis produces bounded observations and split/merge candidates;
- a human owner decides whether a canonical Skill or Knowledge change is made.

The analyzer does not rewrite canonical Skills, infer private model reasoning,
or treat token reduction as the product objective. Token and cache data are
operational evidence used alongside responsibility, workflow, Knowledge, and
quality evidence.

## Problem to solve

XRefKit already records repository-native Skill Run progression, MCP
correlation, Knowledge observations, artifacts, concerns, handoffs, closure,
and optional token totals. The host-side Copilot telemetry can add the missing
execution view:

- one AI invocation and its child model calls;
- input, output, cache-read, and cache-creation token measurements;
- MCP tool-call identity, duration, result status, and trace relationships;
- the session and model context in which a Skill was used.

The combined evidence can answer questions such as:

1. Which Skill XIDs and Knowledge XIDs were offered, resolved, loaded, and
   applied during a run?
2. Which tool calls and model turns are repeated, unproductive, or
   uncorrelated?
3. Does a Skill contain independent responsibility or workflow clusters that
   should be split?
4. Do two Skills repeatedly share the same responsibility, Knowledge, tools,
   outputs, and quality gate such that a merge is worth considering?
5. Did a proposed boundary change improve routing and quality without merely
   moving cost or removing necessary context?

The output is evidence for a design decision, not an automatic decision.

## Scope

### Included

- VS Code GitHub Copilot OpenTelemetry file or OTLP exports;
- VS Code Agent Debug Log exports when approved and available;
- a versioned Python adapter for host-specific telemetry;
- correlation with XRefKit `run_id`, Skill XID, MCP session, repository
  fingerprint, and commit;
- raw and normalized token/cache measurements;
- MCP tool-call and server-receipt evidence;
- XID-level Knowledge and Skill boundary observations;
- deterministic aggregation, reports, dashboards, and review packets;
- retention, privacy, failure handling, reprocessing, and change verification.

### Excluded

- operating an OTel collector, trace database, or visualization platform;
- replacing the OpenTelemetry semantic convention;
- treating a client-side tool span as proof that an MCP server completed the
  request;
- reconstructing private reasoning or hidden prompts when content capture is
  disabled;
- attributing every token to one Knowledge XID when the host only reports
  aggregate usage;
- billing or cost accounting without an explicit provider pricing source;
- automatic Skill split, merge, deletion, or canonical document rewrite;
- making one universal parser for every AI host;
- using a workflow hook to bypass the repository Skill Run protocol.

## Governing boundaries

| Boundary | Owner | Contract |
| --- | --- | --- |
| Copilot host | VS Code/Copilot | Emits traces, metrics, events, or debug evidence according to the host configuration. |
| Telemetry transport and storage | Existing OTel or local storage | Collects and retains raw evidence; it is not XRefKit Knowledge. |
| Copilot adapter | XRefKit tool package | Converts one host schema into a stable, redacted XRefKit observation schema. |
| XRefKit runtime | XRefKit | Creates Skill Run envelopes, records MCP correlation, validates progression, and preserves repository identity. |
| Analysis | Analysis Skill/tool | Computes derived measurements and proposes observations with evidence and unknowns. |
| Quality review | Quality Reviewer Skill | Checks analysis procedure, coverage, counterevidence, and reproducibility. |
| Decision | Accountable human/CAB | Accepts, rejects, defers, or scopes a canonical Skill/Knowledge change. |
| Canonical change | Repository workflow | Changes Skill, Knowledge, routing, or workflow files through normal review and Git history. |

The adapter and analysis output are volatile evidence. Canonical Knowledge
contains the accepted rule or design, not unreviewed raw traces or a hidden
model-generated conclusion.

## Evidence sources

### Primary source: Copilot OpenTelemetry

VS Code documents an `invoke_agent` span for an agent session, `chat` spans
for model calls, and `execute_tool` spans for individual tool invocations.
The documented attributes include model identity, input/output token usage,
cache-read and cache-creation input tokens, tool name/type/call ID, and MCP
server/tool identifiers. See the official
[VS Code agent monitoring guide](https://code.visualstudio.com/docs/agents/guides/monitoring-agents).

The adapter must preserve the source span hierarchy and source attributes.
It must not flatten a cumulative session measurement into a per-turn value
without recording the measurement scope.

### Diagnostic source: Agent Debug Log

The VS Code Agent Debug Log can expose chronological LLM requests, tool calls,
prompts, responses, errors, and a session summary. It can also export a
session as OpenTelemetry JSON. See the official
[Chat Debug view guide](https://code.visualstudio.com/docs/agents/agent-troubleshooting/chat-debug-view).

Debug logs are a diagnostic and backfill source. Their internal file shape is
not the canonical XRefKit schema. The adapter must record `source_kind`, host
version, adapter version, and the reason the debug source was used.

### Fallback sources

Plain extension logs and MCP server output may explain an ingestion failure or
confirm server receipt, but they are not sufficient by themselves for exact
token attribution. MCP server logs are useful for the server-side half of a
tool-call correlation. The official
[MCP server guide](https://code.visualstudio.com/docs/agent-customization/mcp-servers)
describes how to inspect server output in VS Code.

## Collection policy

The recommended local collection profile is:

```json
{
  "github.copilot.chat.otel.enabled": true,
  "github.copilot.chat.otel.exporterType": "file",
  "github.copilot.chat.otel.captureContent": false
}
```

The exact exporter path is supplied through the host-supported configuration,
such as `COPILOT_OTEL_FILE_EXPORTER_PATH`, and is kept outside the repository
working tree unless a sanitized fixture is being prepared. OTLP HTTP or gRPC
may be used when an approved collector already exists.

Content capture remains disabled by default. If a troubleshooting case needs
prompt, response, tool argument, or tool result content, the operator must:

1. obtain the required approval;
2. limit collection to the smallest time window;
3. redact secrets and personal data before analysis;
4. mark the evidence as content-bearing;
5. apply the shorter retention policy.

The official monitoring guide warns that content capture can include sensitive
data. XRefKit must never require content capture for normal Skill boundary
analysis.

## End-to-end architecture

```text
Copilot session
    |
    | OTel JSONL/OTLP or approved Debug Log export
    v
Raw evidence quarantine
    |
    | schema validation, hash, deduplication, redaction, adapter version
    v
Normalized host events
    |
    | exact IDs + explicit correlation sidecar
    v
XRefKit correlation layer
    |-- Skill Run log: run_id, skill_id, phases, work, concerns, closure
    |-- MCP audit: mcp_session_id, repository_fingerprint, tool evidence
    |-- Knowledge records: searched, loaded, applied XIDs
    v
Run and boundary aggregates
    |
    | metrics, co-occurrence graph, counterevidence, unknowns
    v
Observation and proposal report
    |
    | quality review -> accountable human decision
    v
Approved repository change
    |
    | verify, publish, observe the next sample
    `----------------------------------------------'
```

The raw layer, normalized evidence layer, and canonical repository layer are
separate. A report can reference a raw evidence hash and a normalized record
without embedding the raw prompt or full tool result.

## Correlation contract

### Required identity fields

Every normalized record carries the following fields, with `null` or an
explicit unknown state when the source does not provide them:

| Field | Meaning |
| --- | --- |
| `evidence_id` | Stable ID for the normalized event or aggregate. |
| `source_kind` | `copilot_otel`, `copilot_debug`, `mcp_server_log`, or `xrefkit_run`. |
| `source_file_hash` | Hash of the immutable source artifact. |
| `adapter_version` | Parser and normalization version. |
| `event_time` | Source timestamp and timezone/clock-quality state. |
| `trace_id`, `span_id`, `parent_span_id` | OTel relationship when present. |
| `copilot_session_id` | Host session identity when present. |
| `conversation_id` | `gen_ai.conversation.id` when present. |
| `xrefkit_run_id` | XRefKit Skill Run UUID when explicitly bound. |
| `skill_xid`, `skill_id` | Skill identity from the XRefKit run, not guessed from text. |
| `mcp_session_id` | MCP session identity returned by the XRefKit correlation flow. |
| `repository_fingerprint` | Repository identity used by XRefKit. |
| `repository_commit` | Commit or worktree state associated with the run. |
| `correlation_status` | `exact`, `bounded`, `heuristic`, or `unknown`. |

The minimum exact binding is an XRefKit `run_id` plus a Copilot session or
trace identity recorded in an explicit sidecar. A timestamp-only match is
never exact.

### Correlation levels

1. `exact`: an explicit sidecar or shared instrumentation binds the Copilot
   session/trace to one XRefKit `run_id`, and repository identity agrees.
2. `bounded`: the session, repository, and time window agree, but a direct
   `run_id` binding is absent. The result may inform diagnostics but cannot
   support an automatic boundary change.
3. `heuristic`: only weak evidence such as time, user session, or tool name is
   available. Keep it visible as a hypothesis and exclude it from baseline
   totals.
4. `unknown`: the record cannot be safely assigned. Quarantine or report it;
   do not force a Skill or XID assignment.

The current XRefKit CLI already supports a caller-supplied `run_id`, MCP
correlation through `xrefkit skill correlate`, and informational token
recording through `xrefkit skill tokens`. A future Copilot adapter may add a
dedicated correlation command or sidecar schema; until then, it must not
pretend that a Copilot trace contains an XRefKit `run_id`.

### Proposed correlation sidecar

The sidecar is a small, content-free artifact written next to the run evidence:

```json
{
  "schema": "xrefkit.copilot.correlation/v1",
  "xrefkit_run_id": "00000000-0000-0000-0000-000000000000",
  "skill_xid": "<skill-xid>",
  "mcp_session_id": "<mcp-session-id>",
  "repository_fingerprint": "<fingerprint>",
  "repository_commit": "<commit-or-worktree-state>",
  "copilot_session_id": "<session-id>",
  "conversation_id": "<conversation-id-or-null>",
  "trace_ids": ["<trace-id>"],
  "created_at": "<iso-8601>",
  "operator": "<non-secret-operator-id>",
  "correlation_status": "exact"
}
```

The sidecar contains identifiers only. It does not copy prompts, responses,
tool arguments, or tool results. If the host cannot expose a stable session or
trace ID, the sidecar records `unknown` rather than manufacturing one.

## Normalized event model

The Python tool should normalize into a small event model and retain the
source payload separately. The following logical entities are sufficient for
the first implementation:

| Entity | Important fields | Use |
| --- | --- | --- |
| `SkillRun` | run ID, Skill XID, task hash, phases, work items, artifacts, concerns, handoffs, closure | Repository-native execution boundary. |
| `ModelTurn` | trace/span, model, turn index, duration, finish reason, token usage | Model-call and cumulative-token analysis. |
| `TokenUsage` | input, output, cache-read, cache-creation, reasoning-output, scope, source | Raw accounting without double counting. |
| `ToolCall` | call ID, MCP server/tool, parent span, duration, status, server receipt | Tool graph and MCP interface analysis. |
| `KnowledgeEvent` | XID, content hash, action, phase, source | Offered/resolved/loaded/applied/unused evidence. |
| `OutcomeEvent` | artifact, work item, concern, quality result, handoff, closure | Responsibility and quality evidence. |
| `BoundaryObservation` | subject XIDs, window, support, evidence refs, unknowns, proposal, decision | Reviewable split/merge candidate. |

### Token and cache normalization

The source record must preserve these values independently:

```text
input_tokens_raw
output_tokens_raw
cache_read_input_tokens_raw
cache_creation_input_tokens_raw
reasoning_output_tokens_raw
measurement_scope = turn | session_cumulative | invocation_total | unknown
provider_semantics = explicit | documented_inferred | unknown
```

The analyzer must apply the following rules:

- do not add cache-read or cache-creation values to `input_tokens_raw` unless
  the provider semantics explicitly require that interpretation;
- do not sum child `chat` spans and an enclosing `invoke_agent` total;
- do not sum cumulative snapshots as if they were per-turn deltas;
- compute a delta only when the sequence is monotonic, ordered, and has one
  known measurement scope;
- retain raw values even when a normalized total is unavailable;
- mark the total as `unknown` when the source semantics are ambiguous;
- keep token counts separate from captured byte sizes and XRefKit Knowledge
  content sizes;
- do not convert tokens to money without a separately versioned pricing
  source.

This permits a report to say “cache-read input was reported as 42,000 tokens”
without claiming that 42,000 tokens were newly transmitted or that they can
be assigned to one Skill document.

### XID-level Knowledge semantics

The normalized Knowledge state follows the platform design and keeps these
events distinct:

```text
offered -> resolved -> loaded -> applied
                 \-> missing
loaded ----------> unused
resolved --------> duplicate_retrieval
```

The analyzer may attribute a token or byte count to an XID only when the
assembly or host evidence provides an explicit attribution. Otherwise it
reports run-level usage and XID-level state separately.

## Payload and tool surface policy

The analysis system must not recreate the payload growth problem it is
measuring.

- Raw telemetry stays in the evidence store; model-facing reports contain
  aggregates, XIDs, hashes, and short evidence references.
- Tool discovery returns the minimum metadata needed for the current analysis;
  full tool schemas or full documents are fetched only after an XID/capability
  decision.
- A report should reference `skill_xid`, `knowledge_xid`, `trace_id`, and
  `evidence_id` rather than copying their complete bodies.
- Repeated XID content with the same repository fingerprint and content hash
  is referenced from the active context instead of being injected again.
- Captured prompt or tool content is opt-in, redacted, access-controlled, and
  never required for the normal boundary decision.

The analyzer therefore measures payload and cache behavior while preserving the
same XID-first, deferred-detail behavior required by the runtime.

## Skill boundary analysis

### Analysis unit

The primary unit is a tuple:

```text
(skill_xid, skill_run_id, repository_fingerprint, analysis_window)
```

The secondary unit is a pair of Skill XIDs or Knowledge XIDs observed in the
same bounded population. A Skill XID is not merged merely because its text is
similar to another document. Responsibility, authority, workflow, Knowledge,
tool use, artifacts, concerns, and quality ownership are all required inputs.

### Features collected per run

- selected Skill and routing candidates;
- task and input class, represented by a redacted hash or controlled label;
- Skill phase sequence and handoff direction;
- Knowledge XIDs searched, resolved, loaded, applied, missing, duplicated, or
  left unused;
- MCP server/tool sequence, retries, failures, duration, and server receipt;
- model turns, model identity, raw token fields, cache fields, and measurement
  scope;
- work items, artifacts, concerns, judgment significance, quality result, and
  closure state;
- repository fingerprint, commit, adapter version, and correlation status.

### Split candidates

A split candidate is stronger when several independent signals agree:

- repeated clusters of tasks select different Knowledge and tool subsets;
- the clusters have different outputs, artifacts, risks, or quality gates;
- the clusters have different authority or escalation boundaries;
- one cluster can be executed and verified without the other;
- users or routing evidence repeatedly enter through different intents;
- the current Skill causes avoidable context or handoff overhead between the
  clusters.

The report must identify the proposed child responsibilities, required shared
Knowledge, routing rule, handoff contract, and verification plan. A high token
count alone is not split evidence.

### Merge candidates

A merge candidate is stronger when several independent signals agree:

- two Skills are selected together for the same bounded task population;
- they use the same authority, risk, escalation, and quality owner;
- their Knowledge and tool sets substantially overlap;
- their outputs and closure conditions are the same;
- separate routing creates duplicate loading, repeated explanation, or
  unnecessary handoff without a meaningful control boundary;
- a single Skill can preserve the two responsibilities without creating an
  ambiguous operating contract.

Frequent co-occurrence is not sufficient for a merge. A separate approval,
security, data, or quality boundary is counterevidence even when the token and
tool profiles look similar.

### Evidence weighting

The tool should calculate descriptive support, not hide a universal threshold:

```text
support = sample_count
correlation_quality = exact / bounded / heuristic / unknown distribution
boundary_evidence = responsibility + workflow + knowledge + tool + outcome signals
counterevidence = risk, authority, quality, missing data, or regression signal
confidence = support + correlation_quality + boundary_evidence - counterevidence
```

The weights and minimum sample size are configuration owned by the analysis
Skill and must be visible in every report. Until a baseline is established,
the tool should show ranked candidates and confidence bands rather than a
binary “merge” or “split” verdict.

## Analysis output contract

Every candidate report contains:

1. analysis ID, source hashes, time window, repository fingerprint, commit
   range, adapter version, and configuration version;
2. sample count and correlation-quality distribution;
3. raw token/cache totals with measurement scope and provider semantics;
4. tool and Knowledge usage summaries;
5. Skill/Knowledge XIDs affected and their content hashes;
6. proposed split or merge boundary;
7. supporting evidence references and counterevidence;
8. unknowns, data-quality failures, and excluded samples;
9. expected benefits and risks, without claiming causality;
10. human decision, owner, due date, and verification plan.

Example logical record:

```json
{
  "schema": "xrefkit.boundary_observation/v1",
  "observation_id": "<stable-observation-id>",
  "subject_xids": ["<skill-xid-a>", "<skill-xid-b>"],
  "proposal": "split | merge | keep | investigate",
  "analysis_window": {"from": "<iso-8601>", "to": "<iso-8601>"},
  "sample_count": 24,
  "correlation": {"exact": 20, "bounded": 3, "heuristic": 1, "unknown": 0},
  "tokens": {
    "input_raw": 120000,
    "output_raw": 18000,
    "cache_read_raw": 70000,
    "cache_creation_raw": 4000,
    "scope": "turn",
    "provider_semantics": "explicit"
  },
  "evidence_refs": ["<normalized-evidence-id>"],
  "counterevidence": ["<reason-not-to-merge>"],
  "unknowns": ["per-xid-token-attribution-unavailable"],
  "decision": {"status": "pending", "owner": "<human-owner>"},
  "verification_plan": ["run the pre-change and post-change sample comparison"]
}
```

The example values are illustrative only. A generated report must never fill
unknown values with zero or invent an attribution.

## Operational workflow

### One-time setup

1. Choose the approved Copilot telemetry mode: local file, approved OTLP
   collector, or controlled Debug Log export.
2. Configure content capture off and define the evidence directory, access
   group, retention, and deletion owner.
3. Pin the adapter version and record the host, Copilot extension, VS Code,
   Python, and XRefKit versions.
4. Create a redacted fixture from one known Skill Run and validate the parser.
5. Define the analysis Skill configuration: time window, minimum sample,
   allowed sources, thresholds, and reviewer.
6. Confirm that the repository fingerprint and XRefKit startup contract are
   resolved before any canonical analysis is run.

### Per Skill Run

The existing Skill Run protocol remains the operational spine:

```powershell
python -m xrefkit skill run --root . --meta <skill-meta.md> --task-file <task.txt> --run-id <uuid> --json
python -m xrefkit skill correlate --log <run-log.md> --run-id <uuid> --mcp-session-id <id> --repository-fingerprint <fingerprint> --json
python -m xrefkit skill tokens --log <run-log.md> --input <n> --output <n> --total <n> --note "source=<provider>;scope=<scope>" --json
python -m xrefkit skill verify --log <run-log.md> --json
python -m xrefkit skill close --log <run-log.md> --json
```

The commands above are existing XRefKit operations. The Copilot adapter adds
the following sidecar and evidence steps around them:

1. record the Copilot session/trace identity after the session starts;
2. write the content-free correlation sidecar;
3. preserve the raw export outside the canonical document tree;
4. import and normalize the export after the run;
5. link the normalized evidence to the Skill Run and MCP audit records;
6. record an unknown state when any link cannot be proved.

`xrefkit skill verify` remains a progression check. It is not a quality check
and it does not certify the split/merge conclusion.

### Ingestion runbook

The proposed Python tool performs these steps in order:

1. **Acquire**: copy or read the source without changing it; record path,
   source hash, byte size, and acquisition time.
2. **Identify**: detect OTel JSONL, OTLP JSON, Debug Log export, or fallback
   text; reject an unknown format into quarantine.
3. **Validate**: check required IDs and timestamps; retain unknown attributes;
   report schema drift instead of silently dropping fields.
4. **Redact**: apply configured secret and personal-data rules before a
   normalized record becomes reviewable.
5. **Normalize**: emit versioned events and preserve source offsets or span
   references for audit.
6. **Deduplicate**: use source hash plus event/trace/span identity; never
   duplicate a cumulative token snapshot.
7. **Correlate**: apply the sidecar and XRefKit run/MCP evidence; assign the
   explicit correlation level.
8. **Aggregate**: calculate run, Skill, Knowledge, MCP, token, cache, and
   outcome views.
9. **Analyze**: generate ranked observations with supporting and opposing
   evidence.
10. **Review**: send the report to the quality reviewer and accountable owner;
    keep the decision separate from the generated candidate.

### Recurring operation

| Cadence | Operation | Exit evidence |
| --- | --- | --- |
| Per run | Capture, correlate, normalize, and close the Skill Run | Run log, sidecar, source hash, normalization result |
| Daily or per batch | Inspect ingestion failures, unknown correlation, and data-quality drift | Intake status report and quarantined-item list |
| Weekly | Review top split/merge candidates and counterevidence | Human decision or explicit defer/escalate record |
| Per accepted change | Update canonical Skill/Knowledge/routing and run repository checks | Git diff, review, verification, and handoff |
| After the change | Compare a bounded pre/post sample | Outcome report with regression and quality checks |
| Monthly | Review adapter, retention, access, and threshold configuration | Operations review record |

The schedule is a deployment choice. It must not turn an unreviewed analysis
report into an automatic repository mutation.

## Python tool surface

The dashboard-backed boundary report is implemented. The dashboard HTML
`Analysis` tab renders the same proposal-only result included in the dashboard
payload. The Copilot ingestion and pre/post comparison commands remain proposed
interfaces:

```text
# Implemented MVP
python -m xrefkit dashboard data --root . > work/reports/dashboard-observation.json
python -m xrefkit analysis boundary report --input work/reports/dashboard-observation.json --out work/reports/boundary-observation.md

# Proposed future interfaces
python -m xrefkit analysis copilot validate --input <raw-export>
python -m xrefkit analysis copilot ingest --input <raw-export> --out <evidence-dir>
python -m xrefkit analysis copilot correlate --evidence <evidence-dir> --sidecar <sidecar.json>
python -m xrefkit analysis boundary compare --before <report> --after <report> --out <comparison.md>
```

The implementation should be a library-first Python package with:

- immutable source readers;
- one adapter module per host/export shape;
- typed normalized models;
- deterministic aggregation functions;
- a report renderer that never hides unknowns;
- fixture-based tests for each source shape;
- a CLI that can emit JSON for automation and Markdown for human review.

The MVP is intentionally limited to the dashboard JSON contract. It produces
deterministic usage summaries and conservative split, merge, correction, and
investigation candidates. It is not itself a generative AI reviewer and it
does not edit canonical files.

The package may be distributed separately from the XRefKit repository, but
the normalized schema and adapter version must remain compatible with the
repository contract. Distribution or HTTP/PyPI delivery must not be used to
silently replace a canonical Skill or bypass the repository review workflow.

## Quality, safety, and retention

### Data classes

| Class | Examples | Default treatment |
| --- | --- | --- |
| Identity | trace IDs, run IDs, repository fingerprint | Keep in normalized evidence; access controlled. |
| Usage metadata | model, tokens, cache counts, tool names, durations | Keep for analysis; aggregate before model-facing use. |
| Content | prompts, responses, tool args/results, file paths | Off by default; redact and shorten retention when enabled. |
| Canonical knowledge | approved Skill/Knowledge text | Keep in repository; reference by XID and content hash. |

Raw evidence is immutable, access-controlled, and retained only for the
defined analysis window plus the audit period. Normalized evidence contains
the minimum fields needed to reproduce the report. Canonical docs never store
secrets, raw prompts, or full Copilot transcripts.

### Data-quality gates

An analysis report must fail closed for decision purposes when any of these
conditions hold:

- source schema cannot be identified;
- duplicate or cumulative token records cannot be distinguished;
- repository or Skill identity is contradictory;
- the correlation rate is below the configured minimum;
- content redaction has not completed for a content-bearing source;
- an adapter version is missing or unsupported;
- a proposed change has no counterevidence section or verification plan.

Failure means “not decision-ready”, not “no usage occurred”. The report keeps
the failure reason and routes it to investigation.

### Recovery and reprocessing

- quarantine malformed or sensitive inputs without deleting the source hash;
- rerun normalization with a newer adapter against the same immutable source;
- keep analysis configuration and adapter version in every report;
- invalidate derived aggregates when their source or schema version changes;
- never patch a normalized record in place without a new evidence version;
- use Git history for accepted canonical changes and `work/` records for
  operational execution history.

## Operating metrics

The operations dashboard should show data quality and decision quality in
separate panels.

### Collection and correlation

```text
parse_success_rate = valid_sources / acquired_sources
exact_correlation_rate = exact_records / eligible_records
unknown_correlation_rate = unknown_records / acquired_records
server_receipt_rate = records_with_server_receipt / client_tool_calls
deduplication_rate = duplicate_events / acquired_events
```

### Analysis quality

- sample count and source coverage by Skill XID;
- proportion of reports with explicit counterevidence and unknowns;
- reviewer acceptance, rejection, defer, and escalation counts;
- post-change regression and rework rate;
- routing success and quality-gate outcomes before and after a change.

### Token and cache observation

- input/output/cache-read/cache-creation raw totals by source and scope;
- model turns and tool calls per run;
- repeated XID retrieval and duplicate context injection;
- payload byte sizes when measured by the assembly layer.

Token totals are diagnostic indicators. The primary success measure is a
clearer, safer, correctly routed Skill/Knowledge boundary with maintained
quality and traceability.

## Failure modes and responses

| Failure | Detection | Response |
| --- | --- | --- |
| OTel disabled or no export | No source artifact or empty export | Record collection gap; use approved Debug Log only if available. |
| Content capture disabled | No prompt/tool body fields | Continue metadata analysis; do not infer missing content. |
| Host schema drift | Unknown event or attribute rate rises | Quarantine affected records and add a fixture before promotion. |
| Cumulative token snapshots | Scope or monotonicity check fails | Preserve raw snapshots; mark normalized delta unknown. |
| Client tool call without server receipt | No MCP audit/server event | Mark invocation observed but completion unconfirmed. |
| Multiple runs share one Copilot session | Sidecar maps ambiguously | Split the session only with explicit run boundaries; otherwise exclude from exact totals. |
| Missing Skill or Knowledge XID | XRefKit record does not resolve | Keep the source identity and report an unresolved XID; do not create a replacement. |
| Adapter parser bug | Fixture or invariant test fails | Stop promotion, retain source hash, rerun after fix. |
| Candidate conflicts with authority/risk boundary | Reviewer counterevidence | `keep` or `investigate`; no merge. |
| Accepted change worsens quality | Post-change comparison | Revert or follow the repository change process and record the regression. |

## Decision and change workflow

1. The analysis tool writes a `BoundaryObservation` report and references
   affected XIDs, source hashes, and run records.
2. The analysis Skill records unknowns, counterevidence, and a verification
   plan. It does not edit a Skill or Knowledge page.
3. The quality reviewer checks source coverage, correlation, token scope,
   deduplication, interpretation, and reproducibility.
4. The accountable human accepts, rejects, defers, or escalates the proposal.
5. If accepted, a normal XRefKit authoring workflow changes the Skill,
   Knowledge, routing, or workflow definition. New XIDs are created only when
   the repository identity boundary requires them; content edits preserve the
   existing XID.
6. Repository xref, Skill, Knowledge, test, and quality checks run before
   publication.
7. The change is observed on a bounded canary/sample and compared with the
   pre-change report.
8. The run is closed with artifacts, evidence, concerns, quality result, and
   handoff/decision status.

The decision record belongs in the appropriate repository work record or
canonical register. Do not add an ADR for this flow; the repository document
policy assigns history to Git and operational history to `work/` records.

## Implementation phases

### Phase 1: deterministic MVP

- define `xrefkit.copilot.correlation/v1` and
  `xrefkit.boundary_observation/v1`;
- implement a redacted VS Code OTel JSONL reader;
- preserve OTel span hierarchy and raw token/cache scope;
- implement exact, bounded, heuristic, and unknown correlation;
- join existing `work/sessions/` and MCP audit evidence;
- render JSON and Markdown reports;
- add fixtures for cache fields, cumulative totals, MCP calls, missing IDs,
  deduplication, and schema drift;
- run the tool manually against a bounded sample.

### Phase 2: operational integration

- add the content-free sidecar writer/validator;
- add report status and data-quality views to the existing observation
  dashboard;
- add scheduled batch operation and retention checks;
- add a Debug Log adapter as a clearly labeled fallback;
- document access and deletion procedures.

### Phase 3: boundary decision support

- add configurable co-occurrence and responsibility features;
- add pre/post comparison reports;
- define an analysis Skill and its quality-review handoff;
- publish accepted observations through normal repository workflow;
- calibrate thresholds from reviewed samples rather than arbitrary defaults.

### Phase 4: additional hosts

Add another host adapter only after it produces the same normalized contract
and passes the same fixture, privacy, correlation, and token-scope tests.
Host-specific behavior stays in the adapter; XRefKit boundary semantics stay
in the shared analysis layer.

## Verification plan

The implementation is ready for controlled use only when all of the following
are true:

- the same immutable fixture produces the same normalized hash and report;
- malformed, unknown, and sensitive fields are handled explicitly;
- OTel parent/child spans do not double count tokens;
- cumulative token snapshots are not summed as turns;
- cache-read and cache-creation fields remain separately visible;
- client tool calls and server receipts are not conflated;
- exact and non-exact correlation are visibly separated;
- every candidate contains affected XIDs, counterevidence, unknowns, and a
  verification plan;
- no command edits canonical Skill or Knowledge files as a side effect;
- repository xref and quality checks pass for the design and implementation;
- a human can reproduce the report from the source hash, adapter version, and
  configuration version.

## Open implementation decisions

The following are intentionally open and must be decided in the analysis
Skill/tool contract before production use:

- the final `xrefkit.*` OTel attribute vocabulary;
- whether the correlation sidecar is created by the client, adapter, or
  `xrefkit skill correlate` extension;
- the normalized evidence storage location and retention period;
- the exact definition of `applied` Knowledge evidence;
- the minimum sample and threshold configuration;
- the permitted level of per-XID token attribution;
- the accountable owner and quality reviewer for each Skill family;
- the distribution and versioning policy for adapters delivered outside the
  repository.

No open decision may be silently resolved by treating an unknown value as
zero, a client event as server confirmation, or a candidate as an accepted
canonical rule.

## Related contracts and guides

- [Knowledge observation and improvement platform design](088_knowledge_observation_and_improvement_platform_design.md#xid-32B512763C78)
- [Workflow protocol sequence for humans](../guides/087_workflow_protocol_sequence_for_humans.md#xid-E8B4D2F19A63)
- [Skill Run Observation Dashboard usage](../guides/086_skill_run_observation_dashboard_usage.md#xid-4A4763A2DE63)
- [Skill operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [XRefKit startup contract](../core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22)
- [Document update policy](../policies/074_document_update_policy.md#xid-B1D42A6F90C3)
- [OpenTelemetry GenAI span conventions](https://github.com/open-telemetry/semantic-conventions/blob/main/model/gen-ai/spans.yaml)
- [OpenTelemetry GenAI token metrics](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-metrics.md)
