<!-- xid: B27C9E15A640 -->
<a id="xid-B27C9E15A640"></a>

# Azure client-work request examples

These inert samples describe the current strict input shapes. Replace sample
organization/project/workspace/connection IDs with explicitly selected local
configuration. Resolve real stored revisions and evidence before operation.
The write guard fixes PBI 10 / Task 21; replacing those IDs does not generalize
the writer. The [operating model](../../../../knowledge/operations/160_azure_devops_client_work_integration.md#xid-C8E2A591D740)
owns implementation facts and limits. No sample grants operation authority.

## Read profile

```json
{"schema_version":1,"workspace_id":"sample-workspace","connection_id":"sample-read","service":"azure_devops_services","organization":"sample-org","project":"sample-project","environment":"test","auth":{"kind":"pat_env","env_var":"AZURE_DEVOPS_PAT"},"allowed_operations":["read_work_item"],"allowed_item_ids":[10,21]}
```

## Write profile

```json
{"schema_version":1,"workspace_id":"sample-workspace","connection_id":"sample-write","service":"azure_devops_services","organization":"sample-org","project":"sample-project","environment":"test","auth":{"kind":"pat_env","env_var":"AZURE_DEVOPS_PAT"},"allowed_operations":["read_work_item","update_task_state_history"],"allowed_item_ids":[10,21]}
```

## Capture request

```json
{"schema_version":1,"import_id":"sample-import-001","connection_id":"sample-read","organization":"sample-org","project":"sample-project","pbi_id":10,"task_ids":[21]}
```

A comparison capture adds both `comparison_binding_id` and
`expected_observation_revision`, using a new import ID.

## Binding request

```json
{"schema_version":1,"binding_id":"sample-binding-001","import_id":"sample-import-001","plan_id":"sample-plan","plan_revision":"v1","expected_observation_revision":1,"approval_refs":["work/judgments/mapping-approval.md"],"mapping":[{"item_id":21,"included_step_ids":["S1"],"completion_criterion":"The approved Task result is verified against its recorded completion criteria."}]}
```

## Initial delivery request

```json
{"schema_version":1,"report_id":"sample-report-001","connection_id":"sample-write","source_connection_id":"sample-read","write_approval_refs":["work/judgments/task-write-approval.md"],"binding_id":"sample-binding-001","item_id":21,"expected_observation_revision":2,"completion":{"confirmed":false,"evidence_refs":[]},"work_authorization":{"active":true,"rework":false,"evidence_refs":["work/judgments/work-authorization.md"]},"artifacts":[{"artifact_id":"sample-result","version":"v1","availability":"local_only"}]}
```

`confirmed:false` is intentional: this sample does not assert completion. A
Done request needs actual recorded completion evidence and completed mapped
steps. A later request has a new report ID, a new stored observation revision,
and either `previous_report_id` or `previous_reconciliation_id`, never both.

## Reconciliation request

```json
{"schema_version":1,"reconciliation_id":"sample-reconciliation-001","report_id":"sample-report-001","connection_id":"sample-read","source_connection_id":"sample-write","binding_id":"sample-binding-001","expected_observation_revision":2,"approval_refs":["work/judgments/reconciliation-approval.md"]}
```

Here `source_connection_id` identifies the original **write** connection. In
delivery input it identifies the original **import/read** connection. The
reconciliation input never contains a replacement patch.
