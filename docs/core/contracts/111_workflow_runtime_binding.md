<!-- xid: 8D50A972BA9F -->
<a id="xid-8D50A972BA9F"></a>

# Workflow Runtime Binding Contract

This contract is the single owner of the runtime `capability`, `tuning`, and
`responsibility` fields. The binding is part of the Workflow Protocol. Skills,
Knowledge, model-routing policy, and subagent adapters consume it but do not
redefine it.

## Purpose

The Workflow Runtime Binding translates the current instruction and work-item
state into the execution context used for one bounded unit of work. It keeps a
reusable SkillDefinition independent from a particular request while making the
actual execution context observable.

The canonical binding contains:

| Field | Meaning |
| --- | --- |
| `capability` | Reusable ability required by this work item. |
| `tuning` | Technology, domain, quality focus, or other specialization applied to that ability. |
| `responsibility` | Bounded outcome the executor is responsible for producing or checking. It does not transfer human adoption authority. |
| `execution_mode` | Placement constraint for the executor, such as `local_default`, `subagent_preferred`, or `subagent_required`. |
| `instruction_basis` | Evidence pointer to the instruction or state from which the binding was derived. |

## Ownership And Derivation

The parent workflow or host derives the binding from the current instruction,
active work item, authority, and current state. Semantic Skill selection may use
the instruction and SkillDefinition metadata, but the selected SkillDefinition
does not own these values.

For a canonical SkillDefinition v1 run:

1. select the reusable method using its identity, `applies_when`, inputs,
   outputs, and criteria;
2. derive the Workflow Runtime Binding for the concrete work item;
3. open the run with the selected definition and the derived binding;
4. persist the binding before delegation or execution;
5. pass the same binding through ExecutionBinding and subagent startup without
   reinterpretation.

If a required value cannot be derived from available evidence, preserve it as
an unresolved routing condition and do not dispatch the work item. Do not fill
it from a generic role prompt, model profile, or Skill prose.

## Boundary

The binding is:

- runtime control state for one work item or run;
- observable in the run log, ExecutionBinding, subagent receipt, gateway state,
  and dashboard where those surfaces apply;
- allowed to differ between work items that use the same SkillDefinition.

The binding is not:

- SkillDefinition identity or Skill catalog metadata;
- Knowledge or evidence;
- a model capability requirement, cost tier, or ranking signal;
- a Workflow role such as `executor`, `checker`, `quality_reviewer`, or
  `handoff_owner`;
- human approval, acceptance, publication, or adoption authority.

`model_requirements` remains the per-work-item input to model eligibility.
Knowledge remains selected through `knowledge_needs` and XID resolution.
Workflow roles continue to own execution, deterministic checking, quality, and
handoff progression.

## Vocabulary

Use stable, plain terms that describe the current work rather than seniority or
persona.

| Work item | capability | tuning | responsibility |
| --- | --- | --- | --- |
| Implement C# software | software development | C# | implement the scoped change and evidence |
| Review C# software | software review | C# | report findings against the declared criteria |
| Analyze a C# and SQL change | change analysis | C# + SQL | identify bounded impact and unresolved dependencies |

Composite tuning may resolve common, specific, and cross-domain Knowledge. The
binding names the execution context; it does not embed the Knowledge corpus.

## Compatibility

Legacy split Skills may still declare `capability`, `tuning`, `responsibility`,
`execution_mode`, and `capability_layering` in `meta.md`. At the compatibility
boundary, XRefKit maps those values into the Workflow Runtime Binding. They
remain legacy inputs and must not be treated as canonical Skill identity or be
copied into new SkillDefinition v1 headers.

Existing run logs keep their recorded shape. New runtime records identify the
binding owner as `workflow_protocol`.

## Consumers

- `xrefkit skill run` records the binding for Skill-backed execution.
- `xrefkit workflow run` records a generic binding for instruction-backed work.
- `workflow bind-execution` materializes the binding for subagent startup.
- The instruction gateway preserves the binding as task context while using
  separate `model_requirements` for model selection.
- MCP Workflow Protocol initialization distributes this contract and its XID.

Related contracts:

- [Skill and Knowledge Operating Model](../models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Skill Operating Contract](058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [SkillDefinition v1](096_skill_definition_contract.md#xid-E6A19D4B72C3)
- [Work-item model routing](110_work_item_model_routing.md#xid-F2C91B7E4A60)
