// Structure-graph extractor (prototype) for the XDDP "Where" TM coverage backstop.
//
// Emits a deterministic, decomposition-free relation graph of a .NET codebase,
// keyed by Roslyn documentation comment ids (DocID), per the design in
// knowledge/source_analysis/160_structure_graph_tm_backstop.md.
//
// Scope (v1): source-defined nodes only; internal call edges only.
//   nodes: project, namespace, type, method, property, field
//   edges: contains, declares, calls, implements, inherits
//
// Usage:
//   StructureGraph --out <graph.json> [--attributes <attrs.json>] <project1.csproj> [...]
//
// --attributes additionally emits a deterministic, DocID-keyed inventory of every
// custom-attribute application on a source-declared type / method / property /
// field, with constructor + named argument values resolved by Roslyn (constant
// folded). This is a separate output from the relation graph: attribute facts are
// requirement-independent static facts (the static footprint of otherwise-dynamic
// channels: DI, routing, serialization, mapping), consumed on demand rather than
// wired into traversal. See knowledge/source_analysis/160_structure_graph_tm_backstop.md.

using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.MSBuild;

MSBuildLocator.RegisterDefaults();

return await Run(args);

static async Task<int> Run(string[] args)
{
    string? outPath = null;
    string? root = null;
    string? attrPath = null;
    string? diPath = null;
    string? invPath = null;
    string? declPath = null;
    var inputPaths = new List<string>();
    for (var i = 0; i < args.Length; i++)
    {
        if (args[i] == "--out" && i + 1 < args.Length) { outPath = args[++i]; continue; }
        if (args[i] == "--root" && i + 1 < args.Length) { root = args[++i]; continue; }
        if (args[i] == "--attributes" && i + 1 < args.Length) { attrPath = args[++i]; continue; }
        if (args[i] == "--di" && i + 1 < args.Length) { diPath = args[++i]; continue; }
        if (args[i] == "--invocations" && i + 1 < args.Length) { invPath = args[++i]; continue; }
        if (args[i] == "--decl" && i + 1 < args.Length) { declPath = args[++i]; continue; }
        inputPaths.Add(args[i]);
    }
    if (outPath is null || inputPaths.Count == 0)
    {
        Console.Error.WriteLine("usage: StructureGraph --out <graph.json> [--root <repo-root>] [--attributes <attrs.json>] [--di <di.json>] [--invocations <inv.json>] [--decl <decl.json>] <sln-or-csproj> [...]");
        return 2;
    }
    RootPrefix = root is null ? null : Path.GetFullPath(root).Replace('\\', '/').TrimEnd('/') + "/";

    using var ws = MSBuildWorkspace.Create();
    ws.WorkspaceFailed += (_, e) =>
    {
        if (e.Diagnostic.Kind == WorkspaceDiagnosticKind.Failure)
            Console.Error.WriteLine($"[workspace] {e.Diagnostic.Message}");
    };

    foreach (var p in inputPaths)
    {
        var full = Path.GetFullPath(p);
        // A project may already be loaded transitively (it is referenced by an
        // earlier input). Skip it instead of throwing.
        var normFull = full.Replace('\\', '/');
        if (ws.CurrentSolution.Projects.Any(pr =>
                string.Equals(pr.FilePath?.Replace('\\', '/'), normFull, StringComparison.OrdinalIgnoreCase)))
        {
            Console.Error.WriteLine($"[skip] already loaded: {p}");
            continue;
        }
        Console.Error.WriteLine($"[open] {p}");
        if (full.EndsWith(".sln", StringComparison.OrdinalIgnoreCase))
            await ws.OpenSolutionAsync(full);
        else
            await ws.OpenProjectAsync(full);
    }

    var nodes = new Dictionary<string, Node>();
    var edges = new HashSet<Edge>();
    var externalCallCount = new Dictionary<string, int>();
    var projectInfos = new List<ProjectInfo>();
    // Attribute inventory is collected only when --attributes is requested.
    var attrs = attrPath is null ? null : new List<AttrFact>();
    // DI registration inventory is collected only when --di is requested.
    var dis = diPath is null ? null : new List<DiReg>();
    // Framework invocation facts (logging / config / pipeline) only when requested.
    var invs = invPath is null ? null : new List<InvFact>();
    // Declaration / signature facts (async, static state, DbSet, #if) when requested.
    var sink = declPath is null ? null : new DeclSink();
    // Identifier-like string literal -> distinct member DocIDs that use it.
    // A literal shared by >= 2 members is a name-based coupling (topic / schema /
    // config key) invisible to the call graph; emitted as a `name` shared node.
    var literalUsers = new Dictionary<string, HashSet<string>>();

    // A multi-TFM project appears once per target framework (same csproj, distinct
    // compilation). The graph dedupes nodes/edges, but inventory lists would
    // double-count, so analyze one compilation per csproj. The declared TFMs are
    // still captured from the csproj; per-TFM #if variants remain a known limit.
    var seenProjectFiles = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

    foreach (var project in ws.CurrentSolution.Projects)
    {
        if (project.FilePath is not null && !seenProjectFiles.Add(project.FilePath))
        {
            Console.Error.WriteLine($"[skip] additional TFM of {project.Name}");
            continue;
        }
        var projId = "PRJ:" + project.Name;
        nodes.TryAdd(projId, new Node(projId, "project", project.Name, project.Name, project.Name, null));
        projectInfos.Add(new ProjectInfo(project.Name, RelPath(project.FilePath)));

        // Project-reference edges (dependency direction at the assembly boundary).
        foreach (var pr in project.ProjectReferences)
        {
            var refProj = ws.CurrentSolution.GetProject(pr.ProjectId);
            if (refProj is null) continue;
            var refId = "PRJ:" + refProj.Name;
            nodes.TryAdd(refId, new Node(refId, "project", refProj.Name, refProj.Name, refProj.Name, null));
            edges.Add(new Edge("uses-project", projId, refId));
        }

        var comp = await project.GetCompilationAsync();
        if (comp is null) continue;

        // Active preprocessor symbols for this project's (single) compilation —
        // includes the TFM symbol (NET10_0, NETCOREAPP, ...) and any custom
        // define-constants. Multi-TFM enumeration from the csproj is out of scope.
        if (sink is not null && project.ParseOptions is CSharpParseOptions po)
            sink.ProjectSymbols[project.Name] = po.PreprocessorSymbolNames.OrderBy(s => s).ToList();

        // All declared target frameworks from the csproj (the workspace compiles
        // one TFM at a time; multi-TFM variants are only visible in the project).
        if (sink is not null && project.FilePath is not null)
            sink.ProjectTfms.TryAdd(project.Name, ReadTfms(project.FilePath));

        // 1) Declared symbols (types + members) of this project's source assembly.
        WalkNamespace(comp.Assembly.GlobalNamespace, project.Name, projId, nodes, edges, attrs, sink);

        // Assembly-level attributes ([assembly: InternalsVisibleTo(...)], custom
        // markers). Keyed by "A:<assembly>"; framework-injected ones in generated
        // AssemblyInfo carry an obj/ file path and can be filtered downstream.
        if (attrs is not null)
            foreach (var a in comp.Assembly.GetAttributes())
                EmitAttr(a, "A:" + project.Name, "assembly", project.Name, project.Name, attrs);

        // 2) Call edges from invocations / object creations within source.
        foreach (var tree in comp.SyntaxTrees)
        {
            var model = comp.GetSemanticModel(tree);
            var treeRoot = await tree.GetRootAsync();

            // Conditional-compilation symbols referenced by #if / #elif in this
            // file (build-configuration variants a single pass cannot all see).
            if (sink is not null)
                CollectConditionals(treeRoot, RelPath(tree.FilePath), sink);

            foreach (var node in treeRoot.DescendantNodes())
            {
                // Name-based coupling: identifier-like string literals.
                if (node is LiteralExpressionSyntax lit && lit.IsKind(SyntaxKind.StringLiteralExpression))
                {
                    var val = lit.Token.ValueText;
                    if (NameLike.IsMatch(val) && !NameStop.Contains(val))
                    {
                        var owner = DocId(EnclosingDocIdSymbol(model, node.SpanStart));
                        if (owner is not null)
                        {
                            if (!literalUsers.TryGetValue(val, out var set))
                                literalUsers[val] = set = new HashSet<string>();
                            set.Add(owner);
                        }
                    }
                    continue;
                }

                // writes: member -> field it assigns (state-ownership for the
                // responsibility viewpoint). Reverse gives a field's writer set.
                if (node is AssignmentExpressionSyntax assign &&
                    model.GetSymbolInfo(assign.Left).Symbol is IFieldSymbol fld &&
                    !fld.IsImplicitlyDeclared && fld.Locations.Any(l => l.IsInSource))
                {
                    var writer = DocId(EnclosingDocIdSymbol(model, assign.SpanStart));
                    var fieldId = DocId(fld.OriginalDefinition);
                    if (writer is not null && fieldId is not null)
                        edges.Add(new Edge("writes", writer, fieldId));
                }

                // DI registration sites (AddScoped<,> etc.). Independent of the
                // call-edge logic below: the registration method is external
                // (framework), so it never produces an internal call edge.
                if (dis is not null && node is InvocationExpressionSyntax dinv)
                    TryEmitDi(dinv, model, project.Name, dis);

                // Framework invocation facts: logging / config-binding / pipeline.
                if (invs is not null && node is InvocationExpressionSyntax iinv)
                    TryEmitInv(iinv, model, project.Name, invs);

                // Concurrency-primitive sites: lock statements and Interlocked /
                // Monitor calls (synchronization surface for viewpoint 16).
                if (sink is not null)
                {
                    if (node is LockStatementSyntax)
                        AddConcSite("lock", "lock", node, model, project.Name, sink);
                    else if (node is InvocationExpressionSyntax cinv)
                        TryEmitConc(cinv, model, project.Name, sink);
                }

                IMethodSymbol? callee = node switch
                {
                    InvocationExpressionSyntax inv =>
                        model.GetSymbolInfo(inv).Symbol as IMethodSymbol,
                    ObjectCreationExpressionSyntax oc =>
                        model.GetSymbolInfo(oc).Symbol as IMethodSymbol,
                    _ => null,
                };
                if (callee is null) continue;

                var caller = EnclosingDocIdSymbol(model, node.SpanStart);
                var callerId = DocId(caller);
                if (callerId is null) continue;

                // Calls to extension methods via instance syntax resolve to a
                // *reduced* symbol whose DocID differs from the declared static
                // method node; map back via ReducedFrom so edges target the node.
                var calleeDef = (callee.ReducedFrom ?? callee).OriginalDefinition;
                var calleeId = DocId(calleeDef);
                if (calleeId is null) continue;

                var inSource = calleeDef.Locations.Any(l => l.IsInSource);
                if (inSource)
                    edges.Add(new Edge("calls", callerId, calleeId));
                else
                    externalCallCount[callerId] = externalCallCount.GetValueOrDefault(callerId) + 1;
            }
        }
    }

    // Emit name nodes only for literals shared by >= 2 distinct members.
    foreach (var (val, users) in literalUsers)
    {
        if (users.Count < 2) continue;
        var nameId = "NAME:" + val;
        nodes.TryAdd(nameId, new Node(nameId, "name", val, val, "(shared)", null));
        foreach (var u in users)
            edges.Add(new Edge("uses-name", u, nameId));
    }

    var payload = new
    {
        schema = "xrefkit.structure_graph/v1",
        generatedAt = DateTimeOffset.UtcNow.ToString("o"),
        projects = projectInfos,
        nodes = nodes.Values.OrderBy(n => n.Id).ToList(),
        edges = edges.OrderBy(e => e.Type).ThenBy(e => e.From).ThenBy(e => e.To).ToList(),
        externalCallCount,
        stats = new
        {
            nodeCount = nodes.Count,
            edgeCount = edges.Count,
        },
    };

    Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
    await File.WriteAllTextAsync(outPath,
        JsonSerializer.Serialize(payload, new JsonSerializerOptions
        {
            WriteIndented = true,
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        }));
    Console.Error.WriteLine($"[done] nodes={nodes.Count} edges={edges.Count} -> {outPath}");

    if (attrPath is not null && attrs is not null)
    {
        var attrPayload = new
        {
            schema = "xrefkit.attribute_inventory/v1",
            generatedAt = DateTimeOffset.UtcNow.ToString("o"),
            projects = projectInfos,
            attributes = attrs
                .OrderBy(a => a.AttributeName)
                .ThenBy(a => a.Target, StringComparer.Ordinal)
                .ToList(),
            stats = new
            {
                applicationCount = attrs.Count,
                distinctAttributeTypes = attrs.Select(a => a.Attribute).Distinct().Count(),
                annotatedTargets = attrs.Select(a => a.Target).Distinct().Count(),
            },
        };
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(attrPath))!);
        await File.WriteAllTextAsync(attrPath,
            JsonSerializer.Serialize(attrPayload, new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            }));
        Console.Error.WriteLine($"[done] attribute applications={attrs.Count} -> {attrPath}");
    }

    if (diPath is not null && dis is not null)
    {
        var diPayload = new
        {
            schema = "xrefkit.di_registrations/v1",
            generatedAt = DateTimeOffset.UtcNow.ToString("o"),
            projects = projectInfos,
            registrations = dis
                .OrderBy(d => d.ServiceType, StringComparer.Ordinal)
                .ThenBy(d => d.File, StringComparer.Ordinal)
                .ThenBy(d => d.Line)
                .ToList(),
            stats = new
            {
                registrationCount = dis.Count,
                byLifetime = dis.GroupBy(d => d.Lifetime)
                    .ToDictionary(g => g.Key, g => g.Count()),
            },
        };
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(diPath))!);
        await File.WriteAllTextAsync(diPath,
            JsonSerializer.Serialize(diPayload, new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            }));
        Console.Error.WriteLine($"[done] di registrations={dis.Count} -> {diPath}");
    }

    if (invPath is not null && invs is not null)
    {
        var invPayload = new
        {
            schema = "xrefkit.invocation_facts/v1",
            generatedAt = DateTimeOffset.UtcNow.ToString("o"),
            projects = projectInfos,
            invocations = invs
                .OrderBy(v => v.Category, StringComparer.Ordinal)
                .ThenBy(v => v.File, StringComparer.Ordinal)
                .ThenBy(v => v.Line)
                .ToList(),
            stats = new
            {
                invocationCount = invs.Count,
                byCategory = invs.GroupBy(v => v.Category)
                    .ToDictionary(g => g.Key, g => g.Count()),
            },
        };
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(invPath))!);
        await File.WriteAllTextAsync(invPath,
            JsonSerializer.Serialize(invPayload, new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            }));
        Console.Error.WriteLine($"[done] invocation facts={invs.Count} -> {invPath}");
    }

    if (declPath is not null && sink is not null)
    {
        var declPayload = new
        {
            schema = "xrefkit.declaration_facts/v1",
            generatedAt = DateTimeOffset.UtcNow.ToString("o"),
            projects = projectInfos,
            asyncMethods = sink.AsyncMethods.OrderBy(a => a.Display, StringComparer.Ordinal).ToList(),
            staticState = sink.StaticState.OrderBy(s => s.Display, StringComparer.Ordinal).ToList(),
            dbSets = sink.DbSets.OrderBy(d => d.Display, StringComparer.Ordinal).ToList(),
            concurrencySites = sink.ConcurrencySites
                .OrderBy(c => c.File, StringComparer.Ordinal).ThenBy(c => c.Line).ToList(),
            conditionalsByFile = sink.ConditionalsByFile
                .OrderBy(kv => kv.Key, StringComparer.Ordinal)
                .ToDictionary(kv => kv.Key, kv => kv.Value.ToList()),
            projectSymbols = sink.ProjectSymbols,
            projectTfms = sink.ProjectTfms,
            stats = new
            {
                asyncCount = sink.AsyncMethods.Count,
                asyncMissingCancellationToken = sink.AsyncMethods.Count(a => !a.HasCancellationToken),
                staticStateCount = sink.StaticState.Count,
                dbSetCount = sink.DbSets.Count,
                concurrencySiteCount = sink.ConcurrencySites.Count,
                conditionalFileCount = sink.ConditionalsByFile.Count,
            },
        };
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(declPath))!);
        await File.WriteAllTextAsync(declPath,
            JsonSerializer.Serialize(declPayload, new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            }));
        Console.Error.WriteLine($"[done] declaration facts async={sink.AsyncMethods.Count} "
            + $"static={sink.StaticState.Count} dbset={sink.DbSets.Count} "
            + $"conc={sink.ConcurrencySites.Count} -> {declPath}");
    }

    return 0;
}

