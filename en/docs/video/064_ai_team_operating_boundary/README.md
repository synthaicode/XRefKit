# AI Team Operating Boundary Explainer

This is the next-level explainer after `063_ai_organization_explainer_clear`.

## Message

- `063` explains why an AI Team becomes necessary.
- `064` explains what must be fixed inside the AI Team so human responsibility stays manageable.
- The key theme is the operating boundary between AI work and human responsibility.
- The main control points are execution/check separation, unknown/risk/judgment visibility, closure gate, handoff, and Skill maturity.

## Outputs

- `index.html`: slide preview with narration text.
- `manifest.tsv`: source order and narration text.
- The rendered slide sources live in `en/docs/assets/064_ai_team_operating_boundary/`.

## Build

Render slides:

```powershell
node en/docs/assets/064_ai_team_operating_boundary/render.mjs
```

Capture PNGs:

```powershell
$dir='en/docs/assets/064_ai_team_operating_boundary'
foreach ($name in @('01_title_q','01_title','02_review_q','02_review','03_concern_q','03_concern','04_roles_q','04_roles','05_closure_q','05_closure','06_handoff_q','06_handoff','07_maturity_q','07_maturity','08_conclusion_q','08_conclusion')) {
  npx --yes playwright screenshot --viewport-size='1600,900' "$dir/$name.html" "$dir/$name.png"
}
```

Build silent video after PNG capture:

```powershell
python en/docs/video/064_ai_team_operating_boundary/build_video.py
```
