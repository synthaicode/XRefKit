# Installed package MCP asset integration

Status: implementation done; parent owns release and consumer verification.

Basis: authorized Core prerequisite for the C# reporting package. PR #183 was
merged as e442f51b; this supplement preserves its history. Runtime:
c2bf423b-8174-4fbd-872d-73e27bc04b46, python_implementation_flow, isolated executor.

Changes: declared package assets remain an explicit allowlist. Portable paths
and resolved containment reject escapes; Skill/Markdown identity mismatches,
embedded startup shadowing, and duplicate Knowledge identities are refused.
Required Knowledge from manifest and YAML becomes required bound slots; missing
Knowledge remains unsatisfied. Declared asset content participates in catalog
versioning. Core metadata advances to 0.7.8 for parent-owned release.

Validation: `python -m pytest tests/test_package_knowledge_resolution.py
tests/test_mcp_package_routing.py tests/test_package_skill_run.py tests/mcp_catalog.py
tests/test_xrefkit_v2_discovery.py -q`: 76 passed, 1 skipped, 8 subtests passed.
`python -m compileall -q xrefkit/mcp/catalog.py` and `git diff --check` passed.
Installed MCP subprocess tests retrieve Knowledge, axes and schemas and verify
required slots. An initial overly broad test expected all Brownfield external
requirements to exist; the corrected check preserves unsatisfied external
requirements instead of claiming false success. No product exception was added.

Independent source review accepted by host_bridge_quality, recorded in parent
work/csharp-report-release/2026-11-07_independent_core_package_mcp_review.md.

Unverified: Windows symlink creation was unavailable, so that executable test
was skipped; resolved containment is source-reviewed. Published wheel/install
and report consumer acceptance remain parent release handoff. Live replacement
of manifest declarations in an already-built catalog is not asserted.