static void WalkNamespace(INamespaceSymbol ns, string project, string projId,
    Dictionary<string, Node> nodes, HashSet<Edge> edges, List<AttrFact>? attrs, DeclSink? sink)
{
    foreach (var t in ns.GetTypeMembers())
        WalkType(t, project, projId, nodes, edges, attrs, sink);
    foreach (var sub in ns.GetNamespaceMembers())
        WalkNamespace(sub, project, projId, nodes, edges, attrs, sink);
}

static void WalkType(INamedTypeSymbol type, string project, string projId,
    Dictionary<string, Node> nodes, HashSet<Edge> edges, List<AttrFact>? attrs, DeclSink? sink)
{
    var typeId = DocId(type);
    if (typeId is null) return;

    var kind = type.TypeKind switch
    {
        TypeKind.Interface => "interface",
        TypeKind.Struct => "struct",
        TypeKind.Enum => "enum",
        _ => "type",
    };
    nodes.TryAdd(typeId, new Node(typeId, kind, type.Name, type.ToDisplayString(), project, FileOf(type)));
    edges.Add(new Edge("contains", projId, typeId));

    if (attrs is not null) CollectAttributes(type, typeId, kind, type.ToDisplayString(), project, attrs);

    // inherits (skip System.Object / ValueType noise)
    var baseId = DocId(type.BaseType?.OriginalDefinition);
    if (baseId is not null && type.BaseType!.SpecialType is not (SpecialType.System_Object or SpecialType.System_ValueType))
        edges.Add(new Edge("inherits", typeId, baseId));

    // implements
    foreach (var iface in type.Interfaces)
    {
        var ifaceId = DocId(iface.OriginalDefinition);
        if (ifaceId is not null) edges.Add(new Edge("implements", typeId, ifaceId));
    }

    // dispatches-to: method-level dynamic-dispatch resolution. A call statically
    // binds to the interface/abstract member, so traversals that follow only the
    // call graph stop at the abstraction. These edges (abstraction member ->
    // concrete implementation) let a traversal cross the dispatch. Roslyn resolves
    // generic interfaces precisely via FindImplementationForInterfaceMember.
    CollectDispatch(type, edges);

    foreach (var member in type.GetMembers())
    {
        switch (member)
        {
            case IMethodSymbol m when m.MethodKind is MethodKind.Ordinary or MethodKind.Constructor:
                AddMember(m, "method", typeId, project, nodes, edges, attrs, sink);
                AddUses(typeId, type, m.ReturnType, edges);
                foreach (var par in m.Parameters) AddUses(typeId, type, par.Type, edges);
                break;
            case IPropertySymbol p:
                AddMember(p, "property", typeId, project, nodes, edges, attrs, sink);
                AddUses(typeId, type, p.Type, edges);
                break;
            case IFieldSymbol f when !f.IsImplicitlyDeclared:
                AddMember(f, "field", typeId, project, nodes, edges, attrs, sink);
                AddUses(typeId, type, f.Type, edges);
                break;
            case INamedTypeSymbol nested:
                WalkType(nested, project, projId, nodes, edges, attrs, sink);
                break;
        }
    }
}

