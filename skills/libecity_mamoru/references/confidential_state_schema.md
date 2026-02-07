# Confidential State Schema: libecity_mamoru

Use this schema for confidential current-state knowledge.
Store the actual file only in ignored paths (recommended: `.private/libecity_mamoru/current_state.md`).

## Header

- last_updated: `YYYY-MM-DD`
- owner_scope: `self|household`
- risk_tolerance: `low|medium|high`
- monthly_protection_budget: number or range

## Profile Snapshot

- household_structure
- employment_and_income_stability
- key_dependency_risks
- residence_and_disaster_context

## Financial Defense

- emergency_fund_months
- fixed_costs_breakdown
- debt_overview
- liquidity_constraints

## Coverage and Contracts

- insurance_inventory
- known_coverage_gaps
- contract_renewal_calendar
- legal_document_readiness

## Security and Fraud Defense

- account_security_status (MFA/password/recovery)
- fraud_incident_history
- monitoring_and_alerts
- weak_points

## Learning Data

- ingestion_log:
  - source_type
  - source_date
  - ingested_at
  - extracted_fields
  - confidence
  - unresolved_items
- derived_metrics:
  - monthly_fixed_cost_trend
  - abnormal_change_alerts
  - seasonal_notes

## Priority Risks

- high_risks
- medium_risks
- low_risks

## Action Backlog

For each action:
- id
- category
- priority (`now|next|later`)
- owner
- due_date
- expected_effect
- estimated_cost
- status (`todo|doing|done|blocked`)

## Review Log

Add entries in chronological order:
- date
- trigger (monthly/quarterly/event)
- what_changed
- decisions
- follow_up_actions
