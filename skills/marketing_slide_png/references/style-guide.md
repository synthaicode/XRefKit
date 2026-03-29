<!-- xid: 8B1A7D45C9E2 -->
<a id="xid-8B1A7D45C9E2"></a>

# Marketing Slide PNG Style Guide

## Core Style

- beautiful and simple
- avoid information overload
- use a grayscale base with only limited accent color
- prioritize readability through font size and whitespace
- repeat patterns consistently so the audience can learn the deck quickly

## Design Philosophy

- Prefer clean, explainable slides over decorative slides.
- Keep one visual message per slide.
- Use image-based slides when Markdown should only handle page breaks and image placement.
- Make speaker intent obvious in the image itself: title, core claim, labels, and relationships should be visible without reading surrounding markdown.

Interpretation for this repository:

- Beauty:
  - use alignment, spacing, and proportion instead of visual noise
- Simplicity:
  - remove any element that does not help the speaker's message
- Limited color:
  - do not assign a new color to every concept
- Readability:
  - if a viewer cannot understand the slide from normal meeting distance, the slide is too dense
- Consistency:
  - prefer repeating known layout patterns over inventing a fresh composition for each page

## Palette

- Base background:
  - very light gray or blue-tinted white
- Main text:
  - dark navy or dark gray
- Accent colors:
  - use 1 primary accent and at most 1 supporting accent per slide
- Warning / risk:
  - orange or red
- Positive / stable:
  - green

Do not exceed 2 accent families on a slide unless the slide is explicitly categorical.

Recommended default:

- background:
  - grayscale or near-grayscale
- cards:
  - white
- border:
  - soft gray-blue
- accent:
  - one blue family by default
- optional secondary:
  - one muted orange or one muted green only when meaning requires it

## Typography

- Slide title:
  - large and bold
- Subtitle:
  - smaller and muted
- Box labels:
  - bold and scannable
- Explanatory caption:
  - short and secondary

Do not place paragraph-length prose inside diagrams.

Default size hierarchy for 1600x900 render targets:

- title:
  - 52px to 60px
- subtitle:
  - 22px to 26px
- box label:
  - 26px to 32px
- card body:
  - 20px to 24px
- supporting caption:
  - 20px to 22px

## Language Tone

For Japanese decks, prioritize natural presentation tone over direct translated English-style assertions.

- keep the conclusion clear, but do not force the audience with repeated `必要がある`
- prefer expressions such as:
  - `論点になります`
  - `求められます`
  - `重要になります`
  - `つながりにくくなります`
- when presenting a recommendation, prefer:
  - `〜という見方が適しています`
  - `〜を見据えて整理することが重要です`
  - `〜まで含めて考える必要があります`
- avoid overusing:
  - `〜である`
  - `〜しなければならない`
  - `だから〜する必要がある`

See also:

- [Japanese Presentation Tone Guide](japanese-presentation-tone.md)

## Layout Rules

- Keep generous whitespace.
- Use consistent corner radius and border treatment.
- Prefer soft shadows and subtle borders.
- Keep visual weight centered around the main comparison, flow, or hub.
- Avoid crowded multi-layer diagrams.

Contrast rule:

- separate slide background and component background clearly
- prefer white cards against tinted backgrounds
- if card and background are too close, adjust tone before adding more colors

Emphasis rule:

- use size first
- use position second
- use contrast third
- use color last

Do not rely on color alone to tell the audience what to look at.

## Markdown Split

For image-based decks:

- Markdown owns:
  - `---`
  - image embeds
  - optional speaker notes
- PNG owns:
  - slide title
  - slide subtitle or one-line claim
  - boxes, arrows, labels, badges, comparisons, loops

## Rendering Rule

- Always preserve rerenderable sources:
  - `diagram.css`
  - `render.mjs`
  - generated `*.html`
  - final `*.png`
- Do not keep PNG only.