// Method-level dynamic-dispatch edges (abstraction member -> concrete member):
//   - interface implementations, resolved per concrete type via
//     FindImplementationForInterfaceMember (correct for generic interfaces);
//   - virtual/abstract overrides, via OverriddenMethod.
// `from` is keyed by the abstraction member's OriginalDefinition so it matches
// how the call graph keys an interface/virtual callee. Only edges whose
// implementation is declared on *this* type are emitted, so an implementation
// inherited from a base type is recorded once (during the base's walk).
static void CollectDispatch(INamedTypeSymbol type, HashSet<Edge> edges)
{
    if (type.TypeKind is TypeKind.Interface) return;

    foreach (var iface in type.AllInterfaces)
    {
        foreach (var m in iface.GetMembers())
        {
            if (m is not (IMethodSymbol or IPropertySymbol)) continue;
            var impl = type.FindImplementationForInterfaceMember(m);
            if (impl is null || !impl.Locations.Any(l => l.IsInSource)) continue;
            if (!SymbolEqualityComparer.Default.Equals(impl.ContainingType, type)) continue;
            AddDispatch(m, impl, edges);
        }
    }

    foreach (var m in type.GetMembers().OfType<IMethodSymbol>())
        if (m.IsOverride && m.OverriddenMethod is { } ov)
            AddDispatch(ov, m, edges);
}

