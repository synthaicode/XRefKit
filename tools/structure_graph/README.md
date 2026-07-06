<!-- xid: 5ACA25908C18 -->
<a id="xid-5ACA25908C18"></a>

# XRefKit.StructureGraph

Deterministic C# structure-graph extractor built on Roslyn
(`MSBuildWorkspace`). Emits a decomposition-free, DocID-keyed relation graph
of a .NET codebase plus optional semantic inventories, as JSON consumed by
the Python report tools in the [XRefKit](https://github.com/synthaicode/XRefKit)
repository.

## Install

```powershell
dotnet tool install --global XRefKit.StructureGraph
```

## Usage

```powershell
dotnet xrefkit-graph --out graph.json [--root <repo-root>] [--attributes <attrs.json>] [--di <di.json>] [--invocations <inv.json>] [--decl <decl.json>] <sln-or-csproj> [...]
```

Restore the target codebase first (`dotnet restore <sln-or-csproj>`), or
framework-dependent facts (DI, logging, config) come back silently empty.
A .NET SDK must be installed: the extractor resolves MSBuild from the
registered SDK at runtime.

## Outputs

- relation graph (`--out`): nodes project / namespace / type / method /
  property / field; edges contains / declares / calls / implements /
  inherits
- `--attributes`: custom-attribute applications with constant-folded
  constructor and named-argument values
- `--di`: DI service / implementation / lifetime registrations
- `--invocations`: logging / config-binding / pipeline / reflection /
  transaction call shapes
- `--decl`: declaration facts (async without CancellationToken, static
  mutable state, locks, DbSet, `#if`, TFMs)

## Version And Schema Compatibility

All outputs carry `schema: xrefkit.structure_graph/v1`. The package major
version tracks the schema major version: 0.x and 1.x packages emit schema
v1. The XRefKit Python report tools expect the schema version they were
checked out with; keep the tool and the repository in step.

## License

MIT. Source: `tools/structure_graph/` in the XRefKit repository.
