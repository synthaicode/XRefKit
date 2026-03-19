<!-- xid: 8C4D2A7E5103 -->
<a id="xid-8C4D2A7E5103"></a>

# IPA Test Viewpoint Supplement

This page supplements test viewpoints using IPA materials on non-functional requirements.

## Basis

IPA explains that non-functional requirements should be listed comprehensively and classified, and its non-functional requirements grade organizes them into major categories.

Relevant IPA references:

- IPA non-functional requirements grade introduction:
  - https://www.ipa.go.jp/archive/digital/iot-en-ci/jyouryuu/hikinou/ent03-b.html
- IPA survey excerpt showing the six major categories:
  - availability
  - performance and scalability
  - operability and maintainability
  - migration
  - security
  - system environment and ecology
  - https://www.ipa.go.jp/archive/digital/iot-en-ci/jyouryuu/hikinou/ps6vr700000077he-att/000004623.pdf

## Mapping To Test Viewpoints

| IPA concern | Suggested test viewpoints |
|------|------|
| availability | long run, failure, recovery, failover, business-cycle continuity |
| performance and scalability | load, peak load, concurrency, sustained throughput |
| operability and maintainability | operational-cycle checks, monitoring-linked checks, restart or maintenance-window checks |
| migration | migration rehearsal, restart and fallback checks where migration affects operation |
| security | security path, authorization failure path, sensitive-data handling, audit path |
| system environment and ecology | environment-specific behavior, scheduling, resource ceilings, operational timing constraints |

## Rule

- If the target system has operational continuity, periodic batch, or service-level concerns, do not limit test viewpoints to only unit and normal-path checks.
- At least consider `long_run`, `load`, `failure`, and `business_cycle` explicitly.