static void AddDispatch(ISymbol abstraction, ISymbol impl, HashSet<Edge> edges)
{
    var fromId = DocId(abstraction.OriginalDefinition);
    var toId = DocId(impl.OriginalDefinition);
    if (fromId is not null && toId is not null && fromId != toId)
        edges.Add(new Edge("dispatches-to", fromId, toId));
}

// Type-reference (`uses`) edges for the dependency-direction viewpoint: a source
// type T uses another source type U when U appears in T's member signatures
// (field / property / return / parameter types). Named-type leaves are unwrapped
// from arrays and generics; type parameters, external types, and self-references
// are skipped. `calls` / `inherits` / `implements` already carry their relations,
// so this adds only the structural type dependency they miss.
static void AddUses(string fromTypeId, INamedTypeSymbol owner, ITypeSymbol used, HashSet<Edge> edges)
{
    foreach (var leaf in NamedTypeLeaves(used))
    {
        if (SymbolEqualityComparer.Default.Equals(leaf, owner)) continue;
        if (!leaf.Locations.Any(l => l.IsInSource)) continue;
        var toId = DocId(leaf);
        if (toId is not null && toId != fromTypeId)
            edges.Add(new Edge("uses", fromTypeId, toId));
    }
}

// Yield the named-type leaves of a type: unwrap arrays/pointers to the element,
// and a generic type both contributes its definition and recurses its arguments
// (so List<Order> yields List and Order). Type parameters are not leaves.
static IEnumerable<INamedTypeSymbol> NamedTypeLeaves(ITypeSymbol t)
{
    switch (t)
    {
        case IArrayTypeSymbol arr:
            foreach (var l in NamedTypeLeaves(arr.ElementType)) yield return l;
            break;
        case IPointerTypeSymbol ptr:
            foreach (var l in NamedTypeLeaves(ptr.PointedAtType)) yield return l;
            break;
        case INamedTypeSymbol named:
            yield return named.OriginalDefinition as INamedTypeSymbol ?? named;
            foreach (var arg in named.TypeArguments)
                foreach (var l in NamedTypeLeaves(arg)) yield return l;
            break;
    }
}

static void AddMember(ISymbol member, string kind, string typeId, string project,
    Dictionary<string, Node> nodes, HashSet<Edge> edges, List<AttrFact>? attrs, DeclSink? sink)
{
    var id = DocId(member);
    if (id is null) return;
    nodes.TryAdd(id, new Node(id, kind, member.Name, member.ToDisplayString(), project, FileOf(member)));
    edges.Add(new Edge("declares", typeId, id));

    if (attrs is not null) CollectAttributes(member, id, kind, member.ToDisplayString(), project, attrs);
    if (sink is not null) CollectDecl(member, id, project, sink);
}

