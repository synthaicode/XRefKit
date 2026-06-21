<!-- xid: F4B92B6AC13E -->
<a id="xid-F4B92B6AC13E"></a>

# ADR 0001: Where step is grep-first; the deterministic pack is for grep-weak questions only

- Status: Accepted
- Date: 2026-06-21

## Context

A deterministic structure-analysis pack was built (Roslyn structure graph plus
semantic inventories: attributes, DI registrations, invocation facts, declaration
facts) and a `tools/where_seed_traversal.py` traversal was wired into the
`dotnet_change_analysis` skill as a backstop for the **Where** step — the impacted-
boundary list. The premise (see
[160](../../knowledge/source_analysis/160_structure_graph_tm_backstop.md#xid-163AD9936979)
and [121](../../knowledge/source_analysis/121_structure_analysis_determinism_tiers.md#xid-5301B897BA41))
was that deterministic traversal would raise recall and reduce tokens versus an
LLM inferring structure by reading code.

Before adopting this as the standard path, we ran a controlled A/B against an
LLM-only baseline, measuring real subagent token counts and recall/precision
against ground truth, at two codebase scales.

## Decision

**Do not run the deterministic pack as a standard Where backstop.** The standard
Where path is **grep-first**:

```
grep / rg (full reference surface in one pass)
  -> small representative reads (declaration + a few call sites)
  -> LLM impact-pattern classification
  -> split review boundary vs must-change boundary
```

The deterministic pack is retained only as a **Semantic-Inventory Mode** fallback
for questions `grep` answers poorly: custom-attribute values (constant folding),
DI lifetime / captive-dependency, async-without-`CancellationToken`,
`IDisposable`/`IAsyncDisposable` ownership, reflection / convention binding, and
transitive impact with no textual footprint (the one impact case `grep` cannot
follow).

## Evidence (A/B test)

Three arms per objective: LLM-only (grep/read), pack (deterministic traversal),
pack-assisted (LLM curating the pack's candidates). Tokens are real harness
subagent totals; seeds were derived from the objective only (the diff was hidden).

### Small codebase — MailKit.Pooling (905 nodes), make `ISmtpClientAdapter.SendAsync` type-safe

| Metric | LLM-only | Pack-assisted | Pack only |
|---|---|---|---|
| Final impacted files | 5 | 5 (identical) | 16 candidates |
| Recall (HEAD-existing GT) | 100% | 100% | 100% |
| Real tokens | 42,470 | **63,303 (+49%)** | ~0 (CPU) |
| Bytes read | 17,479 | 122,936 (7×) | — |

### Large codebase — Ksql.Linq (6,222 nodes), change the shape of `EntityModel`

Deterministic pack vs the 115-file `grep` reference surface: reached 140 files,
recall 92%, precision 69%.

| Metric | LLM-only | Pack-assisted |
|---|---|---|
| Final impacted files | 117 (review boundary) | 48 (must-change) |
| Real tokens | 43,118 | **44,918 (+4%, tie)** |
| Bytes read | 10,439 (3 files) | 15,104 (6 files) |
| Primary method | `grep` | **`grep` + intersect candidates** |

Across both scales the pack delivered **no token reduction and no accuracy gain**.
The cause is structural: `grep`/`rg` returns a type's full reference surface in one
pass at any scale, and an LLM classifies the impact pattern without reading most
files. The pack-assisted arm fell back to `grep` for the authoritative set anyway,
so the deterministic candidates were largely redundant.

## Consequences

- The `dotnet_change_analysis` Where step is grep-first; it no longer generates the
  structure pack by default. Lower complexity and no restore/build cost on the
  common path.
- The pack's investment is **not** justified by Where-step ROI. Its value is
  narrowed to the grep-weak semantic inventories above, where `grep` cannot do
  constant folding, lifetime joins, or transitive traversal.
- Whether the pack helps on those grep-weak questions is **not yet measured** — the
  open follow-up. The original motivation (deterministic custom-attribute values)
  lives here and was not the subject of this A/B.

## Alternatives considered

- **Pack as the standard Where backstop** (the original wiring): rejected by
  measurement — tie-to-worse on tokens, no accuracy gain, at both scales.
- **Improve pack precision (damping) first**: deferred — even a tie on tokens with
  a perfectly precise candidate set does not beat grep, which is already complete
  and cheap; precision work is only worthwhile inside Semantic-Inventory Mode.

## Limitations

Two single, greppable objectives (one per scale); indicative, not statistical.
HEAD-vs-commit-time drift on the small case (one GT file renamed away, excluded).
Token totals are one model/effort sample per arm.

## References

- Skill: `skills/dotnet_change_analysis/SKILL.md` (Where Impacted-Boundary Analysis;
  Semantic-Inventory Mode)
- [Structure-analysis determinism tiers](../../knowledge/source_analysis/121_structure_analysis_determinism_tiers.md#xid-5301B897BA41)
- [Structure graph as TM coverage backstop](../../knowledge/source_analysis/160_structure_graph_tm_backstop.md#xid-163AD9936979)
- Tools: `tools/structure_graph`, `tools/where_seed_traversal.py`, and the inventory reports under `tools/`
