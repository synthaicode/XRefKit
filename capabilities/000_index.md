<!-- xid: C14253A74C4F -->
<a id="xid-C14253A74C4F"></a>

# Capabilities Index

This folder stores reusable capability definitions.
Keep domain facts in `knowledge/` and executable procedures in `skills/`.

## Rules

- One capability page per coherent reusable unit.
- Keep workflow and governance in `docs/`.
- Keep business activity names in `docs/` workflows and responsibilities, not as capability names.
- Keep domain knowledge references XID-based.
- After edits, run `python -m fm xref fix`.

## Layering

- `docs/`: workflows, governance, boundaries, escalation
- `capabilities/`: capability definitions such as inputs, outputs, preconditions, triggers, constraints
- `knowledge/`: shared domain knowledge used as evidence or reference
- `skills/`: executable procedures that invoke one or more capabilities

## Initial layout

- `investigation/`
- `supply/`
- `estimation/`
- `requirements/`
- `planning/`
- `design/`
- `manufacturing/`
- `operations/`
- `quality/`
- `business/`
- `marketing/`
- `management/`

## Entries

- [CAP-INV-001 Scope Classification](investigation/100_cap_inv_001_service_catalog_analysis.md#xid-867B78FF702F)
- [CAP-INV-002 Change Impact Enumeration](investigation/110_cap_inv_002_source_dependency_analysis.md#xid-E994FCDA8CD1)
- [CAP-INV-003 Structured Investigation Summary](investigation/120_cap_inv_003_change_target_summary.md#xid-6AB17163C9BF)
- [CAP-SUP-001 External Service Condition Comparison](supply/100_cap_sup_001_supplier_four_condition_check.md#xid-2DC9A90A6508)
- [CAP-SUP-002 Cost Pattern Projection](supply/110_cap_sup_002_cost_estimation.md#xid-754A17D69C7C)
- [CAP-EST-001 Solution Option Structuring](estimation/100_cap_est_001_solution_option_generation.md#xid-BDB6B54A3571)
- [CAP-EST-002 Assumption Ambiguity Classification](estimation/110_cap_est_002_assumption_ambiguity_classification.md#xid-B362EA06B9C2)
- [CAP-REQ-001 Requirement Structuring](requirements/100_cap_req_001_requirement_draft_creation.md#xid-BC408337F2A2)
- [CAP-REQ-002 Performance Constraint Structuring](requirements/110_cap_req_002_performance_requirement_definition.md#xid-D67FAD650F8C)
- [CAP-PLN-001 Work and Policy Planning Structuring](planning/100_cap_pln_001_task_decomposition_plan_draft.md#xid-F5193313AB79)
- [CAP-DSN-001 Solution Design Structuring](design/100_cap_dsn_001_solution_design_structuring.md#xid-6C1A2D9F4501)
- [CAP-DSN-002 Test Design Structuring](design/110_cap_dsn_002_test_design_structuring.md#xid-6C1A2D9F4502)
- [CAP-DSN-003 Integration and Regression Test Design Structuring](design/120_cap_dsn_003_integration_regression_test_design_structuring.md#xid-6C1A2D9F4503)
- [CAP-DSN-004 Test Plan Structuring](design/130_cap_dsn_004_test_plan_structuring.md#xid-6C1A2D9F4504)
- [CAP-MFG-001 Scoped Code Realization](manufacturing/100_cap_mfg_001_implementation.md#xid-1A12C5C61269)
- [CAP-MFG-002 Unit-Level Verification](manufacturing/110_cap_mfg_002_unit_test_execution.md#xid-55CC9027ACAD)
- [CAP-MFG-003 Test Method Review](manufacturing/130_cap_mfg_003_test_method_review.md#xid-55CC9027ACAE)
- [CAP-MFG-004 Design Alignment Self Evaluation](manufacturing/120_cap_mfg_004_manufacturing_self_check.md#xid-6F5A9C1B4401)
- [CAP-OPS-001 Release Material Structuring](operations/100_cap_ops_001_release_plan_draft_creation.md#xid-9715BACE7EB8)
- [CAP-OPS-002 Operational Signal Specification](operations/110_cap_ops_002_monitoring_design.md#xid-316B0FB4493C)
- [CAP-OPS-003 Event Response Structuring](operations/120_cap_ops_003_event_response_procedure_draft.md#xid-6DA033B45D93)
- [CAP-OPS-004 Operational Readiness Evaluation](operations/130_cap_ops_004_operational_readiness_gate.md#xid-83140C9538B3)
- [CAP-OPS-005 Release Verification](operations/140_cap_ops_005_release_verification.md#xid-83140C9538B4)
- [CAP-QA-001 Specification Conformance Review](quality/100_cap_qa_001_code_review.md#xid-7E9CCEBEDA2D)
- [CAP-QA-003 Release Plan Suitability Review](quality/120_cap_qa_003_release_plan_suitability_review.md#xid-93E53EF38700)
- [CAP-QA-004 Management Table Check](quality/110_cap_qa_004_management_table_check.md#xid-AFEB172B97D8)
- [CAP-QA-005 Attribute Usage Review](quality/130_cap_qa_005_attribute_usage_review.md#xid-5A1C2F0E5505)
- [CAP-QA-006 Performance Risk Review](quality/140_cap_qa_006_performance_risk_review.md#xid-5A1C2F0E5506)
- [CAP-QA-007 Security Review](quality/150_cap_qa_007_security_review.md#xid-5A1C2F0E5507)
- [CAP-QA-008 License Compliance Check](quality/160_cap_qa_008_license_compliance_check.md#xid-5A1C2F0E5508)
- [CAP-QA-009 Integration and Regression Verification](quality/170_cap_qa_009_integration_regression_verification.md#xid-5A1C2F0E5509)
- [CAP-BIZ-001 Value-Constraint Alignment Evaluation](business/100_cap_biz_001_value_constraint_fit_evaluation.md#xid-837CDB1183C9)
- [CAP-MKT-001 Presentation Material Structuring](marketing/100_cap_mkt_001_presentation_material_structuring.md#xid-A4E9B13D7C20)
- [CAP-MKT-002 Repository Infographic Snapshot](marketing/110_cap_mkt_002_repository_infographic_snapshot.md#xid-C8D4A92F61E0)
- [CAP-MGT-001 Execution Management](management/100_cap_mgt_001_execution_management.md#xid-A365F4499AA7)
- [CAP-MGT-002 Uncertainty and Risk Logging](management/110_cap_mgt_002_uncertainty_risk_logging.md#xid-9F14372D994A)
- [CAP-MGT-003 Out-of-Scope Escalation](management/120_cap_mgt_003_out_of_scope_escalation.md#xid-1E3B2AA5B328)
- [CAP-MGT-004 Context Direction Guard](management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11)