// Emit AttrFacts for every custom-attribute application on a declared symbol,
// including method parameter and return-value attributes (which carry no DocID
// of their own and so are keyed by the containing method).
static void CollectAttributes(ISymbol symbol, string targetId, string targetKind,
    string targetDisplay, string project, List<AttrFact> attrs)
{
    foreach (var a in symbol.GetAttributes())
        EmitAttr(a, targetId, targetKind, targetDisplay, project, attrs);

    if (symbol is IMethodSymbol method)
    {
        // Return-value attributes ([return: ...]) and parameter attributes
        // ([FromServices], [FromKeyedServices("x")], [Required], ...). Parameters
        // have no DocID; key them by the method DocID and name the parameter in
        // the display so DI / routing / validation footprints stay discoverable.
        foreach (var a in method.GetReturnTypeAttributes())
            EmitAttr(a, targetId, "return", targetDisplay, project, attrs);

        foreach (var p in method.Parameters)
            foreach (var a in p.GetAttributes())
                EmitAttr(a, targetId, "parameter", $"{targetDisplay} :: {p.Name}", project, attrs);
    }
}

// Emit one AttrFact for a single attribute application. Compiler-synthesized
// pseudo-attributes with no source application (e.g. implicit [NullableContext])
// are skipped via ApplicationSyntaxReference.
static void EmitAttr(AttributeData a, string targetId, string targetKind,
    string targetDisplay, string project, List<AttrFact> attrs)
{
    if (a.ApplicationSyntaxReference is null) return;
    var attrClass = a.AttributeClass?.OriginalDefinition;
    var attrId = DocId(attrClass);
    if (attrId is null || attrClass is null) return;

    var ctorArgs = a.ConstructorArguments.Select(RenderConstant).ToList();
    var namedArgs = a.NamedArguments.ToDictionary(kv => kv.Key, kv => RenderConstant(kv.Value));

    string? file = null;
    var line = 0;
    var loc = a.ApplicationSyntaxReference.GetSyntax().GetLocation();
    if (loc.IsInSource)
    {
        file = RelPath(loc.SourceTree?.FilePath);
        line = loc.GetLineSpan().StartLinePosition.Line + 1;
    }

    attrs.Add(new AttrFact(
        targetId, targetKind, targetDisplay, project,
        attrId, attrClass.Name, ctorArgs, namedArgs, file, line));
}

// Detect and record a DI registration site (AddSingleton/AddScoped/AddTransient,
// TryAdd* variants, AddHostedService) on Microsoft.Extensions.DependencyInjection.
// Service / implementation types come from generic type arguments or typeof(...)
// overloads; a factory-lambda registration leaves the implementation unresolved
// (recorded as factory=true). Constructor dependency types of the implementation
// are resolved from its greediest public constructor so a downstream report can
// compute captive-dependency candidates.
static void TryEmitDi(InvocationExpressionSyntax inv, SemanticModel model,
    string project, List<DiReg> dis)
{
    if (model.GetSymbolInfo(inv).Symbol is not IMethodSymbol m) return;
    var name = m.Name;
    if (!DiMethods.Contains(name)) return;
    var ns = m.ContainingNamespace?.ToDisplayString();
    if (ns is null || !ns.StartsWith("Microsoft.Extensions.DependencyInjection", StringComparison.Ordinal))
        return;

    var lifetime =
        name.Contains("Singleton") ? "singleton" :
        name.Contains("Scoped") ? "scoped" :
        name.Contains("Transient") ? "transient" :
        name == "AddHostedService" ? "singleton" : "unknown";

    INamedTypeSymbol? service = null, impl = null;
    var ta = m.TypeArguments;
    if (name == "AddHostedService")
    {
        impl = ta.Length >= 1 ? ta[0] as INamedTypeSymbol : null;
        service = impl;
    }
    else if (ta.Length == 2) { service = ta[0] as INamedTypeSymbol; impl = ta[1] as INamedTypeSymbol; }
    else if (ta.Length == 1) { service = ta[0] as INamedTypeSymbol; impl = service; }

    var factory = inv.ArgumentList.Arguments.Any(a =>
        a.Expression is ParenthesizedLambdaExpressionSyntax
                     or SimpleLambdaExpressionSyntax
                     or AnonymousMethodExpressionSyntax);

    // typeof(IFoo), typeof(Foo) overload when no generic type arguments are present.
    if (service is null && impl is null)
    {
        var typeofs = inv.ArgumentList.Arguments
            .Select(a => a.Expression)
            .OfType<TypeOfExpressionSyntax>()
            .Select(t => model.GetTypeInfo(t.Type).Type as INamedTypeSymbol)
            .Where(t => t is not null)
            .ToList();
        if (typeofs.Count == 2) { service = typeofs[0]; impl = typeofs[1]; }
        else if (typeofs.Count == 1) { service = typeofs[0]; impl = service; }
    }

    var ctorDeps = new List<string>();
    if (impl is not null && !factory)
    {
        var ctor = impl.InstanceConstructors
            .Where(c => c.DeclaredAccessibility == Accessibility.Public)
            .OrderByDescending(c => c.Parameters.Length)
            .FirstOrDefault();
        if (ctor is not null)
            foreach (var p in ctor.Parameters)
                ctorDeps.Add(p.Type.ToDisplayString());
    }

    string? file = null;
    var line = 0;
    var loc = inv.GetLocation();
    if (loc.IsInSource)
    {
        file = RelPath(loc.SourceTree?.FilePath);
        line = loc.GetLineSpan().StartLinePosition.Line + 1;
    }

    dis.Add(new DiReg(
        name, lifetime,
        service?.ToDisplayString(), impl?.ToDisplayString(),
        factory, ctorDeps, project, file, line));
}

