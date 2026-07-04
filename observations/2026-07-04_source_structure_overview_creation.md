<!-- xid: EF071B0E0FB8 -->
<a id="xid-EF071B0E0FB8"></a>

# Observation: source_structure_overview Creation

The `source_structure_overview` Skill was created after distinguishing baseline
source-structure knowledge from proposition-specific .NET change analysis.

Observed need:

- `dotnet_change_analysis` works on a specific change or investigation
  proposition.
- Brownfield work also needs a reusable whole-system structure overview that
  remains valid until the target structure changes.
- That overview should become domain knowledge selected later by XID through
  `knowledge_inputs`.

Routing decision:

- Use `source_structure_overview` to create reusable source-structure overview
  domain knowledge.
- Use `source_structure_findings_registration` to register that result into
  canonical knowledge when publication is authorized.
- Use `dotnet_change_analysis` later for proposition-specific change impact,
  selecting the overview from available domain knowledge.
