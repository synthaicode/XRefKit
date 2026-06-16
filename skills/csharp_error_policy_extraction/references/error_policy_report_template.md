<!-- xid: 8A6A9B1C3223 -->
<a id="xid-8A6A9B1C3223"></a>

# Error Policy Report Template

Use this structure for the `csharp_error_policy_extraction` output report.
Sections may grow but must not be dropped; an empty section states why it
is empty.

```md
# Error Policy Report: <target>

- date: `YYYY-MM-DD`
- target: <repository / solution / project>
- scope filters: <filters or none>
- seed input: <prior dotnet_change_analysis note path or none>
- run log: <work/sessions path>

## 1. Search Pattern Set

| # | Pattern / command | Bucket | Added during run? |
|---|---|---|---|

## 2. Inventory (Phase 1)

### 2.1 Throw Sites

| file:line | module | error kind | behavior | propagation terminus | logging | intent | basis |
|---|---|---|---|---|---|---|---|

(rethrow records carry `rethrow_preserving` / `rethrow_resetting`)

### 2.2 Catch Blocks

(same record schema; kind = catch-all / typed / filtered / empty /
log-only / translate)

### 2.3 Custom Exception Types

| type | base | thrown by | caught by | representation convention |
|---|---|---|---|---|

### 2.4 Global Handlers

| handler | file:line | behavior | covers |
|---|---|---|---|

### 2.5 Dotnet-Specific Paths

(async void / fire-and-forget / sync-over-async / DI composition root /
Dispose; same record schema plus path-specific notes)

### 2.6 Omission Policies (detected range only)

(null return / Try* / fallback / bool-only; same record schema; this
section is explicitly non-exhaustive — see section 6)

### Bucket States

| bucket | state (`done` / `unknown` / `not_applicable`) | reason |
|---|---|---|

## 3. Category x Disposition Matrix (Phase 2)

| category \ disposition | fail-fast | propagate | translate | retry | degrade | swallow | log-only |
|---|---|---|---|---|---|---|---|
| configuration | | | | | | | |
| transient | | | | | | | |
| invariant_violation | | | | | | | |
| external_input | | | | | | | |
| unclassified | | | | | | | |

(each non-empty cell: count + representative file:line)

### De-Facto Policy Candidates

| category | majority disposition | share | candidate statement |
|---|---|---|---|

(candidates, not verdicts)

### Unclassified Items

| file:line | why unclassifiable | judgment material |
|---|---|---|

## 4. Contradictions (Phase 3)

Per contradiction group:

- group: <file:line list>
- behaviors: <each item's disposition and effect>
- placement explanation: <explainable -> possible conditional rule / not
  explainable -> contradiction>
- adjudication material: <what a human decision needs>

## 5. DI Startup-Throw Triage

| file:line | occurrence time | recovery responsibility | blast radius | note |
|---|---|---|---|---|

## 6. Coverage Limits (mandatory)

- omission policies: non-exhaustive; detected range = <patterns used>
- dynamic exception paths: reflection / delegate / generated code —
  not traced
- third-party libraries: internal swallowing invisible; boundary behavior
  only
- <additional limits found during the run>

## 7. Handoff List

| finding | type (defect / security) | handoff target | recorded as |
|---|---|---|---|

## 8. Unresolved Items

| item | why unresolved | suggested owner |
|---|---|---|
```
