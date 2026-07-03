<!-- xid: B4F8D2A91C03 -->
<a id="xid-B4F8D2A91C03"></a>

# Maverick.NET Friendbook XML-command Structure Findings

This finding records the current structure of the Maverick.NET 1.0 Friendbook
sample as an XML-command-routed .NET Framework-era application. It is used as a
current source-structure finding for Skill evaluation and design-time routing
where XML command maps, controller class strings, view/result tokens, and
request field names are runtime binding authorities.

## Status

| Field | Value |
| --- | --- |
| Target identity | Maverick.NET 1.0 Friendbook sample |
| Source scope | Friendbook sample application from the Maverick.NET 1.0 source snapshot |
| Analysis kind | `dotnet_structure`, `custom_framework_xml_routing` |
| Current status | Current for the 2026-07-03 source snapshot |
| Last verified on | 2026-07-03 |
| Producer Skill | `dotnet_change_analysis` |
| Source basis | SourceForge Maverick.NET 1.0 source bundle mirrored under `sources/web/sourceforge.net/maverick-net/Maverick.NET-1.0.zip` and local structure analysis report under `work/reports/2026-07-03_maverick_friendbook_dotnet_change_analysis.md` |

## Structure Pivots

| Pivot | Runtime authority | Behavior controlled | Change-sensitive tokens |
| --- | --- | --- | --- |
| XML command map | `maverick.xml` command declarations | URL/command identity to controller, view, and navigation result wiring | Command names, controller class names, view names, result names, and forward targets |
| Controller classes | Friendbook controller source files activated by XML commands | Action execution and result selection | Class names, namespaces, inheritance from Maverick command/controller types, request field names |
| View and result definitions | XML view/result entries and page/template targets | Rendered output and navigation path | View names, JSP/ASPX/page targets, redirect/forward strings |
| Model/request binding | Request parameters consumed by controller code | Runtime input state and validation boundary | Form field names, model keys, request parameter strings |

## Route / Usecase Trace Coverage

| Entry identity | Structural authority | Binding mechanism | Executable owner | Output boundary | Verification state |
| --- | --- | --- | --- | --- | --- |
| Friendbook command routes | XML command map | XML string to controller type and result/view tokens | Friendbook controller classes | XML-declared views and forwards | Cross-file path recorded; runtime execution not verified |
| Friendbook form actions | Page/form action strings and XML command names | Request field names and command tokens | Controller methods reading request state | Result selector and view target | Representative trace recorded; browser flow not verified |

## Implicit Runtime Bindings

| Binding | Producer | Consumer | Silent breakage mode |
| --- | --- | --- | --- |
| XML command name | XML command declaration and page/form links | Maverick command dispatcher | Rename or drift leaves URL/action unresolved without C# compiler diagnostics. |
| Controller class string | XML command declaration | Maverick reflection or factory activation | Class rename, namespace drift, or assembly movement breaks activation. |
| Result/view token | Controller result selection and XML view/result declarations | Maverick view resolver | Token drift returns the wrong navigation target or fails at runtime. |
| Request field name | HTML/form markup | Controller request parameter lookup | Field rename changes runtime input without compiler diagnostics. |
| Page/template path | XML view/result declaration | Web runtime and view resolver | Move or rename breaks rendering at runtime. |

## Prohibited Change Rules

| Rule | Strength | Basis | Safe alternative |
| --- | --- | --- | --- |
| Do not rename XML command names without updating all page/form callers and dispatch references. | hard | Command identity is string-bound through XML and request URLs/actions. | Update XML, callers, and route/usecase trace together. |
| Do not rename or move controller classes referenced by XML without updating the XML class token and verifying runtime activation. | conditional | Controller activation is non-compiler-enforced when the XML token is the authority. | Change code and XML in the same design item, then verify dispatch. |
| Do not rename result/view tokens independently from controller return values and XML result/view declarations. | hard | Result selection is token-matched across controller and XML. | Update both sides and record the trace change. |
| Do not rename form/request field names without updating controller request lookups and related tests. | conditional | Runtime input binding is field-name based. | Update markup, controller lookup, and test case granularity together. |

## Selection Metadata

| Field | Value |
| --- | --- |
| Framework family | .NET Framework-era custom MVC framework |
| Routing authority | XML command map |
| Entry binding modes | URL/action string, XML command name, form field name |
| Controller binding modes | XML class token, reflection/factory activation |
| View binding modes | XML result/view token and page/template path |
| State and persistence binding modes | Request parameters and model keys observed from controller/page coupling; persistence detail not verified |
| Change-sensitive tokens | Command names, controller class tokens, result/view names, request field names, page/template paths |
| Reuse purpose | Evaluation fixture for non-standard .NET structure analysis and XML-routed runtime binding |

## Unresolved Verification

- Build and runtime execution were not verified.
- Browser-level Friendbook usecase behavior was not verified.
- Security assessment is out of scope for this finding.
- C# defect review is out of scope for this finding.
- Persistence and transaction behavior were not fully verified from runtime evidence.

## Knowledge Relations

- depends_on: [Dotnet change analysis viewpoints](120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)

## Sources

- source_type: archive
- source_path: ../../sources/web/sourceforge.net/maverick-net/Maverick.NET-1.0.zip
- source_locator: Friendbook sample application, `maverick.xml`, controller source files, view/result declarations
- extracted_at: 2026-07-03
- analysis_source: ../../work/reports/2026-07-03_maverick_friendbook_dotnet_change_analysis.md
