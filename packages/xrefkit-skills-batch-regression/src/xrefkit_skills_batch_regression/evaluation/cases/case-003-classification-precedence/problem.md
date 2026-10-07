# Case 003: classification precedence and traceable differences

## Task

Compare old and new results for the same serialized inputs. Apply the stated
classification precedence exactly:

`system_error > uncertain > business_invalid > upstream_absent > result comparison`

Normalize only `run_id` and `completed_at`. Preserve the input, both results,
the evidence reference, and the planned-rule relation for every difference.

## Explicit rules

- `JP + Full`: unchanged successful result.
- `US + Full`: `tax_total` change is planned and approved; `processed_count`
  must not change.
- `JP + Delta`: upstream source is explicitly absent; it is not a system error.
- `US + Delta`: the old execution returned a timeout error. The new execution
  returned a success result. The timeout evidence is attached to the old run.
- `EU + Full`: the new execution returned a serialization error; no result
  comparison is valid.
- `EU + Delta`: both runs returned `status=unknown` because the adapter lost
  the source correlation key. This is uncertain, not baseline_match.

## Observed records

```yaml
- input: {region: JP, mode: Full}
  old: {status: ok, processed_count: 10, tax_total: 1000, run_id: old-1, completed_at: t1}
  new: {status: ok, processed_count: 10, tax_total: 1000, run_id: new-1, completed_at: t2}
- input: {region: US, mode: Full}
  old: {status: ok, processed_count: 12, tax_total: 1200, run_id: old-2, completed_at: t1}
  new: {status: ok, processed_count: 12, tax_total: 1260, run_id: new-2, completed_at: t2}
- input: {region: JP, mode: Delta}
  old: {status: upstream_absent, source: jp-delta-feed}
  new: {status: upstream_absent, source: jp-delta-feed}
- input: {region: US, mode: Delta}
  old: {status: timeout, error_ref: old-timeout-4}
  new: {status: ok, processed_count: 4, tax_total: 400}
- input: {region: EU, mode: Full}
  old: {status: ok, processed_count: 9, tax_total: 900}
  new: {status: serialization_error, error_ref: new-serialization-5}
- input: {region: EU, mode: Delta}
  old: {status: unknown, correlation_key: null}
  new: {status: unknown, correlation_key: null}
```

## Required output

Produce one classification per input, retain all evidence references, and list
which findings require human disposition before closure.
