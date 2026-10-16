# Independent source review: guided legacy migration

## Status

done — Source review and independent review-artifact quality accepted. Three original findings and the later embedded-identity correction independently rechecked as pass-after-fix. Publication remains coordinator-owned.

## Result

Scope: Core 0.7.0 migration changes at source checkpoint c588d46, including catalog/server wiring, contribution byte preservation, legacy migration registration, legacy_guidance.py, legacy_resources.py, packaged bootstrap resources, tests and guide. Reviewer did not author implementation. Runtime: ad94a081-9c7c-4d3a-8df2-afe73623b8d1, python_review. User authorized repository-native governance.

### Category matrix and static boundary

All rows are bounded source-review dispositions, not production or business certification. In the last column, production/real-business limitations are `not_detectable_by_static_analysis` and explicitly outside this feature review; named pending parent integration/compatibility results are `requires_runtime_or_human_evidence` and remain closure-relevant until recorded. A source pass does not pass those pending runtime checks. `confirmed_by_static_analysis` below includes direct source inspection; executed reproductions are separately identified.

| Category | Status | confirmed_by_static_analysis | not_detectable_by_static_analysis / requires_runtime_or_human_evidence |
|---|---|---|---|
| static baseline | pass | pyproject pytest config and python-package quality, Bandit -ll, declared/resolved pip-audit gates identified | Final full local gate and source-identical CI passed; no formatter/type-checker configured in inspected project metadata |
| resource efficiency | pass within scope | Prepared contribution has existing file-count/per-file/total limits; scoped resource fetch reuses one session; temporary staging is context-managed | Real legacy inventory size and deployment memory/cache quotas are out of scope, no production-volume safety claim |
| operational resilience | pass within scope | Durable migration staging/state and explicit changed-file failure; prepared files are not overwritten on resume | Focused migration/HTTP suite and final full gate passed; interrupted deployment behavior not independently load-tested |
| synchronization | pass within scope | Migration writes use existing lock, cache publishes through rename, cache loser retries validation | Concurrent filesystem hostile mutation is not claimed solved; final full gate passed; no production concurrency certification |
| required input | pass within feature scope | Skill/resource selections reject absent or excluded files; human expectation task remains explicit; F2 quoted-key credential gap corrected and independently rechecked | Actual business expectations and credential-free approval remain human-owned |
| support lifecycle | pass for declared runtime boundary | Requires Python >=3.11; no new third-party dependency introduced | Python 3.11 security-support end 2027-10 checked against https://devguide.python.org/versions/ on 2026-10-16; declared/resolved dependency audits passed in CI; reviewed-wheel official compatibility passed |
| error paths | pass within scope | Resource mismatch and missing adoption fail; no legacy code imported by inspection; uploaded files verified before registration | Filesystem quota/permission failure recovery not exhaustively exercised |
| time/locale/encoding | pass-after-fix | UTF-8 explicit; byte reads/base64 preserve CRLF; F1 case-insensitive reserved-path corruption corrected and independently rechecked | Non-UTF-8 legacy assets excluded with disposition, not supported silently |
| state/determinism | pass within scope | Existing runtime workitems retained on resume; retrieval receipts alone cannot complete resource migration; pinned manifest/hash association | Closed workflow records are evidence records, not independent business proof |
| uncertainty/escalation | pass within scope | Baseline/tests/expectations workitems remain pending; generated behavior test skipped; completion requires existing closure and exact criteria | Actual unavailable legacy environment remains explicit unverified boundary |
| contract/schema | pass-after-fix | Hash, path, duplicate, file-set and schema validation present; F1 reserved alias rejection corrected and independently rechecked | Malicious server and hostile local administrator excluded; no arbitrary schema compatibility promise |
| trace/context | pass within scope | Contribution ID, manifest hash, namespace, workitem identity and retrieval receipts retained; server audit records registration | Operational sufficiency for a particular regulated deployment not assessed |
| custom framework | pass within scope | catalog.skills dynamically rebuilds routing; server uses startup and active-run checks, admin registration; existing signed adoption reused; bootstrap definition/knowledge/tool packaged | Migration/HTTP regressions, clean wheel/sdist install CI and official compatibility passed; actual customer environment remains out of scope |

### Detector facts: required inputs

| Input | Decision gated | Source | Missing/invalid behavior | Default provenance | Disposition |
|---|---|---|---|---|---|
| selected Skill/resource path | include candidate bytes | client inventory | reject | none | pass |
| signed review/adoption | register accepted bundle | existing contribution event store | reject | none | pass |
| baseline/business expectation | complete migration | existing Skill Run | pending/unknown without required complete workitems | none | pass, record evidence only |
| credential-like configuration | include candidate bytes | UTF-8 source | Supported quoted-key credential candidates excluded after F2 correction | heuristic incomplete; human secret review required | pass-after-fix within feature scope |

