# Batch Impact Regression

Analyze existing C# batches and SQL Server stored-procedure execution paths
when a requirement changes behavior and the combination space is large.

Follow the bundled 15-step workflow in `references/workflow.md`. Inspect C#
and SQL as one execution path, keep business constraints separate from source
conditions, and stop when dynamic dispatch, DB side effects, or expected
differences lack evidence.

Use the deterministic tools under `scripts/`:

```powershell
python scripts/batch_regression.py extract-tables <source-root> -o tables.json
python scripts/batch_regression.py report <config.json> <old.json> <new.json> -o report.json
```

The first command creates source-backed decision-table evidence, inferred
factors, and a strength-2 pairwise covering-table candidate. The second
compares old/new adapter records. Neither command connects to a real database;
use an isolated adapter conforming to `references/adapter-contract.md`.

The human remains responsible for business validity, baseline correctness,
planned differences, unexplained differences, and release disposition.
