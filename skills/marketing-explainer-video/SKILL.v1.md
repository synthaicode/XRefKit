---
schema_version: 1
skill_id: marketing_explainer_video
xid: B8F1A6C4D720
summary: create repository-ready narrated marketing explainer videos with staged slide reveals, TTS audio, credits, previews, and publication placement
applies_when:
- user needs a short product overview video, AI/team explainer video, narrated slide video, Japanese or English marketing video, README-linked MP4, or conversion of a message flow into a video package
exclusions:
- Human acceptance or publication approval remains with the requester
- Unsupported facts, claims, or interpretation remain explicit as unknown
inputs:
- target audience, message flow, language, voice/TTS choice, required credits, asset directory, video directory, and publication target
outputs:
- HTML/CSS slide sources, PNG slide states, narration manifest, preview HTML, video build scripts, final MP4, and optional README/docs link
criteria:
- id: artifact_traceability
  statement: Produced artifacts retain the source pointers, reproducible inputs, and verification evidence required by this Skill
  verification: Inspect the artifact paths, source links, and verification record
- id: acceptance_boundary
  statement: Human acceptance and publication decisions remain explicit and are not inferred from successful generation
  verification: Check the handoff and acceptance boundary before closure
- id: output_closure
  statement: The declared artifact output exists and unresolved items are returned
  verification: Check output paths, open items, and handoff
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: marketing_video_tts_engine_guidance
  query: marketing video TTS engine guidance
  required_when: Required when applying this Skill's source or production guidance
  seed_xids:
  - 9C41D7B2A5E1
control_refs: []
aliases:
- 5E147B19D33D
- A6B923E41178
---
<!-- xid: B8F1A6C4D720 -->
<a id="xid-B8F1A6C4D720"></a>

# Marketing Explainer Video

## Purpose

Create short marketing explainer videos that are understandable to first-time viewers. Use a question-then-explanation structure, reveal slide content in sync with narration, and ship reproducible source files with the final MP4.

## Inputs

- target audience and purpose
- message flow or rough script
- language and target voices
- assets directory and video directory
- TTS engine choice such as VOICEVOX, Azure Speech, or silent preview
- required credits and license text
- desired publication target such as README, docs page, or release artifact

## Outputs

- `render.mjs` and `diagram.css`
- per-state `*.html` and `*.png` slide assets
- `manifest.tsv` with slide order and narration
- preview `index.html`
- build script for silent or TTS video
- final `*.mp4`
- README or docs link update when requested

## Story Design

- Define the core term early, within the first two or three slides.
- Use a clear progression: problem -> attempted solution -> new human burden -> next structure.
- Make each step answer what changed for humans, not only what changed technically.
- Before locking slide order, write one bridge line per step:
  - what the viewer understands now
  - what question or doubt remains
  - what the next slide resolves
- If a slide needs a concept that has not been introduced yet, add a setup slide
  instead of hiding the jump inside narration.
- Add at least one concrete example and one Before / After slide.
- Avoid explaining implementation brands or internal repository names unless the user explicitly asks.
- Use short question-only states before full explanation states so viewers can follow the narration.
- Remove visible speaker labels when voice and timing already distinguish roles.

## Slide Construction

- Use the `marketing_slide_png` pattern for CSS/HTML-rendered PNG slides.
- Keep each slide state to one visual message.
- Prefer `*_q` filenames for question-only states and the base filename for the revealed explanation state.
- Keep text large enough for video playback; verify full slides, not just HTML.
- Use summary bars for the lasting point, but avoid overlapping them with main content.
- When translating, re-balance text length and font sizes instead of preserving Japanese layout sizes blindly.

## Narration and Pacing

- Write narration in dialogue form when the topic can feel abstract.
- Put one narration turn per row in `manifest.tsv`.
- Add short pauses after questions and after explanation slides.
- Avoid monotone pacing by alternating:
  - question-only state
  - explanation reveal
  - flow or comparison slide
  - summary slide
