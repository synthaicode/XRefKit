<!-- xid: 30E6A4F6F3AB -->
<a id="xid-30E6A4F6F3AB"></a>

# C# Custom Framework Analysis Criteria

This page defines C#-specific source-analysis viewpoints used when an application relies on an application-specific framework.

This page builds on:

- [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](../source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)

For framework structure analysis, the common criteria reference selects its
structural core and Planning / Unknown rules. Load an additional review topic
from that entry point only when its axis is needed for the current boundary
investigation; a full source review still follows the language review spec and
all its active categories. This does not infer public-framework semantics or
expand structure analysis into defect judgment.

## C#-Specific Viewpoints

| Viewpoint | What to confirm |
|------|------|
| Entry-point patterns | `Program.cs`, host startup, controller equivalents, hosted services, batch runners, message handlers, schedulers |
| Registration patterns | DI registration extensions, service locators, factories, handler registries, assembly scanning, reflection-based wiring |
| Type-shape conventions | required base classes, interfaces, attributes, partial classes, generic base patterns, naming rules |
| Async and execution model | `Task` usage, cancellation flow, sync-over-async risks, thread-affinity assumptions |
| Data and serialization patterns | DTOs, entities, mappers, serializers, custom binders, persistence wrappers, transaction helpers |
| Configuration patterns | `appsettings`, options-like wrappers, custom loaders, environment overrides, static configuration access |
| Project and assembly boundaries | which projects or assemblies represent framework, shared libraries, and application code |
| Test integration patterns | test host bootstrapping, framework setup, fake infrastructure, and fixture conventions |

## Review Rule

When reviewing C# code on a custom framework:

- verify attribute semantics from local framework code or usage examples
- verify registration and runtime preconditions from local startup or framework bootstrap code
- verify async, serialization, and configuration behavior from local framework implementation, not from ASP.NET Core assumptions

## Unknown Rule

- If C#-specific framework registration, lifecycle, or attribute semantics cannot be confirmed, record `unknown`.
- Do not invent ASP.NET Core-like behavior unless local evidence proves the custom framework behaves that way.
