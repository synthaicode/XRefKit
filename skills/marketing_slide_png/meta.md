<!-- xid: 5E2C4A90D711 -->
<a id="xid-5E2C4A90D711"></a>

# Skill Meta: marketing_slide_png

- skill_id: `marketing_slide_png`
- summary: create marketing-group slide visuals or standalone repository infographics by rendering CSS/HTML diagrams to PNG
- use_when: user needs presentation diagrams, figure-first slides, or a one-page repository explainer image where the final visual must be readable and rerenderable
- input: target deck markdown path or target infographic path, target asset directory, slide messages or central infographic claim, diagram structure, repository fact map, and branding constraints
- output: slide-ready PNG diagrams or a standalone infographic PNG, reusable `diagram.css`, reusable `render.mjs`, and updated deck markdown when the output is a deck
- maturity: `trial`
- execution_mode: `local_default`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: create marketing-group slide visuals or standalone repository infographics by rendering CSS/HTML diagrams to PNG
- role_responsibilities:
  - executor: user needs presentation diagrams, figure-first slides, or a one-page repository explainer image where the final visual must be readable and rerenderable
- os_contract: v1
- constraints: treat this as Marketing Group work; keep official announcement ownership outside this skill; put slide titles, labels, and visual hierarchy inside the generated image when the deck is image-based; keep Markdown minimal and avoid duplicating slide content outside the PNG; for repository infographics, represent the current repository state and preserve rerenderable sources
- lifecycle:
  - startup: confirm deck path, audience, visual direction, and whether the deck should be image-based
  - planning: map each slide to one visual message and decide which content belongs in PNG versus speaker notes
  - execution: build CSS/HTML render sources, generate PNG assets, and embed those assets into the markdown deck
  - monitoring_and_control: verify one-image-per-slide clarity, regenerate images when structure changes, and keep rendering reproducible
  - closure: confirm assets exist, markdown references are correct, and rerender commands are preserved
- tags: `marketing`, `presentation`, `slides`, `diagram`, `png`, `css`, `html`, `marp`, `infographic`, `repository-snapshot`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/marketing/110_cap_mkt_002_repository_infographic_snapshot.md#xid-C8D4A92F61E0`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- observation_refs:
  - `../../observations/2026-04-29_skill_run_marketing_slide_png.md`
  - `../../observations/2026-04-29_skill_run_closure_gate.md`
