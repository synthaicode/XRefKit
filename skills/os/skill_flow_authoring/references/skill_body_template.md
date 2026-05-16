<!-- xid: 84C920557A2C -->
<a id="xid-84C920557A2C"></a>

# Skill Body Template

```md
# Skill: <skill_id>

## Purpose

<one-paragraph purpose>

## Required Knowledge (XID)

- [Reference name](<relative-path-to-docs-or-knowledge>/<path>.md#xid-...)

## Optional References

- [Template or helper](./references/<file>.md)

## Inputs

- <input 1>
- <input 2>

## Outputs

- <output 1>
- <output 2>

## Anti-Forgetting Structure

- explicitly state what later AI runs must not have to reconstruct
- explicitly state where reusable facts live
- explicitly state what must be handed off with evidence

## Startup

- <confirm boundary>
- <confirm required artifacts>
- <load required rules>

## Planning

- <scope decision>
- <target file decision>
- <maturity decision>

## Execution

1. <perform creation/update step>
2. <perform validation step>

## Monitoring and Control

- <downgrade unsupported inference>
- <stop and escalate condition>

## Closure

- <return outputs and gaps>

## Rules

- <must not rule>
- <must not rule>
```

Authoring notes:

- Keep procedure in the Skill.
- Move reusable domain facts to `knowledge/`.
- Replace sample links with real `#xid-...` references before treating the
  Skill as ready.
- Replace the relative-path placeholder so it matches the actual family path of
  the Skill.
- If the Skill loads external context, include the guard.
- If a later AI could forget it, encode it structurally instead of assuming it
  will stay in memory.
