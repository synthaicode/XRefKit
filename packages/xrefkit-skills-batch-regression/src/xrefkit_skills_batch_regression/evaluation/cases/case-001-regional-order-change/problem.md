# Case 001: regional order batch change

## Task

Analyze the proposed change to an existing C# batch and its SQL Server stored
procedure. Produce a deterministic candidate/comparison report, classify every
candidate result, identify unresolved human decisions, and state whether the
release can proceed.

Do not infer business rules from source conditions. Use only the explicitly
listed business constraint and planned-difference rule. Treat the old result as
an observed baseline, not as business truth.

## C# entry point

```csharp
public async Task RunAsync(string region, string mode, CancellationToken ct)
{
    await using var connection = await factory.OpenAsync(ct);
    await connection.ExecuteAsync(
        "dbo.ApplyOrderBatch",
        new { Region = region, Mode = mode },
        commandType: CommandType.StoredProcedure);
}
```

## SQL Server path

```sql
CREATE PROCEDURE dbo.ApplyOrderBatch
    @Region nvarchar(10),
    @Mode nvarchar(10)
AS
BEGIN
    SET NOCOUNT ON;

    IF @Region = N'US' AND @Mode = N'Delta'
        RETURN 17;

    UPDATE dbo.OrderSummary
       SET ProcessedCount = ProcessedCount + 1
     WHERE Region = @Region;
END
```

The return code is shown as source evidence only. It is not a business rule for
this case unless the explicit constraint below says so.

## Explicit candidate dimensions

```yaml
dimensions:
  region: [JP, US]
  mode: [Full, Delta]
```

## Explicit business constraint

`US + Delta` is business-invalid because the business owner has approved that
the Delta feed is not available for US orders. This constraint is configured
outside the source code and must remain a human-owned decision.

## Explicit planned difference

For `US + Full`, the new version intentionally changes `tax_total` because the
approved tax-rate table changed. The difference is planned only for the
`tax_total` field. Other changed fields remain unexplained.

## Old/new observed results

The isolated adapter produced these records for the same serialized inputs:

| region | mode | old result | new result |
|---|---|---:|---:|
| JP | Full | processed=10, tax_total=1000 | processed=10, tax_total=1000 |
| JP | Delta | processed=8, tax_total=800 | processed=8, tax_total=800 |
| US | Full | processed=12, tax_total=1200 | processed=12, tax_total=1260 |
| US | Delta | not executed by business constraint | not executed by business constraint |

## Required output

The report must include:

- candidate count and post-constraint count;
- the C# to stored-procedure path;
- classification for all four candidates;
- evidence for the business-invalid and planned-difference decisions;
- reduced regression-set recommendation;
- unresolved decisions and release disposition;
- explicit statement that the old version is an observed baseline only.