// Detect and record a framework invocation fact in one of three categories:
//   logging   ILogger.Log* calls, with the level
//   config    IConfiguration GetSection/GetValue/GetConnectionString/Bind and
//             IServiceCollection Configure<T>, with the key literal / bound type
//   pipeline  IApplicationBuilder Use* middleware calls (order reconstructed by
//             the downstream report from file:line within the enclosing member)
// Each is namespace-gated to keep the match deterministic and low-noise.
static void TryEmitInv(InvocationExpressionSyntax inv, SemanticModel model,
    string project, List<InvFact> invs)
{
    if (model.GetSymbolInfo(inv).Symbol is not IMethodSymbol m) return;
    var name = m.Name;
    var ns = m.ContainingNamespace?.ToDisplayString() ?? "";

    string? category = null, key = null, targetType = null, level = null;

    if (name.StartsWith("Log", StringComparison.Ordinal) &&
        ns.StartsWith("Microsoft.Extensions.Logging", StringComparison.Ordinal))
    {
        category = "logging";
        var suffix = name.Length > 3 ? name[3..] : "";
        level = LogLevels.Contains(suffix) ? suffix : LevelFromArg(inv, model) ?? "(dynamic)";
    }
    else if (ConfigMethods.Contains(name) &&
             (ns.StartsWith("Microsoft.Extensions.Configuration", StringComparison.Ordinal) ||
              ns.StartsWith("Microsoft.Extensions.DependencyInjection", StringComparison.Ordinal) ||
              ns.StartsWith("Microsoft.Extensions.Options", StringComparison.Ordinal)))
    {
        category = "config";
        key = FirstStringLiteral(inv);
        if (m.TypeArguments.Length >= 1) targetType = m.TypeArguments[0].ToDisplayString();
    }
    else if (name.StartsWith("Use", StringComparison.Ordinal) &&
             ns.StartsWith("Microsoft.AspNetCore.Builder", StringComparison.Ordinal))
    {
        category = "pipeline";
    }
    else if (IsDiscovery(name, inv, ns))
    {
        // Reflection / assembly scanning: runtime wiring invisible to the call
        // graph. The fact that a scan happens is deterministic; what it resolves
        // to at runtime is spec-out (viewpoint 7).
        category = "discovery";
        key = FirstStringLiteral(inv);
    }
    else if ((name == "BeginTransaction" || name == "BeginTransactionAsync") &&
             (ns.Contains("EntityFrameworkCore") || ns.StartsWith("System.Data", StringComparison.Ordinal)))
    {
        category = "transaction";
    }
    else
    {
        return;
    }

    var enclosing = EnclosingDocIdSymbol(model, inv.SpanStart);

    string? file = null;
    var line = 0;
    var loc = inv.GetLocation();
    if (loc.IsInSource)
    {
        file = RelPath(loc.SourceTree?.FilePath);
        line = loc.GetLineSpan().StartLinePosition.Line + 1;
    }

    invs.Add(new InvFact(
        category, name, m.ReceiverType?.ToDisplayString(),
        DocId(enclosing), enclosing?.ToDisplayString(),
        key, targetType, level, project, file, line));
}

// Level from a leading LogLevel.Xxx argument to ILogger.Log(level, ...).
static string? LevelFromArg(InvocationExpressionSyntax inv, SemanticModel model)
{
    foreach (var a in inv.ArgumentList.Arguments)
        if (a.Expression is MemberAccessExpressionSyntax ma &&
            model.GetSymbolInfo(ma).Symbol is IFieldSymbol f &&
            f.ContainingType?.Name == "LogLevel")
            return f.Name;
    return null;
}

static string? FirstStringLiteral(InvocationExpressionSyntax inv)
{
    foreach (var a in inv.ArgumentList.Arguments)
        if (a.Expression is LiteralExpressionSyntax lit && lit.IsKind(SyntaxKind.StringLiteralExpression))
            return lit.Token.ValueText;
    return null;
}

// Reflection / scanning call shapes. Method names are specific enough that a
// namespace prefix is a sufficient guard; GetType is gated on a string argument
// to exclude the ubiquitous parameterless object.GetType().
static bool IsDiscovery(string name, InvocationExpressionSyntax inv, string ns)
{
    if ((name == "GetTypes" || name == "GetExportedTypes") &&
        ns.StartsWith("System.Reflection", StringComparison.Ordinal)) return true;
    if (name == "GetAssemblies" && ns.StartsWith("System", StringComparison.Ordinal)) return true;
    if (name == "Scan" && ns.StartsWith("Microsoft.Extensions.DependencyInjection", StringComparison.Ordinal)) return true;
    if (name == "CreateInstance" && ns.StartsWith("System", StringComparison.Ordinal)) return true;
    if (name == "GetType" && inv.ArgumentList.Arguments.Count >= 1 &&
        ns.StartsWith("System", StringComparison.Ordinal)) return true;
    return false;
}

// Declaration/signature facts for a single member: async/Task-returning methods
// (with a CancellationToken-presence flag), static mutable state, and DbSet<T>
// properties. These are requirement-independent facts about the declaration.
static void CollectDecl(ISymbol member, string id, string project, DeclSink sink)
{
    var (file, line) = FileLineOf(member);
    switch (member)
    {
        case IMethodSymbol m when m.IsAsync || IsTaskLike(m.ReturnType):
            var hasCt = m.Parameters.Any(p => IsCancellationToken(p.Type));
            sink.AsyncMethods.Add(new AsyncFact(
                id, m.ToDisplayString(), m.ReturnType.ToDisplayString(),
                m.IsAsync, hasCt, project, file, line));
            break;

        case IFieldSymbol f when f.IsStatic && !f.IsConst && !f.IsReadOnly:
            sink.StaticState.Add(new StaticFact(
                id, f.ToDisplayString(), "field", f.Type.ToDisplayString(), project, file, line));
            break;

        case IPropertySymbol p:
            var entity = DbSetEntity(p.Type);
            if (entity is not null)
                sink.DbSets.Add(new DbSetFact(
                    id, p.ToDisplayString(), entity.ToDisplayString(), project, file, line));
            else if (p.IsStatic && p.SetMethod is not null && !p.IsReadOnly)
                sink.StaticState.Add(new StaticFact(
                    id, p.ToDisplayString(), "property", p.Type.ToDisplayString(), project, file, line));
            break;
    }
}

