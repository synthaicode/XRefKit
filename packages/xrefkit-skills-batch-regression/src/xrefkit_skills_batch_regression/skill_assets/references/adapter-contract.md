<!-- xid: F4818190FD09 -->
<a id="xid-F4818190FD09"></a>

# Adapter boundary

The Skill does not claim to connect to a real batch or database. An adapter
must produce versioned JSON records with:

```json
{
  "input": {"dimension": "value"},
  "status": "success|business_error|system_error|not_executed",
  "result": {"field": "value"},
  "error": {"code": "...", "message": "..."},
  "updated_rows": 0,
  "path_refs": ["path-id"],
  "evidence_refs": ["file-or-log"]
}
```

An implementation may wrap `dotnet`, a test harness, or SQL Server tooling,
but it must enforce the configured timeout, isolate the DB, capture exit code,
stdout/stderr, result sets, return values, OUTPUT values, exceptions, and side
effect checks. The deterministic scripts consume artifacts; they do not invent
adapter output.
