# xrefkit-skills-batch-regression

XRefKit Skill Package v0.4.2 for impact analysis and combination regression of
existing C# batches backed by SQL Server stored procedures.

The package provides a discoverable XRefKit v2 Skill Package and bundles the
repository-native Skill procedure, deterministic combination/result tools,
source condition extraction, configuration references, and synthetic fixtures.
Real batch and database execution still requires an isolated adapter supplied
by the consuming project.

Install:

```powershell
python -m pip install xrefkit-skills-batch-regression==0.4.2
```

The package is discovered through the `xrefkit.skill_packages` entry-point
group and includes the deterministic tools under `skill_assets/scripts/`.

The folder-based XRefKit MCP reads `skills/**/meta.md` from its `--repo`
directory. Materialize this package into that repository after installation:

```powershell
xrefkit-batch-regression install-mcp-skill --repo C:\path\to\xrefkit-repository
```

Restart the MCP server after materialization. The command refuses to overwrite
an existing Skill unless `--force` is explicitly supplied.
