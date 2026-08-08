<!-- xid: B4F1C8D2A612 -->
<a id="xid-B4F1C8D2A612"></a>

# Service, data, and impact investigation

Declare `scope`, `included`, `excluded`, `detail_level`, and `unknowns`.
Identify service/version/environment, C# and SQL components, stored
procedures, tables, integrations, downstream consumers, branches, calls,
reads/writes, transactions, errors, retries, cancellations, and result paths.

When existing data affects behavior, record source, environment, extraction
time, query/filter, snapshot or fixture method, masking, counts, freshness,
related-record rules, lifecycle/status distribution, NULL/missing cases, and
reproducibility. Map data states to tests. Do not use production as a test
shortcut; stale, incomplete, unavailable, or unreproducible data is an
impact-bearing `unknown`.

Use DFD for movement, Entity/ER for structure, state views for lifecycle, and
sequence/process views for timing. Preserve stable service, entity, flow, and
change-point identifiers. Import existing artifacts before new discovery and
reuse XID-bearing Knowledge through `xref show`.
