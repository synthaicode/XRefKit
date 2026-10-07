# Case 002: dynamic procedure dispatch is unresolved

## Task

Analyze the batch path and determine whether the regression comparison can
start. Stop at the first material unknown and prepare a human handoff when the
execution path cannot be proven.

## C# path

```csharp
public Task RunAsync(BatchRequest request, CancellationToken ct)
{
    var procedure = configuration[request.Operation + ":Procedure"];
    return executor.ExecuteAsync(procedure, request.Parameters, ct);
}
```

The configuration file supplied for this case contains only:

```yaml
OrderDelta: ${ORDER_DELTA_PROCEDURE}
```

The environment value is not supplied. No source or deployment artifact proves
which stored procedure the placeholder resolves to.

## SQL evidence available

The repository contains `dbo.ApplyOrderFull.sql`, but no resolved procedure
name for `OrderDelta`. One script contains dynamic SQL that builds a table name
from an input prefix. The allowed prefixes and resulting tables are not
provided.

## Execution boundary

- target database: isolated test database is declared, but the adapter cannot
  resolve the procedure name;
- old/new selectors: supplied;
- combination values: `region=[JP,US]`, `mode=[Full,Delta]`;
- old/new result files: absent;
- rollback/restore procedure: not supplied.

## Required output

Report the known path, unresolved path, minimum evidence needed, and whether
execution, comparison, reduced-set selection, or release disposition may
continue.
