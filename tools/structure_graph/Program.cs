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
//   StructureGraph --out <graph.json> <project1.csproj> [<project2.csproj> ...]

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
    var inputPaths = new List<string>();
    for (var i = 0; i < args.Length; i++)
    {
        if (args[i] == "--out" && i + 1 < args.Length) { outPath = args[++i]; continue; }
        if (args[i] == "--root" && i + 1 < args.Length) { root = args[++i]; continue; }
        inputPaths.Add(args[i]);
    }
    if (outPath is null || inputPaths.Count == 0)
    {
        Console.Error.WriteLine("usage: StructureGraph --out <graph.json> [--root <repo-root>] <sln-or-csproj> [...]");
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
        Console.Error.WriteLine($"[open] {p}");
        var full = Path.GetFullPath(p);
        if (full.EndsWith(".sln", StringComparison.OrdinalIgnoreCase))
            await ws.OpenSolutionAsync(full);
        else
            await ws.OpenProjectAsync(full);
    }

    var nodes = new Dictionary<string, Node>();
    var edges = new HashSet<Edge>();
    var externalCallCount = new Dictionary<string, int>();
    var projectInfos = new List<ProjectInfo>();
    // Identifier-like string literal -> distinct member DocIDs that use it.
    // A literal shared by >= 2 members is a name-based coupling (topic / schema /
    // config key) invisible to the call graph; emitted as a `name` shared node.
    var literalUsers = new Dictionary<string, HashSet<string>>();

    foreach (var project in ws.CurrentSolution.Projects)
    {
        var projId = "PRJ:" + project.Name;
        nodes.TryAdd(projId, new Node(projId, "project", project.Name, project.Name, project.Name, null));
        projectInfos.Add(new ProjectInfo(project.Name, RelPath(project.FilePath)));

        var comp = await project.GetCompilationAsync();
        if (comp is null) continue;

        // 1) Declared symbols (types + members) of this project's source assembly.
        WalkNamespace(comp.Assembly.GlobalNamespace, project.Name, projId, nodes, edges);

        // 2) Call edges from invocations / object creations within source.
        foreach (var tree in comp.SyntaxTrees)
        {
            var model = comp.GetSemanticModel(tree);
            var treeRoot = await tree.GetRootAsync();

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
    return 0;
}

static void WalkNamespace(INamespaceSymbol ns, string project, string projId,
    Dictionary<string, Node> nodes, HashSet<Edge> edges)
{
    foreach (var t in ns.GetTypeMembers())
        WalkType(t, project, projId, nodes, edges);
    foreach (var sub in ns.GetNamespaceMembers())
        WalkNamespace(sub, project, projId, nodes, edges);
}

static void WalkType(INamedTypeSymbol type, string project, string projId,
    Dictionary<string, Node> nodes, HashSet<Edge> edges)
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

    foreach (var member in type.GetMembers())
    {
        switch (member)
        {
            case IMethodSymbol m when m.MethodKind is MethodKind.Ordinary or MethodKind.Constructor:
                AddMember(m, "method", typeId, project, nodes, edges);
                break;
            case IPropertySymbol p:
                AddMember(p, "property", typeId, project, nodes, edges);
                break;
            case IFieldSymbol f when !f.IsImplicitlyDeclared:
                AddMember(f, "field", typeId, project, nodes, edges);
                break;
            case INamedTypeSymbol nested:
                WalkType(nested, project, projId, nodes, edges);
                break;
        }
    }
}

static void AddMember(ISymbol member, string kind, string typeId, string project,
    Dictionary<string, Node> nodes, HashSet<Edge> edges)
{
    var id = DocId(member);
    if (id is null) return;
    nodes.TryAdd(id, new Node(id, kind, member.Name, member.ToDisplayString(), project, FileOf(member)));
    edges.Add(new Edge("declares", typeId, id));
}

static ISymbol? EnclosingDocIdSymbol(SemanticModel model, int position)
{
    var s = model.GetEnclosingSymbol(position);
    while (s is not null)
    {
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
