# Confidential Password State Schema

Use this schema for confidential password-management knowledge.
Store actual records only in ignored paths (recommended: `.private/password_management/current_state.md`).

## Header

- last_updated: `YYYY-MM-DD`
- scope: `personal|household|team`
- owner
- security_level_goal: `baseline|strong|high`

## Critical Accounts

- primary_email_accounts
- financial_accounts
- cloud_admin_accounts
- work_identity_accounts

## Password Controls

- password_manager_status (tool, adoption level)
- unique_password_coverage_percent
- known_reuse_groups
- weak_password_exceptions

## MFA and Recovery

- mfa_coverage_percent
- phishing_resistant_mfa_accounts
- recovery_methods_inventory
- backup_codes_storage_status

## Incidents and Exposure

- known_breaches_or_leaks
- phishing_or_takeover_history
- unresolved_incidents

## Action Backlog

For each action:
- id
- account_group
- priority (`now|next|later`)
- owner
- due_date
- expected_risk_reduction
- status (`todo|doing|done|blocked`)

## Review Log

- date
- trigger
- changes
- decisions
- follow_up
