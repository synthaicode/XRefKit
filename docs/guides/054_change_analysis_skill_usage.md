<!-- xid: C5A8F13D7E21 -->
<a id="xid-C5A8F13D7E21"></a>

# Change Analysis Skill Usage

This page explains how to request the change-analysis skill that generates Markdown investigation notes for code changes.

## Target Skill

- `.NET application structure analysis`:
  - skill: `dotnet_change_analysis`
  - definition: `skills/dotnet_change_analysis/SKILL.md`

For applications whose behavior is controlled by external definitions
(XML, YAML, JSON, properties, framework-specific configuration), apply the
canonical viewpoints in
[External-definition change analysis viewpoints](../../knowledge/source_analysis/130_external_definition_change_analysis_viewpoints.md#xid-4D91A26BE301)
within the same analysis run; there is no separate skill for that case.

## Minimum Request Format

Include the following items in the request:

- target path
- change objective
- scope
- output path

## Request Template

```text
Use `dotnet_change_analysis` to analyze `<target_path>` and create a Markdown change-analysis note.
Change objective: `<change objective>`
Scope: `<scope>`
Output path: `<output_path>`
```

## .NET Request Examples

### Example 1: feature change

```text
Use `dotnet_change_analysis` to analyze `C:\dev\sample-dotnet-app` and create a Markdown change-analysis note.
Change objective: add approval-step branching to the order registration flow
Scope: `src/App.Web`, `src/App.Application`, related tests
Output path: `work/order-approval-change-analysis.md`
```

### Example 2: logging and performance impact

```text
Use `dotnet_change_analysis` to analyze `C:\dev\sample-dotnet-app` and create a Markdown change-analysis note.
Change objective: change batch execution logging and confirm performance and resource impact
Scope: batch startup path, background workers, logging configuration, related repositories
Output path: `work/batch-logging-impact.md`
```

### Example 3: custom attribute investigation

```text
Use `dotnet_change_analysis` to analyze `C:\dev\sample-dotnet-app` and create a Markdown change-analysis note.
Change objective: change behavior controlled by custom attributes on application services
Scope: custom attribute definitions, consuming framework code, affected services, related tests
Output path: `work/custom-attribute-change-analysis.md`
```

## Japanese Request Examples

### Example 1: .NET

```text
`dotnet_change_analysis` を使って `C:\dev\sample-dotnet-app` を解析し、受注登録の承認分岐追加に関する調査MDを作成して。
対象範囲は `src/App.Web`、`src/App.Application`、関連テスト。
出力先は `work/order-approval-change-analysis.md`。
```

## Scope Writing Rule

- Name concrete files, modules, services, or directories when possible.
- Mention related tests if the change should preserve current behavior.
- Mention logging, custom attributes, concurrency, performance, or resource concerns explicitly when they are part of the change objective.
- For external-definition-driven applications, mention both the definition files and the consuming code area.

## Output Expectation

The generated Markdown note is expected to include:

- current structure or definition summary
- impacted boundaries
- unresolved items
- viewpoint-based checks
- evidence paths

## Related

- [Skill authoring with xref](013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
