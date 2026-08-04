<!-- xid: 7A2F4C8D2201 -->
<a id="xid-7A2F4C8D2201"></a>

# Service Catalog Knowledge Schema

This fragment defines the canonical Knowledge shape for identifying which
existing service owns a requested change before requirements are finalized.
It is a schema and decision rule, not an inventory of any particular system.

## Purpose

Use the catalog to map a request to the responsible existing service, identify
candidate services when responsibility is shared, and make missing ownership
evidence visible before requirements flow into planning or design.

## Required Service Record

Each service record should contain:

- `service_id` and stable name;
- business purpose and responsibility boundary;
- owning group or decision owner;
- supported business activities and request types;
- entrypoints: API, message, batch, screen, file, scheduled job, or CLI;
- owned components, databases, schemas, queues, files, and configuration;
- provided and consumed interfaces;
- authoritative data and read/write responsibility;
- known local implementation and test patterns;
- lifecycle, deployment unit, and environment variants;
- evidence references, validity/recheck condition, and unresolved ownership;
- `status`: `current`, `candidate`, `retired`, or `unknown`.

## Requirement Routing Rule

Requirements work must select the responsible service from catalog evidence.
If multiple services are candidates, record the responsibility split and the
decision owner. Do not infer ownership from folder names, namespace names, or a
single call site. If the catalog is missing or stale, the service assignment is
`unknown` and blocks requirement closure until resolved or explicitly scoped
out.

## Reuse Boundary

The catalog records service responsibility and routing evidence. It does not
approve business requirements, prescribe implementation, or replace the data
flow record defined by the companion Knowledge fragment.
