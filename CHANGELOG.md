# Changelog

## 0.7.0

- Guide migration from the new connected AI: inspect client-local legacy Skills,
  shared Python tools, tests and dependency files without executing them; prepare
  selected resources and concrete work items in the existing Workflow runtime.
- Generate static test preparation scaffolds while preserving missing behavioral
  expectations as unknown. Observed legacy outputs remain distinct from
  business-approved expected results; unavailable checks never count as passing.
- Transfer prepared assets through existing contribution upload, review and human
  adoption. Register only the exact adopted bundle, retaining converted Skill
  readiness and explicit client verification requirements.
- Associate registered Skills with shared resource manifests, pinned metadata and
  file hashes. Fetch resources over HTTP MCP into a verified local version cache
  while preserving relative paths. Python runs on the client; the server does
  not execute migrated code or install its dependencies.
- Reject unsafe resource paths, changed adopted bytes and damaged caches; retain
  preparation progress and migration failures for explicit recovery.
- Document the package-first HTTP workflow, test-safety boundary, registration,
  client execution and separate evidence required for completion.

Compatibility requires the official Skill dependency-admission updates:
Brownfield 0.1.6, CSharp 0.1.2 and Batch Regression 0.4.4. Core release gates check
the exact Core wheel against both published and candidate Skills. XDDP remains
an unpublished candidate. Real legacy environments still require their own
dependency, safe-execution and business-expectation verification.

## 0.6.2

- Preserve the released 0.6.1 runtime, including MCP contribution and maturity
  review, instruction gateway, guided legacy migration, setup, and Attention Pet.
- Adopt 62 audited canonical repository Skill definitions, retaining original
  source obligations, declared runtime-policy provenance, legacy invocation/XID
  aliases, explicit missing-input refusal, and draft refusal. External split/YAML
  Skill APIs remain supported; new runtime records retain Workflow ownership.
- Return the selected canonical definition's actual raw content with stable
  conditional retrieval and collision/freshness checks.
- Split source-analysis criteria into a stable common router and 11 coherent
  on-demand fragments. Preserve all original source lines and consumer obligations;
  no similarity-based knowledge merge or deletion occurs.
- Require reviewable ontology assessment during material knowledge authoring,
  with bounded structural evidence validation that does not certify semantic truth.
- Use task-owned report shapes and supplementary readability guidance inspired
  by ASD-STE100. Preserve task-specific detail and evidence; no fixed heading
  sequence or ASD compliance guarantee is imposed. Machine Run Logs are unchanged.
- Gate Core releases on the exact wheel with separately verified published and
  repository candidate official Skills, executed regressions, and combined installs.
  XDDP remains an unpublished candidate and is not released by this Core update.

Compatibility: 0.6.2 stays within the public Brownfield0.1.5, Csharp0.1.1, and
Batch regression0.4.3 distribution ranges. Dependency admission is not a passing
compatibility claim; the release requires the exact-wheel checks and CI to pass.
Repository source adoption is scoped to this repository's explicit manifest and
does not silently migrate third-party repositories or promote Skill maturity.
