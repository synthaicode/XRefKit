<!-- xid: 91B67D4AC2F3 -->
<a id="xid-91B67D4AC2F3"></a>

# Skill: marketing_slide_png

## Purpose

Create slide visuals as CSS/HTML-rendered PNG assets for Marketing Group work. Use this when the deck should be figure-first: Markdown mainly controls page breaks and image placement, while slide titles, key messages, labels, and diagram structure live inside the generated PNG.

## References

- [Marketing Slide PNG Style Guide](references/style-guide.md)
- [Japanese Presentation Tone Guide](references/japanese-presentation-tone.md)
- [Marketing Slide PNG Layout Patterns](references/layout-patterns.md)
- [Marketing Slide PNG Pattern Samples](references/pattern-samples.md)

## Ownership

- Treat this skill as Marketing Group work.
- Use PR Group for official announcement work instead of this skill.

## Inputs

- deck markdown path
- target asset directory
- slide-by-slide message list
- visual direction or brand constraints
- whether the deck should be image-based for all slides or only selected slides

## Outputs

- `diagram.css`
- `render.mjs`
- per-slide `*.html`
- per-slide `*.png`
- updated markdown deck that embeds the generated PNG files

## Startup

- Confirm the target deck path.
- Confirm that the deck should be image-based, or identify which slides should use image-based composition.
- Confirm the audience and purpose so each slide can be reduced to one visual message.
- Confirm whether titles and supporting labels should live inside the PNG. Default to yes for image-based decks.
- Read the style guide and pick layout patterns before writing any render script.
- When the deck is Japanese, read the Japanese presentation tone guide and keep claims clear but wording natural.

## Planning

- Map each slide to one core message.
- Decide what stays in Markdown:
  - page breaks
  - image embed lines
  - optional speaker notes only
- Decide what moves into the PNG:
  - slide title
  - subtitle or one-line claim
  - boxes, arrows, comparisons, loops, labels, badges
- Prefer comparison, flow, hub-and-spoke, and loop layouts for concept slides.
- Choose patterns from `references/layout-patterns.md` instead of inventing a new structure by default.
- Keep one visual per slide. If the slide needs two different stories, split it.

## Execution

- Create or reuse an asset folder under `ja/docs/assets/<deck-name>/` when the deck is Japanese, or the matching docs tree when not.
- Create:
  - `diagram.css` for shared visual rules
  - `render.mjs` for deterministic HTML generation
  - one `*.html` per slide image
- Put the slide title and key message inside the generated image when the deck is image-based.
- Keep the markdown deck minimal. Prefer this pattern:

```md
---

![slide image](assets/<deck-name>/01_example.png)
```

- Generate HTML first, then render PNG from those HTML files.
- Prefer reproducible local commands. In this repository, the working pattern is:

```powershell
node ja/docs/assets/<deck-name>/render.mjs
npx --yes playwright install chromium
npx --yes playwright screenshot --browser chromium --viewport-size "1600,900" file:///.../01_example.html .../01_example.png
```

- If multiple images are needed, render all HTML files in a loop and keep filenames ordered such as `01_`, `02_`, `03_`.

## Monitoring and Control

- Verify every slide still has one visual message.
- Verify markdown does not repeat text that already appears inside the PNG.
- Regenerate PNG files after any structural change to the diagrams.
- Keep CSS simple and consistent across slides:
  - stable typography
  - limited color palette
  - consistent spacing
  - minimal decorative effects
- Follow `references/style-guide.md` for color, typography, and markdown split decisions.
- Follow `references/japanese-presentation-tone.md` when writing Japanese titles, subtitles, badges, and summary lines.

## Closure

- Confirm every embedded PNG exists on disk.
- Confirm the markdown paths match the generated asset paths.
- Keep rerenderable sources:
  - do not keep only PNG
  - preserve CSS and HTML generation sources
- Preserve the rendering command path so another agent can rerun the asset generation without reverse-engineering the process.

## Rules

- Markdown should mainly own page breaks and image placement for image-based decks.
- Put the communicative content into the image when using the image-based pattern.
- Do not duplicate the same title and bullets in both Markdown and PNG.
- Do not create over-decorated diagrams. Favor clarity over novelty.
- Do not use this skill for official announcements; that belongs to PR Group.
