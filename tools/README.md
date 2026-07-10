<!-- xid: 505FA1F89936 -->
<a id="xid-505FA1F89936"></a>

# tools/ — when to use which

Choose by the **question you are answering**, not by the tool you remember. The
headline rule comes from a measured A/B
([ADR 0001](../docs/adr/0001-where-step-grep-first.md#xid-F4B92B6AC13E)):

> For **text-greppable** questions — where a type / method / config key is
> referenced, used, or constructed — use `grep`/`rg` + LLM reasoning. Do **not**
> run the deterministic structure pack: it gives no token or accuracy gain over
> grep at any codebase scale, and grep is complete and cheaper.

The deterministic tools earn their cost only on questions grep answers poorly:
constant-folded values, lifetime/type joins, transitive reach with no textual
footprint, and quality predicates that must be exhaustive, reproducible, and
auditable.

## Decision guide

| Your question | Use | Do NOT use |
|---|---|---|
| Where is `Foo` / `Foo.Bar` / `new Foo` referenced or constructed? (impact discovery) | `grep` / `rg` → small representative reads → LLM impact-pattern classification → review vs must-change split | the structure pack (ADR 0001) |
| A fact grep can't compute: attribute **values**, DI **lifetimes**, transitive non-textual reach, async-without-CT | the structure pack, one inventory per question (below) | grep alone |
| Does this code **violate** a quality property P (gate: exhaustive / reproducible / auditable)? | the analyzer pipeline (below) | LLM-only scan (variance, misses) |
| What are the de-facto conventions of an existing codebase? | `csharp_naming_profile.py`, `csharp_commonality.py` | — |
| Is C# even in scope for this run? | `cs_scope_probe.py` | — |
| The repo's own CI / governance | `run_quality_gate.py` and its sub-checks | the C# analysis tools |

## Semantic-inventory tools (grep-weak C# questions)

Precondition: `dotnet restore <sln-or-csproj>` first, or framework-dependent facts
(DI, logging, config) come back silently empty. All output is **candidate, not
verdict** — confirm activation, curate against the objective, record the rest as
`unknown`. See [121](../knowledge/source_analysis/121_structure_analysis_determinism_tiers.md#xid-5301B897BA41).

| Tool | Answers (grep can't) |
|---|---|
| `structure_graph/` (C# Roslyn extractor) | emits the graph + `--attributes` / `--di` / `--invocations` / `--decl` inventories |
| `attribute_inventory_report.py` | custom-attribute applications with **constant-folded** ctor/named values |
| `di_registration_report.py` | DI service/impl/**lifetime**, **captive-dependency**, `new`-bypass (with `--graph`) |
| `invocation_facts_report.py` | logging / config-binding / pipeline-order / reflection-discovery / transaction call shapes |
| `declaration_facts_report.py` | async-without-`CancellationToken`, static mutable state, lock/`Interlocked`, `DbSet`, `#if`, TFMs |
| `structure_graph_report.py` | dependency direction, fan-in/out coupling, `writes` state-ownership |
| `test_coverage_reach.py` | test→SUT reachability over `calls`+`dispatches-to`; coverage-gap candidates |
| `where_seed_traversal.py` | **transitive** impact grep cannot follow (A→B→C with no textual mention); seed-driven, damped. Not for greppable impact |

## Quality-gate tools (deterministic violation checks)

A gate needs exhaustiveness, reproducibility, and audit — the LLM's weak spots.
Tier the patterns ([131](../knowledge/source_analysis/131_csharp_error_policy_locator_tiers.md#xid-D1F4A7C3E209)):
T2 semantic/flow patterns belong here; T1 purely-lexical patterns are often as well
served by grep + LLM.

| Tool | Role |
|---|---|
| `cs_scope_probe.py` | applicability gate: is C# in scope for this run |
| `collect_analyzer_sarif.py` | run the Roslyn analyzers, emit SARIF |
| `sarif_to_locator.py` | normalize SARIF into `cs.err.*` locator candidates |
| `error_policy_locator.py` | the custom locators an analyzer doesn't cover (e.g. empty-catch) |
| `error_policy_audit.py` | merge analyzer + custom hits into one candidate stream (dedup) |

Pipeline: `collect_analyzer_sarif.py → sarif_to_locator.py ─┐`
`error_policy_locator.py ───────────────────────────────────┴→ error_policy_audit.py`.
Output is candidate-only; disposition and per-case approval stay downstream
(`csharp_review`, `csharp_error_policy_extraction`).

## Design-time descriptive tools

| Tool | Role |
|---|---|
| `csharp_naming_profile.py` | de-facto naming conventions (dominant casing/affixes + outliers) for matching new code to existing |
| `csharp_commonality.py` | DRY candidates: duplicate blocks and repeated literals (candidate-only, does not refactor) |

## Repo governance / CI (not for analyzing target codebases)

| Tool | Role |
|---|---|
| `run_quality_gate.py` | the repository's own gate: pytest, `xrefkit xref/skill/pack` checks, log audit, baselines, node project checks |
| `audit_skill_runtime_logs.py` | audit Skill runtime logs (`xrefkit.skillrun`) |
| `check_skill_knowledge_xids.py` | verify Skill `knowledge_slots` / `knowledge_refs` and Skill-body `knowledge/` links are connected by resolvable canonical `#xid-...` references (`12` uppercase hex chars); use `--fix-missing-xids` to assign or replace XIDs in checked Skill files and directly referenced local Markdown/source files |
| `check_project_quality_baseline.py` | node projects under `projects/` baseline check |
| `migrate_legacy_flow_skill.py` | migrate a legacy flow into the Flow/Capability/Skill model |
| `convert_to_xrefkit_skill.py` | normalize external Skill directories or `skills/` + `knowledge/` trees into XRefKit Skill/Knowledge split form |

### `convert_to_xrefkit_skill.py` usage

Use this when importing file-based external Skills whose `SKILL.md`, `skill.md`,
`README.md`, or `readme.md` links to local Markdown/TXT reference files that
should become XRefKit Knowledge.

Single Skill mode takes one Skill directory:

```powershell
python tools/convert_to_xrefkit_skill.py <external-skill-dir> --skill-id <skill_id> --json
```

Batch mode takes the parent root that contains `skills/` and optional
`knowledge/`, not the `skills/` directory itself:

```powershell
python tools/convert_to_xrefkit_skill.py <external-root> --batch --skill-id-prefix <prefix> --json
```

For batch mode, the expected source shape is:

```text
<external-root>/
+-- skills/
|   +-- alpha/
|   |   +-- SKILL.md
|   +-- beta/
|       +-- skill.md
+-- knowledge/
    +-- shared.md
```

The tool scans only direct children of `<external-root>/skills/`. A child is a
Skill when it contains `SKILL.md`, `skill.md`, `README.md`, or `readme.md`.
It imports only Markdown/TXT files that are directly linked from the Skill
document. Unlinked files are left untouched.

Default output is private draft content:

```text
skills_private/<skill_id-or-prefix.skill-folder>/
knowledge/imported_skills/<skill_id-or-prefix>/
```

Existing canonical XIDs in linked reference files are preserved. Missing XIDs
are assigned. Skill links are rewritten to `knowledge/...#xid-...`, and the
generated `meta.md` receives `knowledge_slots` bound to the imported XIDs.

## Binding rules

- **Greppable → grep.** The structure pack is opt-in per grep-weak question, never a
  standard pass (ADR 0001).
- **Restore before Roslyn.** `structure_graph` and the analyzer pipeline need symbols
  resolved; unrestored targets yield silently empty framework facts.
- **Build after a source-level copy.** `structure_graph/bin/` is gitignored, so a
  fresh clone or file copy has no binary; build it per
  [078_structure_graph_build_guide](../docs/guides/078_structure_graph_build_guide.md#xid-8B3E5D0A94C7)
  before using the semantic-inventory tools.
- **Candidate, not verdict.** Every analysis tool here proposes; inclusion, severity,
  and any change are decided downstream by a human/LLM with per-case approval.
