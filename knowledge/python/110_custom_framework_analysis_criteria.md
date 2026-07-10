<!-- xid: A9B7C6D5E4F2 -->
<a id="xid-A9B7C6D5E4F2"></a>

# Python Custom Framework Analysis Criteria

This page defines Python-specific viewpoints used when an application relies on
an application-specific framework.

This page builds on:

- [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](../source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)

## Python-Specific Viewpoints

| Viewpoint | What to confirm |
|------|------|
| Entry-point patterns | ASGI/WSGI apps, CLI commands, workers, schedulers, management commands, notebooks, scripts |
| Registration patterns | decorators, routers, dependency providers, plugin registries, settings modules, import scanning |
| Type-shape conventions | base classes, protocols, dataclasses, Pydantic models, mixins, naming rules |
| Async and execution model | event-loop ownership, task lifecycle, sync/async adapters, cancellation flow |
| Data and serialization patterns | schemas, serializers, ORM models, migrations, mappers, DataFrame transforms |
| Configuration patterns | environment variables, settings objects, `.env`, config files, secrets, runtime overrides |
| Package and module boundaries | framework packages, reusable libraries, application modules, plugin modules |
| Test integration patterns | fixtures, app factories, dependency overrides, fake infrastructure, async test setup |

## Review Rule

When reviewing Python code on a custom framework:

- verify decorator, registration, dependency-injection, and plugin semantics
  from local framework code or usage examples
- verify async, serialization, settings, and lifecycle behavior from local
  implementation, not from Flask, Django, FastAPI, Celery, or pytest
  assumptions
- treat import-order and auto-discovery behavior as evidence-sensitive

## Unknown Rule

- If Python-specific framework registration, lifecycle, or decorator semantics
  cannot be confirmed, record `unknown`.
- Do not invent public-framework behavior unless local evidence proves the
  custom framework behaves that way.
