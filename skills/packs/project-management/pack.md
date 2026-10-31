<!-- xid: 6A37D1F9B804 -->
<a id="xid-6A37D1F9B804"></a>

# Pack Manifest: Project Management

- pack_id: `project-management`
- summary: establish project progress rules, coordinate iterative requirements discovery, and guide contributors using recorded prerequisites and independent quality decisions
- maturity: `draft`
- depends_on:
  - os_contract_version: `1`
- entry: `../../../docs/packs/project-management/entry.md#xid-78C2A5F1D903`
- owns_skills:
  - `skills/packs/project-management/progress_rules_setup`
  - `skills/packs/project-management/requirements_discovery_coordination`
  - `skills/packs/project-management/work_progress_coordination`
- uses_skills:
  - `skills/packs/business-intake/business_learning_interview`
  - `skills/investigation_flow`
  - `skills/requirements_flow`
  - `skills/planning_flow`
  - `skills/brownfield-workflow`
  - `skills/os/local_work_management`
  - `skills/os/azure_work_item_integration`
- uses_knowledge:
  - `knowledge/operations/161_local_client_work_management.md#xid-F3A8D602C951`
  - `knowledge/operations/160_azure_devops_client_work_integration.md#xid-C8E2A591D740`
- inputs: purpose and current clues, project-selected rules and records, human answers, evidence and separate quality decisions
- outputs: confirmed setup or setup gaps, iterative discovery records, scoped next actions, persistent artifacts and explicit human handoffs

Project-specific Knowledge is selected by the three definitions' query needs;
no fictional project settings are bundled. The used operating-model Knowledge
applies only when its corresponding persistence adapter is selected. Existing
technical Skills and quality ownership remain external handoff dependencies.
This draft grouping does not approve trial use or install those dependencies.
