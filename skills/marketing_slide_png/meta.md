<!-- xid: 5E2C4A90D711 -->
<a id="xid-5E2C4A90D711"></a>

# Skill Meta: marketing_slide_png

- skill_id: `marketing_slide_png`
- summary: create marketing-group slide visuals by rendering CSS/HTML diagrams to PNG and keep Markdown slide files as page-break shells
- use_when: user needs presentation diagrams, figure-first slides, or visually structured slide assets for decks where Markdown should mainly control page breaks and image placement
- input: target deck markdown path, target asset directory, slide messages, diagram structure, and branding constraints
- output: slide-ready PNG diagrams, reusable `diagram.css`, reusable `render.mjs`, and updated deck markdown that embeds the generated PNG assets
- guard_policy: `required`
- constraints: treat this as Marketing Group work; keep official announcement ownership outside this skill; put slide titles, labels, and visual hierarchy inside the generated image when the deck is image-based; keep Markdown minimal and avoid duplicating slide content outside the PNG
- lifecycle:
  - startup: confirm deck path, audience, visual direction, and whether the deck should be image-based
  - planning: map each slide to one visual message and decide which content belongs in PNG versus speaker notes
  - execution: build CSS/HTML render sources, generate PNG assets, and embed those assets into the markdown deck
  - monitoring_and_control: verify one-image-per-slide clarity, regenerate images when structure changes, and keep rendering reproducible
  - closure: confirm assets exist, markdown references are correct, and rerender commands are preserved
- tags: `marketing`, `presentation`, `slides`, `diagram`, `png`, `css`, `html`, `marp`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
