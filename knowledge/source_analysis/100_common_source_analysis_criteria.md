<!-- xid: 5F21C8A41001 -->
<a id="xid-5F21C8A41001"></a>

# Common Source Analysis Criteria

This page defines language-neutral viewpoints for analyzing an existing codebase before planning, design, or review.

## Core Viewpoints

| Viewpoint | What to confirm |
|------|------|
| Entry points | where execution starts and how requests, jobs, or events enter the system |
| Responsibility split | how behavior is divided across layers, modules, services, or components |
| Dependency direction | which components depend on which others, and whether the direction is intentional |
| Extension points | where new behavior is naturally added without violating the current structure |
| Data boundary | where input, output, persistence, and mapping boundaries exist |
| Configuration boundary | where settings are loaded, overridden, and consumed |
| Error boundary | where failures are handled, translated, retried, or surfaced |
| Security boundary | where authentication, authorization, secret handling, and sensitive-data controls apply |
| Performance-sensitive paths | where expensive or high-frequency execution occurs |
| Test boundary | how unit, integration, regression, and edge-case tests are organized |
| Application/framework boundary | what belongs to reusable framework mechanisms versus application-specific code |

## Planning Rule

Planning should use these viewpoints to produce a modification policy that follows the current codebase structure by default.

## Unknown Rule

- If a core viewpoint cannot be confirmed, record `unknown`.
- Do not invent a cleaner target structure unless the current structure and deviation reason are both explicit.