// Conditional-compilation symbols referenced in #if / #elif conditions.
static void CollectConditionals(SyntaxNode treeRoot, string? file, DeclSink sink)
{
    if (file is null) return;
    for (var dir = treeRoot.GetFirstDirective(); dir is not null; dir = dir.GetNextDirective())
    {
        if (dir is not ConditionalDirectiveTriviaSyntax cond) continue;
        foreach (var ident in cond.Condition.DescendantNodesAndSelf().OfType<IdentifierNameSyntax>())
        {
            if (!sink.ConditionalsByFile.TryGetValue(file, out var set))
                sink.ConditionalsByFile[file] = set = new SortedSet<string>(StringComparer.Ordinal);
            set.Add(ident.Identifier.ValueText);
        }
    }
}

// Record a concurrency-primitive site (lock statement / Interlocked / Monitor),
// keyed by the enclosing member.
static void AddConcSite(string kind, string detail, SyntaxNode node,
    SemanticModel model, string project, DeclSink sink)
{
    var enclosing = EnclosingDocIdSymbol(model, node.SpanStart);
    string? file = null;
    var line = 0;
    var loc = node.GetLocation();
    if (loc.IsInSource)
    {
        file = RelPath(loc.SourceTree?.FilePath);
        line = loc.GetLineSpan().StartLinePosition.Line + 1;
    }
    sink.ConcurrencySites.Add(new ConcFact(
        kind, detail, DocId(enclosing), enclosing?.ToDisplayString(), project, file, line));
}

static void TryEmitConc(InvocationExpressionSyntax inv, SemanticModel model,
    string project, DeclSink sink)
{
    if (model.GetSymbolInfo(inv).Symbol is not IMethodSymbol m) return;
    var ct = m.ContainingType;
    if (ct?.ContainingNamespace?.ToDisplayString() != "System.Threading") return;
    var kind = ct.Name switch
    {
        "Interlocked" => "interlocked",
        "Monitor" => "monitor",
        _ => null,
    };
    if (kind is not null) AddConcSite(kind, m.Name, inv, model, project, sink);
}

