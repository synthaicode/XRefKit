<!-- xid: 9C03927FF35B -->
<a id="xid-9C03927FF35B"></a>

# C# and SQL Server analysis checklist

Analyze one execution path across both layers. Record evidence locations for:

- C# schedule/CLI entry, command construction, SP name resolution, parameter names/types/size/precision/scale, NULL/empty/default/date/decimal conversion, timeout, retries, cancellation, result-set mapping, return value, OUTPUT parameters, and exceptions.
- SP definitions and child SPs, functions, views, tables, temp tables, table variables, dynamic SQL, dynamic object names, validation/calculation/update branches, row counts, transaction boundaries, isolation, locks, commits/rollbacks, triggers, and error propagation.
- Cross-boundary type, precision/scale, rounding, collation, date/time-zone, NULL, empty-string, default-value, and encoding behavior.

Do not conclude from C# alone or SQL alone. If dynamic SQL or dynamic SP
resolution cannot be closed statically, record the unresolved target and the
affected candidate count as `uncertain` until runtime evidence closes it.
Never run a write-capable batch against production. Prefer a cloned/snapshot
DB, isolated schema, disposable database, or transaction rollback, and prove
the side-effect check with before/after row counts and changed keys.
