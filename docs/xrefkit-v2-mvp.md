<!-- xid: E179D62EA4F4 -->
<a id="xid-E179D62EA4F4"></a>

# XRefKit v2: Current Architecture and MVP Boundary

This document describes the current XRefKit architecture and the compatibility
surface retained from the original v2 package/resolver MVP. The repository has
grown beyond that first resolver-only prototype: the active runtime includes
Skill execution, workflow binding, MCP distribution, execution observation,
decision trace, local overlays, and human-controlled adoption paths.

## Purpose

XRefKit supplies referenceable Knowledge, executable Skill procedures, and
governance controls for AI work. Its central problem is judgment-material
resolution: make the relevant method, Knowledge, evidence, runtime boundary,
and unresolved conditions available without silently turning references into
authority or guesses into facts.

The current path is:

```text
instruction
  -> semantic Skill or workflow routing
  -> instruction-derived runtime binding
  -> on-demand XID Knowledge resolution
  -> client-side execution and observation
  -> deterministic checks and human adoption decision
```

Knowledge is supplied on demand. A resolved XID proves repository resolution;
it does not by itself prove that the body entered model context or that the
content was used as judgment evidence. Run records preserve those distinctions.

## Responsibility boundaries

### Core runtime

The Python runtime owns contracts, discovery, routing inputs, Skill Run and
workflow records, execution binding, XID resolution, deterministic checks,
MCP tool contracts, and observation surfaces. It does not decide the semantic
validity or business adoption of an output.

### Skill and Knowledge

Skill definitions carry executable procedure and Skill-specific boundaries.
Knowledge carries reusable evidence, rules, and domain criteria. Routing uses
the current instruction and catalog metadata; capability, tuning,
responsibility, and execution mode are derived for the work item at run time.
Knowledge bodies are loaded only for selected XIDs, with content hashes and
source trace retained in the resulting bundle or run record.

### Client and human boundary

The client or orchestrator performs the work after the runtime envelope and
execution binding succeed. It records execution observations and preserves
unknowns. A human remains accountable for output acceptance, canonical
Skill/Knowledge adoption, and other authority decisions.

## Runtime surfaces

The active runtime includes:

- `xrefkit skill run` for Skill-backed execution and `xrefkit workflow run` for
  instruction-backed work;
- execution binding that validates source mode, repository identity, Skill
  identity, work-item context, and MCP correlation;
- SkillDefinition v1 package assets plus legacy split `meta.md` / `SKILL.md`
  compatibility during migration;
- XID catalog, on-demand document and Knowledge resolution, and selected
  context construction;
- MCP stdio, SSE, and streamable HTTP server transports, startup context,
  protocol blocks, Skill distribution, local Skill edits, local Knowledge,
  contribution return, review, and adoption tools;
- workflow phases, work items, artifacts, concerns, verification, closure,
  reporting, and human evaluation records;
- dashboard data and proposal-only boundary analysis;
- decision-trace checkpoints, events, impact analysis, return checks, and
  human evaluation boundaries;
- goal-mode continuation packets, wake observations, and per-goal leases.

The MCP server distributes inert definitions and records boundary events. It
does not execute a Skill method or make the human adoption decision.

## Legacy package and resolver compatibility

The original v2 package model remains supported for compatibility and for
package-first distribution:

- a package can publish Skill definitions, entry text, reusable fragments,
  Knowledge, review axes, schemas, templates, and a `package_manifest.yaml`;
- Python entry points discover packages, but discovery does not enable a
  package for resolution until the package is explicitly selected;
- a Project Local manifest can extend a package Skill and add local Knowledge,
  templates, schemas, and review axes;
- the resolver builds an `EffectiveSkillBundle` with effective identity,
  inherited contracts, selected loaded text, available Knowledge metadata,
  required outputs, conflicts, and source trace;
- `referenced_xids`, `loaded_xids`, and `used_xids` remain distinct. Used XIDs
  are runtime evidence and must be loaded before they can be marked used.

The single-inheritance resolver and package registry are compatibility
surfaces. They do not replace the active MCP catalog, runtime binding, or
workflow protocols.

## Execution observation

Run logs and dashboard data are evidence of what the runtime observed. They
retain run identity, source hashes, XID references, loaded and used Knowledge,
work-item and phase state, artifacts, concerns, checks, closure, handoff, and
where available host or model observations.

The boundary-analysis command consumes dashboard JSON and produces a
deterministic proposal-only report. Host-specific Copilot telemetry adapters,
full OpenTelemetry normalization, and generative analysis Skills remain
separate future work. Observation does not authorize a canonical change.

## MCP and contribution boundary

MCP is both a distribution and audit boundary. Startup establishes the
repository identity and required context before guarded tools are available.
The server resolves XIDs and transfers selected definitions; the client keeps
the execution record and invokes returned client commands where required.

Local Skill edits preserve source identity and provenance without overwriting
existing edits. Local Knowledge is separately registered and exported. A
contribution return is staged, sealed, reviewed with human authority, and only
then adopted through the repository-owned transport boundary. Review, adoption,
publication, distribution, and live verification remain separate states.

## Goal-mode boundary

Goal mode now stores append-only continuation packets, explicit wake events,
and one active lease per goal. These records support safe later inspection and
prevent concurrent lease holders. Provider quota observation, automatic wake
scheduling, and automatic session re-entry remain outside the implemented
runtime.

## Compatibility and not-yet-complete work

Retained compatibility includes legacy split Skills, Skill Package discovery,
Project Local manifests, the single-inheritance resolver, and the original
effective-bundle/source-trace model. Current architecture adds the runtime and
MCP boundaries around those assets.

The following remain incomplete or intentionally bounded:

- automatic discovery-time package installation or activation; `xrefkit skills
  sync` remains an explicit administrator operation;
- multiple inheritance and general-purpose executable package code;
- automatic provider quota watcher and unattended goal re-entry;
- full host-specific Copilot OTel ingestion and universal host-log parsing;
- automatic semantic Skill merge, split, deletion, or canonical rewrite;
- automatic human approval or adoption of analysis proposals;
- causal claims about business outcomes from Knowledge usage alone.

These are boundaries of implementation, not instructions to infer missing
behavior. New capabilities must pass the relevant runtime, evidence, review,
and human adoption contracts before becoming canonical.

## Representative commands

```powershell
python -m xrefkit skill run --definition <path-to-SKILL.v1.md> --task "<task>" --capability "<capability>" --tuning "<tuning>" --responsibility "<responsibility>" --execution-mode <mode> --json
# Legacy split compatibility only:
python -m xrefkit skill run --meta <path-to-meta.md> --task "<task>" --json
python -m xrefkit workflow run --task "<task>" --completion-condition "<condition>" --json
python -m xrefkit xref search "<query>"
python -m xrefkit xref show <XID>
python -m xrefkit dashboard data --root .
python -m xrefkit analysis boundary report --input <dashboard-json> --out <report>
python -m xrefkit xref check
```
