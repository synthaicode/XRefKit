# Arrow and block alignment in presentation diagrams

## Observation

In the Japanese presentation derived from the article on AI-assisted software
development, the user observed that arrows were harder to read when their
source and destination were not enclosed as blocks. After the blocks were
added, the user further specified that arrows between them should sit at the
vertical center of the blocks. The revised deck is
`work/2026-09-26_code-quality-presentation/output/code-cheap-quality-ja-centered-arrows.pptx`
in the original workspace.

## Skill implication

For flow diagrams, identify the content blocks joined by each arrow, enclose
those blocks, and align forward arrows with the blocks' vertical midpoint.
Inspect the rendered result at presentation size. In loops, distinguish a
return arrow from forward steps by routing it outside the blocks.

The source presentation was a PPTX. Applying this guidance to a PNG produced
by `marketing_slide_png` remains to be verified in a future Skill run.
