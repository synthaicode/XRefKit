<!-- xid: 7A2F4C8D1401 -->
<a id="xid-7A2F4C8D1401"></a>

# LLM Review Knowledge Usage Rules

This page defines how an LLM may use its internal knowledge when executing review capabilities.

## Purpose

Prevent unsupported review judgments and keep local evidence ahead of model priors.

## Core Rule

- Review capabilities use LLM internal knowledge as a helper, not as primary evidence.
- Local evidence, repository evidence, and explicitly loaded domain knowledge take priority over model recall.

## Priority Order

1. Target artifacts:
   - code
   - diff
   - dependency list
   - measurement result
   - provenance data
2. Local evidence:
   - specification
   - design
   - coding rule
   - license policy
   - performance requirement
   - security requirement
3. Canonical knowledge:
   - `knowledge/` pages referenced by XID
4. LLM internal knowledge:
   - general language, framework, and engineering knowledge used only to interpret evidence or propose follow-up checks

## Allowed Uses of Internal Knowledge

- explain likely meaning of a framework construct
- suggest where supporting evidence should exist
- identify common risk patterns to verify in local artifacts
- help map local evidence to a review criterion

## Disallowed Uses of Internal Knowledge

- treating model recall as proof that a local implementation is correct
- asserting performance, security, or license compliance without supporting evidence
- assuming framework behavior without verifying required preconditions in the target code or configuration
- filling missing specification or design intent from general knowledge

## Domain-Specific Rules

- specification:
  - specification and design evidence outrank general coding knowledge
  - if intended behavior is not stated locally, record `unknown`
- performance:
  - measured data or explicit performance requirements outrank performance heuristics
  - do not claim observed performance without measurement evidence
- security:
  - common vulnerability knowledge may guide inspection
  - do not assert exploitability or safety without local evidence
- license:
  - package metadata, license texts, and provenance records outrank remembered package reputation
  - do not assume license acceptability from model recall

## Required Handling When Evidence Is Missing

- mark the result as `unknown`
- record the evidence gap explicitly
- attach metrics under [Metrics definition](120_metrics_definition.md#xid-7A2F4C8D1201)

## Output Rule

- Every review judgment must distinguish:
  - evidence-backed findings
  - inference needing confirmation
  - unresolved items marked as `unknown`

## Relation To Capability Types

- This rule is mandatory for `judgment` capabilities.
- `execution` capabilities may use internal knowledge more freely for drafting or structuring, but must still preserve uncertainty when outputs depend on missing evidence.