- If the slide already contains both question and explanation, split it into two states.

## TTS

- Keep secrets in environment variables. Never write API keys into scripts or manifests.
- Choose the TTS path explicitly by loading [Marketing video TTS engine guidance](../../knowledge/operations/150_marketing_video_tts_engine_guidance.md#xid-9C41D7B2A5E1) before synthesis planning.
- For VOICEVOX, include explicit credit slides and final visible credit text for all voices used.
- For Irodori-TTS, treat it as offline segment generation and record the checkpoint family and prompting method in build notes.
- For Azure Speech, read `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` from the environment.
- Use different voices for question and answer roles when available.
- Generate segment videos from still PNG + audio, then concatenate and re-encode the final MP4 to avoid timestamp/fps issues.

## Licensing

- Add a final credit slide when the audio engine or voice model requires attribution.
- Include visible voice credits in the video, not only in README text.
- Keep generated intermediate audio and segment files out of commits unless explicitly requested.
- Commit final MP4, source scripts, manifests, slide assets, and preview files.

## Verification

- Render HTML, then capture PNGs with Playwright or the repository's established screenshot method.
- Inspect representative PNGs, especially:
  - title slide
  - dense definition slide
  - concrete example slide
  - Before / After slide
  - license/credit slide
- Check scenario continuity before polishing visuals:
  - no term appears before it is set up
  - no conclusion appears before the problem and failed alternative are visible
  - each slide can answer why it follows the previous slide
- Build the MP4 and verify:
  - resolution
  - fps
  - duration
  - final file path
  - audio is present when TTS is expected
- Run repository checks such as `python -m xrefkit xref fix` after adding Markdown or documentation links.

## Publication

- If the video is for README playback, prefer a root-level `readme.mp4` or a GitHub raw URL.
- Keep README copy short and benefit-led.
- When committing, stage only the intended video package. Leave unrelated dirty worktree changes untouched.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Marketing Explainer Video

## Purpose

Create short marketing explainer videos that are understandable to first-time viewers. Use a question-then-explanation structure, reveal slide content in sync with narration, and ship reproducible source files with the final MP4.

## Inputs

- target audience and purpose
- message flow or rough script
- language and target voices
- assets directory and video directory
- TTS engine choice such as VOICEVOX, Azure Speech, or silent preview
- required credits and license text
- desired publication target such as README, docs page, or release artifact

## Outputs

- `render.mjs` and `diagram.css`
- per-state `*.html` and `*.png` slide assets
- `manifest.tsv` with slide order and narration
- preview `index.html`
- build script for silent or TTS video
- final `*.mp4`
- README or docs link update when requested

## Story Design

- Define the core term early, within the first two or three slides.
- Use a clear progression: problem -> attempted solution -> new human burden -> next structure.
- Make each step answer what changed for humans, not only what changed technically.
- Before locking slide order, write one bridge line per step:
  - what the viewer understands now
  - what question or doubt remains
  - what the next slide resolves
- If a slide needs a concept that has not been introduced yet, add a setup slide
  instead of hiding the jump inside narration.
- Add at least one concrete example and one Before / After slide.
- Avoid explaining implementation brands or internal repository names unless the user explicitly asks.
- Use short question-only states before full explanation states so viewers can follow the narration.
- Remove visible speaker labels when voice and timing already distinguish roles.

## Slide Construction

- Use the `marketing_slide_png` pattern for CSS/HTML-rendered PNG slides.
- Keep each slide state to one visual message.
- Prefer `*_q` filenames for question-only states and the base filename for the revealed explanation state.
- Keep text large enough for video playback; verify full slides, not just HTML.
- Use summary bars for the lasting point, but avoid overlapping them with main content.
- When translating, re-balance text length and font sizes instead of preserving Japanese layout sizes blindly.

## Narration and Pacing

- Write narration in dialogue form when the topic can feel abstract.
- Put one narration turn per row in `manifest.tsv`.
- Add short pauses after questions and after explanation slides.
- Avoid monotone pacing by alternating:
  - question-only state
  - explanation reveal
  - flow or comparison slide
  - summary slide
- If the slide already contains both question and explanation, split it into two states.

## TTS

- Keep secrets in environment variables. Never write API keys into scripts or manifests.
- Choose the TTS path explicitly by loading [Marketing video TTS engine guidance](../../knowledge/operations/150_marketing_video_tts_engine_guidance.md#xid-9C41D7B2A5E1) before synthesis planning.
- For VOICEVOX, include explicit credit slides and final visible credit text for all voices used.
- For Irodori-TTS, treat it as offline segment generation and record the checkpoint family and prompting method in build notes.
- For Azure Speech, read `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` from the environment.
- Use different voices for question and answer roles when available.
- Generate segment videos from still PNG + audio, then concatenate and re-encode the final MP4 to avoid timestamp/fps issues.

## Licensing

- Add a final credit slide when the audio engine or voice model requires attribution.
- Include visible voice credits in the video, not only in README text.
- Keep generated intermediate audio and segment files out of commits unless explicitly requested.
- Commit final MP4, source scripts, manifests, slide assets, and preview files.

## Verification

- Render HTML, then capture PNGs with Playwright or the repository's established screenshot method.
- Inspect representative PNGs, especially:
  - title slide
  - dense definition slide
  - concrete example slide
  - Before / After slide
  - license/credit slide
- Check scenario continuity before polishing visuals:
  - no term appears before it is set up
  - no conclusion appears before the problem and failed alternative are visible
  - each slide can answer why it follows the previous slide
- Build the MP4 and verify:
  - resolution
  - fps
  - duration
  - final file path
  - audio is present when TTS is expected
- Run repository checks such as `python -m xrefkit xref fix` after adding Markdown or documentation links.

## Publication

- If the video is for README playback, prefer a root-level `readme.mp4` or a GitHub raw URL.
- Keep README copy short and benefit-led.
- When committing, stage only the intended video package. Leave unrelated dirty worktree changes untouched.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: create repository-ready narrated marketing explainer videos with staged slide reveals, TTS audio, licensing credits, previews, and README placement

- use_when: user needs a short product overview video, AI/team explainer video, narrated slide video, Japanese or English marketing video, README-linked MP4, or conversion of a message flow into a video package

- input: target audience, message flow, language, voice/TTS choice, required credits, asset directory, video directory, and publication target

- output: HTML/CSS slide sources, PNG slide states, narration manifest, preview HTML, video build scripts, final MP4, and optional README/docs link

- constraints: keep secrets out of source files; include required audio/voice credits; use staged reveals when narration has question and explanation parts; commit final assets and source scripts but not intermediate audio or segment files unless requested

- lifecycle:
  - startup: clarify purpose, audience, language, voice/TTS engine, and publication target
  - planning: design a problem-to-solution flow with early definition, concrete example, and Before / After comparison
  - execution: render HTML/CSS slide states, capture PNGs, build narration manifest, synthesize audio when needed, and generate MP4
  - monitoring_and_control: inspect representative PNGs, verify timing and metadata, check visible credits, and run repository validation
  - closure: provide final paths, duration, voice credits, and commit only the intended video package when asked

- tags: `marketing`, `video`, `explainer`, `tts`, `voicevox`, `azure-speech`, `slides`, `readme`

- knowledge_slots:
  - name=marketing_video_tts_engine_guidance; bind=9C41D7B2A5E1

- observation_refs:
  - `../../observations/2026-04-30_feedback_marketing-video-production-gaps.md`

Original source description: Create repository-ready marketing explainer videos from a message flow using staged slide reveals, dialogue-style narration, HTML/CSS slide rendering, TTS audio, licensing credits, preview pages, and README/video placement. Use when Codex is asked to make or revise a short explanatory video, overview video, narrated slide video, Japanese/English marketing video, or README-linked product video.
