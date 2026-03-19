<!-- xid: 5F21C8A41002 -->
<a id="xid-5F21C8A41002"></a>

# Custom Framework Common Criteria

This page defines language-neutral viewpoints for analyzing an application-specific framework.

## Priority Rule

When a custom framework is present, use evidence in the following order:

1. current application code
2. local design and operational documents
3. custom framework base code
4. existing application usage examples
5. general language or platform knowledge

General language or platform knowledge is supplementary only.

## Framework Viewpoints

| Viewpoint | What to confirm |
|------|------|
| Framework lifecycle | initialization, execution flow, transaction or unit-of-work flow, post-processing, and shutdown behavior |
| Framework extension points | hooks, registration points, base types, handlers, conventions, or plug-in points intended for customization |
| Convention rules | placement, naming, registration, inheritance, packaging, or configuration conventions required by the framework |
| Dependency mechanism | how the framework resolves or provides dependencies |
| Data access mechanism | framework-provided persistence, transaction, or query behavior |
| Configuration mechanism | how framework configuration is loaded and overridden |
| Error and logging mechanism | framework-level error translation, logging, and audit behavior |
| Security mechanism | framework-provided identity, authorization, masking, and execution-context behavior |
| Test mechanism | framework-specific test harnesses, setup assumptions, and test doubles |
| Change boundary | where application changes are allowed versus where framework code should remain untouched |

## Planning Rule

Planning should identify framework lifecycle, extension points, and convention rules before defining a modification policy.

## Unknown Rule

- If framework lifecycle or extension points cannot be confirmed, record `unknown`.
- Do not assume public-framework behavior unless local evidence proves the custom framework behaves that way.