## Findings

### F1 — major: reserve manifest filename case-insensitively

Evidence: xrefkit/mcp/legacy_resources.py validate_resource_manifest checks `path == MANIFEST_NAME`, while Windows treats LEGACY-RESOURCES.JSON as the same file. Isolated Windows reproduction constructed a valid manifest with that resource. materialize_legacy_resources returned a cache after replacing verified resource bytes with generated manifest bytes. Observed `original_preserved False`; second materialization raised `resource content mismatch: LEGACY-RESOURCES.JSON`.

Violated condition: returned cache must contain exact approved bytes. Remediation: casefold reserved manifest name and generated scaffold collisions; reject portable aliases before writes. Implementation-local, sent to implementation and coordinator. No actual user resource modified.

### F2 — major: quoted credential keys evade preparation exclusion

Evidence: xrefkit/mcp/legacy_guidance.py `_SECRET_CONTENT` only accepts unquoted key followed by colon/equal. Fake-only isolated settings.json with `{"api_key": "EXAMPLE_FAKE_TEST_ONLY_123456"}` inside a root Skill was both inventoried and bundled automatically. Existing credentials.json fixture uses filename detection and misses this case.

Violated condition: known credential-bearing configuration should not be automatically bundled. Remediation: detect supported quoted JSON/YAML key representations, regression with fake values, retain human secret review because heuristics cannot prove absence. Security-axis discovery handed to coordinator; coordinator accepted bounded in-scope correction and documented that existing security_review is C#-specific and unsuitable. No comprehensive security certification claimed.

### F3 — minor: prune known ignored directories before enumeration

Evidence path: `xrefkit/mcp/legacy_guidance.py` inventory traversal. Violated condition: ignored environments must be pruned before enumeration so excluded trees do not determine preparation cost. Original source used sorted(source.rglob('*')) before rejecting hidden/generated descendants. This materialized every .venv/.git/node_modules entry even though none was eligible. Implementation replaced this with top-down os.walk and directory pruning, with an excluded-directory disposition. A regression prevents scandir calls on ignored subtrees.

### Independent correction recheck

Executed `python -m pytest tests/test_legacy_guidance.py -k "quoted_config or case_alias or prunes_environment or embedded_bootstrap" -q`: 10 passed, 10 deselected. F2 and F3 are pass-after-fix. Guidance reserved aliases reject before writes; the subsequent F1 resource-validator recheck is recorded below. The embedded catalog identity change avoids new Git subprocess calls during live request bootstrap; source and new targeted test reviewed.

Source-race assessment: prepare rereads selected bytes and reapplies the credential detector before constructing the manifest. Resolved containment and symlink checks protect selected source reads; no arbitrary legacy code is imported. Exact upload metadata excludes unrelated files already present in the preparation output directory. No claim is made about hostile concurrent filesystem mutation or exhaustive credential detection.

## Evidence

Startup C3A1F78D9B22 and required source set loaded. Semantic routing selected python_review; runtime was opened only after coordinator committed prepared source because clean-tree checkpoint initially refused.

Loaded required criteria: A9B7C6D5E4F1, A9B7C6D5E4F2, 5F21C8A41001, 5F21C8A41002, 7A2F4C8D1901, 7A2F4C8D1801 and all ten common review-axis topics 5F21C8A41101 through 5F21C8A41110 plus shared overload basis 5F21C8A41111. Source obligation retention includes explicit evidence limits, independent finding disposition and quality-role separation.

### Final source disposition

Executed `python -m pytest tests/test_legacy_resources.py -k "reserved or case_alias" -q`: 4 passed, 15 deselected. Inspected the resource validator casefold guard and direct materialization regression. F1 is pass-after-fix; rejected aliases never publish a cache. F1/F2/F3 are all resolved at source-review scope. Matrix rows formerly needs_confirmation because of these defects are now pass-after-fix; static-baseline row is accepted on the final evidence below.

### Integrated validation evidence received

Independent quality reviewer read terminal local logs on 2026-10-16: focused entire migration/resource/HTTP-related suite 48 passed in 32.03s (`.tmp/070-focused-final.log`); final wheel and sdist successfully built (`.tmp/070-build-final.log`); artifact inspection found no forbidden paths, oversized files or credential patterns (`.tmp/070-artifact-final.log`); Bandit found 0 medium/high severity issues and 62 low severity issues (`.tmp/070-bandit-final.log`); declared requirements audit reported no known vulnerabilities (`.tmp/070-dependency-audit.log`). Coordinator reported final Twine success. These observations are archived here because local temporary logs are not public artifacts. Full configured gate, resolved dependency audit and exact-wheel official MCP compatibility are not represented by these partial results.

### Full local baseline terminal result

