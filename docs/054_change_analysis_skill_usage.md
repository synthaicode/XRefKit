<!-- xid: C5A8F13D7E21 -->
<a id="xid-C5A8F13D7E21"></a>

# Change Analysis Skill Usage

This page explains how to request the change-analysis skills that generate Markdown investigation notes for code changes.

## Target Skills

- `.NET application structure analysis`:
  - skill: `dotnet_change_analysis`
  - definition: `skills/dotnet_change_analysis/SKILL.md`
- `External-definition-driven application structure analysis`:
  - skill: `external_definition_change_analysis`
  - definition: `skills/external_definition_change_analysis/SKILL.md`

## Skill Selection Rule

- Use `dotnet_change_analysis` when the main structure is expressed in source code and .NET project files.
- Use `external_definition_change_analysis` when XML, YAML, JSON, properties files, or framework-specific configuration files control routing, flow, mapping, validation, scheduling, or activation.
- If both are present, choose the one that controls the intended change most directly.
- If the intended change spans both code-side and external-definition-side control, start with `external_definition_change_analysis` and explicitly mention the related code area.

## Minimum Request Format

Include the following items in the request:

- target path
- change objective
- scope
- output path

## Request Template

```text
Use `<skill_name>` to analyze `<target_path>` and create a Markdown change-analysis note.
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

## External-Definition Request Examples

### Example 1: Struts XML transition change

```text
Use `external_definition_change_analysis` to analyze `C:\dev\legacy-webapp` and create a Markdown change-analysis note.
Change objective: add an approval transition defined in Struts XML
Scope: `struts-config.xml`, related action classes, validators, transition targets, related tests
Output path: `work/struts-approval-transition-analysis.md`
```

### Example 2: external validation rule change

```text
Use `external_definition_change_analysis` to analyze `C:\dev\legacy-webapp` and create a Markdown change-analysis note.
Change objective: change validation rules defined outside code and confirm activation conditions
Scope: validation XML, consuming framework components, affected screens, related tests
Output path: `work/validation-rule-change-analysis.md`
```

### Example 3: scheduler and retry policy change

```text
Use `external_definition_change_analysis` to analyze `C:\dev\integration-app` and create a Markdown change-analysis note.
Change objective: change scheduler and retry behavior driven by external configuration
Scope: scheduler definitions, retry settings, consuming jobs, logging, monitoring, related tests
Output path: `work/scheduler-retry-change-analysis.md`
```

## Japanese Request Examples

### Example 1: .NET

```text
`dotnet_change_analysis` を使って `C:\dev\sample-dotnet-app` を解析し、受注登録の承認分岐追加に関する調査MDを作成して。
対象範囲は `src/App.Web`、`src/App.Application`、関連テスト。
出力先は `work/order-approval-change-analysis.md`。
```

### Example 2: external definition

```text
`external_definition_change_analysis` を使って `C:\dev\legacy-webapp` を解析し、Struts の XML 定義で制御している承認遷移追加の調査MDを作成して。
対象範囲は `struts-config.xml`、関連 Action、validator、遷移先画面、関連テスト。
出力先は `work/struts-approval-transition-analysis.md`。
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
- [Investigation workflow](032_investigation_workflow.md#xid-8B31F02A4001)
