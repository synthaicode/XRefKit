<!-- xid: 9604C0C31FE3 -->
<a id="xid-9604C0C31FE3"></a>

# Flow Doc Template

Use this only when the Flow also needs a human-readable explanation in `docs/`.

```md
# <Flow title>

## Purpose

<why this workflow exists>

## Boundary

- previous side: <what hands work in>
- current responsibility: <what this flow is responsible for>
- next side: <what receives the output>

## Inputs

- <input>

## Outputs

- <output>

## Control Points

- <approval, risk, or quality gate>

## Related Machine-Readable Flow

- `flows/<flow_id>.yaml`
```

Keep the source of truth split explicit:

- `flows/` for machine-readable control
- `docs/` for human-readable explanation
