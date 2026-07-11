# Human Docs

This folder contains human-facing language trees and presentation-oriented
materials.

- `diagrams/`: cross-language concept diagrams with minimal canonical notes
- `ja/`: Japanese human-facing docs, materials, assets, and video packages
- `en/`: English human-facing materials, assets, and video packages

These trees are not canonical AI-facing operational docs.
Canonical operational docs remain under:

- `docs/`
- `knowledge/`
- `agent/`

For diagram entry points, see
[human-docs/diagrams/index.md](diagrams/index.md).

For the canonical language boundary, see
[docs/policies/030_language_policy.md](../docs/policies/030_language_policy.md#xid-72FB974C8236).

## Public Deck Scope

A public deck has one reader level, one central question, and one learning
outcome. It should normally contain 8 to 12 slides and should link to another
deck instead of repeating that deck's explanation.

The public catalog uses four levels:

| Level | Reader starting point | Deck scope |
| --- | --- | --- |
| Problem | New to the operating problem | Why prompt-centric AI use does not become durable business execution |
| Model | Familiar with AI agents | How Goal, Skills, routing, Knowledge, and workflow connect |
| Implementation | Evaluating XRefKit | How the repository and package implement the operating model |
| Boundary | Designing governance | What AI may decide and what remains with humans |

The site top page routes readers by their current question. Complete deck
discovery belongs to the language catalogs under `site/ja/` and `site/en/`.
Legacy decks may keep stable routes without being listed in the current public
catalog.
