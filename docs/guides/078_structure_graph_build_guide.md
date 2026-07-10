<!-- xid: 8B3E5D0A94C7 -->
<a id="xid-8B3E5D0A94C7"></a>

# Structure Graph Build Guide (Binary Setup After A Source-Level Copy)

A source-level copy of this repository (git clone, plain file copy, or
XRefKit MCP client-tool materialization) does not carry compiled binaries:
`tools/structure_graph/bin/` and `obj/` are gitignored. The C# extractor in
`tools/structure_graph/` must therefore be built once on the new machine
before any of the semantic-inventory tools work. This page is that build
procedure.

## When This Is Required

`tools/structure_graph` is the only compiled tool in `tools/`. Everything
that consumes its output fails or comes back empty without it:

| Consumer | Needs |
| --- | --- |
| `tools/structure_graph_report.py` | the relation graph (`graph.json`) |
| `tools/attribute_inventory_report.py` | `--attributes` output |
| `tools/di_registration_report.py` | `--di` output |
| `tools/invocation_facts_report.py` | `--invocations` output |
| `tools/declaration_facts_report.py` | `--decl` output |
| `tools/test_coverage_reach.py`, `tools/where_seed_traversal.py` | the relation graph |
| Skills `dotnet_change_analysis`, `qa_gate_review` | the tools above |

The pure-Python tools in `tools/` and the `xrefkit` runtime do not need this
build. They need Python 3.11+ and the Python dependencies declared by the
package.

## Option A: Install From NuGet (Preferred)

The extractor is published to nuget.org as the dotnet tool
`XRefKit.StructureGraph` (command name `dotnet-xrefkit-graph`), packed from
`tools/structure_graph/` in this repository by the
`structure-graph-nuget-publish` workflow. On a machine with nuget.org
access, no build is needed:

```powershell
dotnet tool install --global XRefKit.StructureGraph
dotnet xrefkit-graph --out graph.json <sln-or-csproj>
```

The tool package bundles its dependencies, so install-time restore does not
touch nuget.org beyond fetching the package itself. A .NET 10 SDK is still
required at run time (the extractor resolves MSBuild from the registered
SDK, and the target codebase must be restored anyway).

Closed networks: mirror the same `.nupkg` through the XRefKit MCP `/dist`
routes (`--dist-extra-dir`), then install from the downloaded folder
without any feed access:

```powershell
dotnet tool install --tool-path .xrefkit/tools --add-source <download-dir> XRefKit.StructureGraph
.xrefkit/tools/dotnet-xrefkit-graph --out graph.json <sln-or-csproj>
```

Package-to-schema compatibility: package majors 0.x and 1.x emit schema
`xrefkit.structure_graph/v1`; the publish workflow enforces that rule at
tag time.

## Option B: Build From Source

### Prerequisites

- .NET SDK 10.0.1xx or later (`StructureGraph.csproj` targets `net10.0`).
  Verify with `dotnet --list-sdks`.
- NuGet package access (nuget.org or a private feed) for the first restore:
  `Microsoft.Build.Locator`, `Microsoft.CodeAnalysis.CSharp.Workspaces`,
  `Microsoft.CodeAnalysis.Workspaces.MSBuild`.

### Build

From the repository root:

```powershell
dotnet build tools/structure_graph/StructureGraph.csproj -c Release
```

Output lands at:

```text
tools/structure_graph/bin/Release/net10.0/StructureGraph.exe
```

(`StructureGraph` without `.exe` on Linux/macOS.)

#### Expected warnings

`NU1903` (known vulnerability advisory for the transitive
`Microsoft.Build.Tasks.Core` 17.7.2) is expected at the current package
pins and does not fail the build. The extractor runs MSBuild assemblies
resolved from the locally registered SDK at runtime
(`MSBuildLocator.RegisterDefaults()`), not the flagged transitive copy.
Revisit the pins when the Roslyn workspace packages update.

### Verify

Running the binary without arguments prints the usage line to stderr and
exits with code 2 (by design — no output file was requested):

```powershell
tools/structure_graph/bin/Release/net10.0/StructureGraph.exe
```

```text
usage: StructureGraph --out <graph.json> [--root <repo-root>] [--attributes <attrs.json>] [--di <di.json>] [--invocations <inv.json>] [--decl <decl.json>] <sln-or-csproj> [...]
```

### Run

Either invoke the built binary directly (path above), or build-and-run in
one step:

```powershell
dotnet run --project tools/structure_graph -c Release -- --out graph.json <sln-or-csproj>
```

Before extracting facts from a target codebase, restore that codebase first
(`dotnet restore <sln-or-csproj>`), or framework-dependent facts (DI,
logging, config) come back silently empty — see `tools/README.md`
("Restore before Roslyn").

## Machines Without NuGet Access

If the copy destination cannot reach any NuGet feed:

1. Mirror the published `.nupkg` through the XRefKit MCP `/dist` routes and
   install with `--add-source <download-dir>` as in Option A. This is the
   preferred offline path: the tool package bundles its dependencies.
2. Or build on a connected machine and copy the entire
   `tools/structure_graph/bin/Release/net10.0/` directory to the same path
   on the destination. The destination still needs the .NET 10 runtime or
   SDK (the SDK is required anyway to restore the *target* codebase for
   extraction).
3. Or run the extraction on the connected machine and transfer only the
   emitted JSON outputs (`graph.json`, `attrs.json`, ...): the Python
   report tools consume precomputed output and need no binary.

## Publishing (Maintainers)

Publishing runs from this repository (monorepo publishing; no separate
repository). Two workflows mirror the Ksql.Linq.Cli release flow:

| Trigger | Workflow | Destination |
| --- | --- | --- |
| tag `structure-graph-vX.Y.Z` | `.github/workflows/structure-graph-nuget-publish.yml` | nuget.org (needs `NUGET_API_KEY` secret) |
| tag `structure-graph-vX.Y.Z-rc.N` or manual dispatch | `.github/workflows/structure-graph-publish-github-packages.yml` | GitHub Packages |

Both pack `tools/structure_graph/StructureGraph.csproj` with
`PackageVersion` taken from the tag and smoke-test the installed tool
(no-arg run must print the usage line). The nuget.org workflow additionally
fails the release if the package major does not match the emitted schema
major (`xrefkit.structure_graph/v<N>` in `Program.cs`), except during the
pre-1.0 era (major 0).

## Note For XRefKit MCP Clients

The XRefKit MCP client-tool distribution (`/dist`, `get_client_tool_*`)
ships Python files only; neither the structure_graph C# source nor its
binaries are included. A remote client that needs structure-graph facts
should install the NuGet tool (Option A, or its `/dist`-mirrored `.nupkg`
form), or receive precomputed graph JSON as in the previous section.

## Related

- [Structure graph as TM coverage backstop](../../knowledge/source_analysis/160_structure_graph_tm_backstop.md#xid-163AD9936979)
- [Change analysis skill usage](054_change_analysis_skill_usage.md#xid-C5A8F13D7E21)
