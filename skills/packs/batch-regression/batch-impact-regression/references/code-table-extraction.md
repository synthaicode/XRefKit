<!-- xid: 8E50930676E2 -->
<a id="xid-8E50930676E2"></a>

# Code table extraction

Run:

```powershell
python scripts/batch_regression.py extract-tables <source-root> -o <report.json>
```

The scanner reads `.cs` and `.sql` files and emits:

- `decision_table`: each statically recognized `if`, `when`, or `case` condition with source path and line
- `factors`: fields and literal comparison values with evidence references
- `orthogonal_table`: deterministic strength-2 pairwise covering rows
- `uncertainties`: expressions that were found but not resolved statically

The output is evidence for review. It does not prove that a condition is an
業務ルール, does not infer branch outcomes, and does not replace compilation,
Roslyn analysis, SQL Server parsing, or human confirmation. Dynamic SQL,
reflection, generated code, macros, configuration-driven rules, and complex
multi-line expressions may remain unresolved.
