<!-- xid: 7B3E5D1A6101 -->
<a id="xid-7B3E5D1A6101"></a>

# IPA Release Activity Catalog

This page defines release-related activities that should be considered when creating a release policy, using IPA materials as the basis.

## Basis

IPA states that non-functional requirements should be listed comprehensively and classified, and that major items should be decided first before the remaining items are detailed.

Relevant IPA sources:

- Non-functional requirements grade introduction:
  - https://www.ipa.go.jp/archive/digital/iot-en-ci/jyouryuu/hikinou/ent03-b.html
- IPA material on quantitative reliability improvement during operation:
  - https://www.ipa.go.jp/archive/files/000045090.pdf
- IPA agile model contract page, which notes continuous release after the first release with coordination between development and operations:
  - https://www.ipa.go.jp/digital/model/agile20200331.html

## Release Activity Areas

| Activity area | What to define in release policy |
|------|------|
| Environment split | define release activities separately for test environment and production environment |
| Release scope confirmation | what is included in the release, excluded, and deferred |
| Release timing and sequence | release window, order, dependency order, phased rollout, and business timing constraints |
| Cutover procedure | deployment steps, switchover order, data migration order, and operator actions |
| Rollback and fallback | rollback trigger, fallback path, restoration method, and decision authority |
| Data migration and reconciliation | migration target, validation method, reconciliation check, and post-migration confirmation |
| Operational readiness | monitoring readiness, operational procedure readiness, staffing, and communication readiness |
| Verification before release | completion conditions for unit, integration/regression, release verification, and unresolved-item handling |
| Monitoring after release | what signals are watched immediately after release, thresholds, and observation window |
| Incident and failure response | how failures are detected, triaged, escalated, recovered, and communicated |
| Business-cycle considerations | daily, weekly, monthly, closing, batch, or periodic operational timing that affects release planning |
| Long-run and load considerations | sustained operation, peak load, performance degradation, and capacity risk after release |
| Stakeholder communication | who is informed before, during, and after release |

## Planning Rule

Release policy should not stop at "how to deploy."

It should at least define:

- test-environment release activities
- production-environment release activities
- release timing and execution order
- rollback and fallback conditions
- operational and monitoring preparation
- verification gates before release
- post-release observation and incident response
- business-cycle and long-run timing constraints where applicable

## Trace Rule

- Each release-policy decision should cite the current operational artifact, source finding, or business constraint used as its basis.
- If a required activity area is not applicable, record `out_of_scope` with a reason.
- If the project cannot confirm a required activity area, record `unknown`.

## Environment Rule

- Release policy must distinguish at least:
  - test environment release
  - production environment release
- Do not reuse the same release steps blindly across environments.
- If cutover, verification, rollback, observation window, or communication differs by environment, record the difference explicitly.