The local full-suite run completed with **4 failed, 1506 passed, 4 skipped, 108 subtests passed in 609.82s**. Failures: `test_human_review_then_local_adoption_is_catalog_visible_and_auditable`, `test_stdio_startup_receipt_and_reference[protocols2-python_review]`, `test_catalog_defaults_to_one_definition_and_old_id_resolves`, and `test_existing_catalog_readiness_and_aliases_remain_unchanged`. This is a failed baseline, not a pass. Coordinator assigned diagnosis/corrections and independent regression recheck; baseline acceptance was withheld until the corrected final run recorded below. This run collected tests before the coordinator's subsequent adoption assertion correction; that timing does not erase the recorded failures.

The exact-wheel official compatibility evidence at `work/sessions/2026-10-16_evidence_core_070_official_compatibility.json` independently shows 17 published and 43 candidate tests passed, zero skips, both combination installations passed, for wheel SHA256 `807ee76f7fb9a1dd58009c6a40af60294384ad92ed44f250f2a90fff8ab67b12`. XDDP published package is explicitly `not_published` (404), while its candidate passed. This evidence does not certify third-party packages or real-business behavior. Exact-head CI run 38886240214 at commit `3eb61c6ab8e5d5d5d9a7ec65008183837dc3dc67` had passed build, malware/artifact scan, clean wheel installs on Python 3.11/3.12/3.13, clean sdist install and official compatibility; test/security job was still running when inspected.

## Open Items

No unresolved source or baseline finding within this feature review. Actual legacy environment was not supplied: source filesystem, installed dependencies, safe test infrastructure, baseline outputs and business-approved expected results remain unverified and outside this feature-review acceptance. Public release and installation verification remain coordinator-owned and are not established by this review.

## Handoff

Independent quality reviewer accepted category coverage, evidence/remediation validity and final baseline disposition. Parent owns deterministic review-run verification/closure and authorized release publication. This acceptance routes release work; it does not replace human business acceptance.

verdict: proceed
reason: Source corrections independently rechecked; final configured baseline and source-identical CI passed; no closure-affecting review concern remains.
evidence: Final baseline acceptance below and work/sessions/2026-10-16_evidence_core_070_validation.md.
required_followup: Parent deterministic closure and release/public-install verification.

## Follow-up independent review: embedded document identity

Reviewed the later working-tree correction in `XRefCatalog.get_document_by_xid`: the fallback embedded catalog now receives the active serving catalog's repository fingerprint and fingerprint basis before document resolution. Embedded content still supplies its original XID and content hash. Existing local/conflict/alias resolution remains before the fallback; no lookup conflict or client validation guard is bypassed.

This fixes the mismatch between active-server startup/session identity and packaged knowledge/template document identity. Full and conditional responses both use `_conditional_document_response` with the active fingerprint. Inspected `subagent_startup.add_document` and `client_cache.load`: strict fingerprint/XID/content-hash checks remain unchanged. This is a provider response correction, not a relaxation of trust checks.

The adoption tests now assert the exact five expected Skill IDs, including the shipped bootstrap Skill, and explicitly retain rejection of the unadopted candidate. This is stronger than merely increasing a count.

Independently executed the bootstrap/client-run test and both affected adoption tests: **3 passed in 16.80s**. Source disposition: **pass-after-fix**, no new source finding. Parent still owns the updated full baseline and runtime quality/closure; this follow-up does not convert pending baseline evidence to success.

## Final baseline acceptance

Independent quality reviewer inspected `.tmp/070-quality-reviewed.log`: **1510 passed, 4 skipped, 108 subtests passed in 584.60s**; xref reported zero issues, Skill lint passed, all four packs passed, tracked runtime audit checked three records successfully, and both project quality baselines passed. Coordinator confirmed terminal exit code zero. Skipped tests remain skips, not passes. The earlier four-failure run above is retained as superseded evidence.

GitHub Actions run [38887141164](https://github.com/synthaicode/XRefKit/actions/runs/38887141164) was independently verified completed/success at source SHA `30a1a971e7203553b8ee27ef881846d5fedf9834`: test/security quality (including declared and resolved dependency audits), build, artifact/malware scan, clean wheel installations on Python 3.11/3.12/3.13, clean sdist installation and official Skill compatibility all succeeded. PyPI publication was skipped; no publication success is inferred. The subsequent HEAD difference inspected at acceptance was only a runtime trace JSON, with no source change.

Final reviewed-wheel compatibility evidence is `work/sessions/2026-10-16_evidence_core_070_reviewed_compatibility.json`, for SHA256 `d30ef901af4715a6a71bd2064fb849612ed15842c5637f5c66f63338819c1c72`: published 17 and candidate 43 tests, zero skips, both combined environments passed. XDDP published-package absence is explicit and its candidate passed. Final build, artifact inspection and Twine succeeded. These bounded results resolve `baseline-final`; they do not validate an unavailable real legacy environment or approve its business expectations.