// Declared target frameworks from a csproj: the contents of every
// <TargetFramework> / <TargetFrameworks> element, ';'-split and de-duplicated.
static List<string> ReadTfms(string csprojPath)
{
    var tfms = new List<string>();
    try
    {
        var text = File.ReadAllText(csprojPath);
        foreach (Match mm in Regex.Matches(text, @"<TargetFrameworks?>([^<]+)</TargetFrameworks?>"))
            foreach (var t in mm.Groups[1].Value.Split(';',
                         StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
                if (!t.StartsWith("$(", StringComparison.Ordinal) && !tfms.Contains(t))
                    tfms.Add(t);
    }
    catch { /* unreadable csproj: report no TFMs rather than fail the run */ }
    return tfms;
}

static bool IsTaskLike(ITypeSymbol t)
{
    var d = t.OriginalDefinition;
    return d.ContainingNamespace?.ToDisplayString() == "System.Threading.Tasks"
        && d.Name is "Task" or "ValueTask";
}

static bool IsCancellationToken(ITypeSymbol t) =>
    t.Name == "CancellationToken" && t.ContainingNamespace?.ToDisplayString() == "System.Threading";

static ITypeSymbol? DbSetEntity(ITypeSymbol t) =>
    t is INamedTypeSymbol { Name: "DbSet", TypeArguments.Length: 1 } g
        && g.OriginalDefinition.ContainingNamespace?.ToDisplayString() == "Microsoft.EntityFrameworkCore"
        ? g.TypeArguments[0]
        : null;

static (string? file, int line) FileLineOf(ISymbol s)
{
    var loc = s.Locations.FirstOrDefault(l => l.IsInSource);
    return loc is null
        ? (null, 0)
        : (RelPath(loc.SourceTree?.FilePath), loc.GetLineSpan().StartLinePosition.Line + 1);
}

// Render a Roslyn TypedConstant into a JSON-friendly value (constant folded).
static object? RenderConstant(TypedConstant c) => c.Kind switch
{
    TypedConstantKind.Array => c.IsNull ? null : c.Values.Select(RenderConstant).ToList(),
    TypedConstantKind.Type => (c.Value as ITypeSymbol)?.ToDisplayString(),
    TypedConstantKind.Enum => c.Value, // underlying numeric value
    TypedConstantKind.Error => null,
    _ => c.Value, // primitive / string / null
};

static ISymbol? EnclosingDocIdSymbol(SemanticModel model, int position)
{
    var s = model.GetEnclosingSymbol(position);
    while (s is not null)
    {
        // Lambdas and local functions get a malformed, unstable DocID (empty
        // member name) and are not graph nodes; their facts belong to the
        // containing named member, so walk past them.
        if (s is IMethodSymbol { MethodKind: MethodKind.AnonymousFunction or MethodKind.LocalFunction })
        {
            s = s.ContainingSymbol;
            continue;
        }
        if (s is IMethodSymbol or IPropertySymbol or IFieldSymbol && DocId(s) is not null)
            return s;
        s = s.ContainingSymbol;
    }
    return null;
}

static string? DocId(ISymbol? s) => s?.GetDocumentationCommentId();

static string? FileOf(ISymbol s)
{
    var loc = s.Locations.FirstOrDefault(l => l.IsInSource);
    return loc is null ? null : RelPath(loc.SourceTree?.FilePath);
}

static string? RelPath(string? path)
{
    if (string.IsNullOrEmpty(path)) return null;
    var norm = path.Replace('\\', '/');
    if (RootPrefix is not null && norm.StartsWith(RootPrefix, StringComparison.OrdinalIgnoreCase))
        return norm[RootPrefix.Length..];
    return norm;
}

partial class Program
{
    internal static string? RootPrefix;

    // DI registration extension methods recognised on IServiceCollection.
    internal static readonly HashSet<string> DiMethods = new(StringComparer.Ordinal)
    {
        "AddSingleton", "AddScoped", "AddTransient",
        "TryAddSingleton", "TryAddScoped", "TryAddTransient",
        "AddHostedService",
    };

    // ILogger.Log<Level> suffixes that name a level directly.
    internal static readonly HashSet<string> LogLevels = new(StringComparer.Ordinal)
    {
        "Information", "Warning", "Error", "Debug", "Trace", "Critical",
    };

    // IConfiguration / Options binding methods carrying a key or a bound type.
    internal static readonly HashSet<string> ConfigMethods = new(StringComparer.Ordinal)
    {
        "GetSection", "GetValue", "GetConnectionString", "Bind", "Configure",
    };
    // Identifier-like: topic / stream / table / schema-subject / config-key shapes.
    internal static readonly Regex NameLike =
        new(@"^[A-Za-z_][A-Za-z0-9_.:\-]{2,127}$", RegexOptions.Compiled);

    // Language tokens are not name-based coupling — a change to "BIGINT" or
    // "Select" does not ripple the way a topic/column name does. Filter them so
    // the name nodes carry only genuine, change-relevant shared names.
    internal static readonly HashSet<string> NameStop = new(StringComparer.OrdinalIgnoreCase)
    {
        // SQL / KSQL keywords
        "SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "OUTER", "FULL",
        "ON", "GROUP", "BY", "HAVING", "ORDER", "ASC", "DESC", "LIMIT", "OFFSET",
        "EMIT", "CHANGES", "FINAL", "CREATE", "DROP", "STREAM", "TABLE", "VIEW",
        "INSERT", "INTO", "VALUES", "AS", "WITH", "AND", "OR", "NOT", "IN", "IS",
        "NULL", "TRUE", "FALSE", "LIKE", "BETWEEN", "CASE", "WHEN", "THEN", "ELSE",
        "END", "DISTINCT", "PARTITION", "WINDOW", "TUMBLING", "HOPPING", "SESSION",
        "ADVANCE", "SIZE", "GRACE", "RETENTION", "KEY", "KEYS", "PRIMARY",
        "ROWTIME", "ROWKEY", "FORMAT", "REPLICAS", "PARTITIONS",
        // KSQL / SQL types
        "BIGINT", "INT", "INTEGER", "SMALLINT", "DOUBLE", "BOOLEAN", "VARCHAR",
        "STRING", "BYTES", "DECIMAL", "NUMERIC", "ARRAY", "MAP", "STRUCT",
        "DATE", "TIME", "TIMESTAMP",
        // aggregate / scalar functions
        "AVG", "SUM", "COUNT", "MIN", "MAX", "COLLECT_LIST", "COLLECT_SET",
        "TOPK", "EARLIEST_BY_OFFSET", "LATEST_BY_OFFSET", "CONCAT", "SUBSTRING",
        // LINQ operators
        "Select", "SelectMany", "Where", "Join", "GroupBy", "GroupJoin",
        "OrderBy", "OrderByDescending", "ThenBy", "Take", "Skip", "Aggregate",
        "Average", "First", "FirstOrDefault", "Single", "SingleOrDefault",
        "Any", "All", "Distinct", "ToList", "ToArray",
    };
}

record Node(string Id, string Kind, string Name, string Display, string Project, string? File);
record Edge(string Type, string From, string To);
record ProjectInfo(string Name, string? File);

// One custom-attribute application on a source-declared symbol.
//   Target        DocID of the annotated type / method / property / field
//   Attribute     DocID of the attribute type (T:Ns.FooAttribute)
//   AttributeName attribute type short name (FooAttribute)
//   CtorArgs      positional argument values (constant folded)
//   NamedArgs     named argument values keyed by property/field name
record AttrFact(
    string Target, string TargetKind, string TargetDisplay, string Project,
    string Attribute, string AttributeName,
    List<object?> CtorArgs, Dictionary<string, object?> NamedArgs,
    string? File, int Line);

// One DI registration site.
//   Method          registration method (AddScoped, AddHostedService, ...)
//   Lifetime        singleton / scoped / transient (hosted services -> singleton)
//   ServiceType     the registered (injectable) type; null if unresolved
//   ImplementationType resolved concrete type; null when a factory provides it
//   Factory         a factory lambda supplies the instance
//   CtorDeps        the implementation's greediest-public-ctor parameter types
record DiReg(
    string Method, string Lifetime,
    string? ServiceType, string? ImplementationType,
    bool Factory, List<string> CtorDeps,
    string Project, string? File, int Line);

// Collected declaration/signature facts (unit D), populated only with --decl.
class DeclSink
{
    public List<AsyncFact> AsyncMethods { get; } = new();
    public List<StaticFact> StaticState { get; } = new();
    public List<DbSetFact> DbSets { get; } = new();
    public List<ConcFact> ConcurrencySites { get; } = new();
    public Dictionary<string, SortedSet<string>> ConditionalsByFile { get; } = new();
    public Dictionary<string, List<string>> ProjectSymbols { get; } = new();
    public Dictionary<string, List<string>> ProjectTfms { get; } = new();
}

// A concurrency-primitive site: a lock statement, or an Interlocked / Monitor
// call. Kind is lock | interlocked | monitor; Detail is the method name (or
// "lock"). Keyed by the enclosing member.
record ConcFact(
    string Kind, string Detail, string? Enclosing, string? EnclosingDisplay,
    string Project, string? File, int Line);

// async / Task-returning method, with whether it takes a CancellationToken (an
// async method without one is a propagation-gap candidate).
record AsyncFact(
    string Target, string Display, string ReturnType,
    bool IsAsync, bool HasCancellationToken,
    string Project, string? File, int Line);

// Static mutable shared state: a non-const non-readonly static field, or a
// static settable property.
record StaticFact(
    string Target, string Display, string Kind, string Type,
    string Project, string? File, int Line);

// An EF Core DbSet<TEntity> property (a persistence boundary).
record DbSetFact(
    string Target, string Display, string EntityType,
    string Project, string? File, int Line);

// One framework invocation fact.
//   Category      logging | config | pipeline
//   Method        invoked method name (LogError, GetSection, UseRouting, ...)
//   ReceiverType  the `this`/receiver type display
//   Enclosing     DocID of the member the call sits in (null at top level)
//   Key           config key string literal, when present
//   TargetType    bound/option type for Configure<T> / GetValue<T>
//   Level         log level for the logging category
record InvFact(
    string Category, string Method, string? ReceiverType,
    string? Enclosing, string? EnclosingDisplay,
    string? Key, string? TargetType, string? Level,
    string Project, string? File, int Line);
