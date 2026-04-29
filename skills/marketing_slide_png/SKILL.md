<!-- xid: 91B67D4AC2F3 -->
<a id="xid-91B67D4AC2F3"></a>

# Skill: marketing_slide_png

## Purpose

Create slide visuals as CSS/HTML-rendered PNG assets for Marketing Group work. Use this when the deck should be figure-first: Markdown mainly controls page breaks and image placement, while slide titles, key messages, labels, and diagram structure live inside the generated PNG.

This skill may also be used in `single_image_infographic` mode when Marketing Group needs a standalone one-page repository explainer image, such as a current-state visual summary of XRefKit's operating model.

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
- output mode:
  - `slide_deck`
  - `single_image_infographic`

## Outputs

- `diagram.css`
- `render.mjs`
- per-slide `*.html`
- per-slide `*.png`
- updated markdown deck that embeds the generated PNG files
- for `single_image_infographic`: one standalone PNG plus its reusable HTML/CSS/render sources

## Startup

- Confirm the target deck path.
- For `single_image_infographic`, confirm the target repository scope and target image path instead of a deck path.
- Confirm that the deck should be image-based, or identify which slides should use image-based composition.
- Confirm the audience and purpose so each slide can be reduced to one visual message.
- Confirm whether titles and supporting labels should live inside the PNG. Default to yes for image-based decks.
- Read the style guide and pick layout patterns before writing any render script.
- When the deck is Japanese, read the Japanese presentation tone guide and keep claims clear but wording natural.

## Planning

- Map each slide to one core message.
- For `single_image_infographic`, map the image to one central claim and a small number of visual sections.
- When the image represents the current repository, build a repository fact map before visual layout:
  - entry points read
  - repository structures shown
  - control rules shown
  - evidence-backed claims
  - marketing explanations
  - unknown or unstable claims
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
- Keep one central claim per standalone infographic. If the image needs multiple unrelated claims, split it into a deck or a series of images.

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
- For `single_image_infographic`, use an explicit filename that names the repository snapshot, such as `xrefkit_os.html` and `xrefkit_os.png`.

## Monitoring and Control

- Verify every slide still has one visual message.
- Verify every standalone infographic still has one central claim.
- For repository snapshot infographics, verify the image represents the current repository state and does not invent undocumented capabilities.
- Verify important XRefKit control ideas are not accidentally dropped when they are part of the requested message:
  - AI does not rely on memory
  - required context is loaded from control assets
  - execution and checking are separated
  - unsupported guessing is stopped
  - unknowns and risks stay explicit
  - context-direction guard protects higher-layer intent and authority
  - trade-offs and approvals return to humans
  - audit trail and XID traceability support reproducibility
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
- For `single_image_infographic`, confirm the standalone PNG exists on disk.
- Confirm the markdown paths match the generated asset paths.
- Keep rerenderable sources:
  - do not keep only PNG
  - preserve CSS and HTML generation sources
- Preserve the rendering command path so another agent can rerun the asset generation without reverse-engineering the process.

## Rules

- Markdown should mainly own page breaks and image placement for image-based decks.
- For standalone repository infographics, preserve a short source note or session log that records which repository entry points were read.
- Put the communicative content into the image when using the image-based pattern.
- Do not duplicate the same title and bullets in both Markdown and PNG.
- Do not create over-decorated diagrams. Favor clarity over novelty.
- Do not use this skill for official announcements; that belongs to PR Group.
