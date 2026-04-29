<!-- xid: 5A7C31D9E842 -->
<a id="xid-5A7C31D9E842"></a>

# AI Organization Explainer Video Team Usage Guide

This page explains how to use the AI Organization Explainer Video Team, formerly
called the Parapara Video Creation Team.

`Parapara` is the slide-based video format. The team purpose is marketing-facing:
it produces an understandable explanation video about this repository's AI
organization model.

This page is a team-specific usage guide.
It is not a general repository operating model and not a system integration design page.
For the team structure and operating loop, see
[AI Organization Explainer Video Team operating model](057_ai_organization_explainer_video_team_operating_model.md#xid-2E8F4A1C9B73).
For the boundary among operating models, usage guides, and design pages, see [Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583).

## Purpose

Use this team when you need to produce a short slide-based marketing or
orientation video that explains XRefKit's AI organization model in plain terms.
The same Marketing Group production function also owns upstream presentation
material creation for explanatory decks: goal definition, issue organization,
information collection, analysis, and structure design.
It also owns standalone one-page repository infographics when the request is to
represent the current repository as a visual operating model.

The team should make the viewer understand:

- this repository is not a place to store model weights
- this repository manages responsibilities, knowledge, workflows, skills,
  evidence, and outputs for AI work
- AI work becomes more stable when responsibility boundaries and checks are made
  explicit
- OR Team exists to keep the organization improving after normal execution work

## Recommended Presentation Structure

Use the following structure as the default chapter sequence when explaining what
this repository's AI organization manages:

1. normal AI use:
   - show that AI use often starts as individual practice
   - show why prompt sharing alone does not create stable operation
2. AI characteristics:
   - explain that AI is useful but can forget, skip, mix responsibilities, and
     drift
3. work structure:
   - explain that real work is a bundle of tasks, checks, handoffs, and
     decisions
4. role composition:
   - explain why multiple AI roles should be composed around responsibility
     boundaries
5. repository structure:
   - show how `docs / flows / capabilities / skills / knowledge / outputs`
     support that organization
6. quality and handoff:
   - explain self-check, evidence, unknown handling, and explicit handoff
7. OR Team:
   - explain why continuous improvement needs observation, improvement, and
     re-observation
8. value:
   - reduce person-dependence
   - align explanation and operating quality
   - make improvement possible
9. conclusion:
   - explain that XRefKit is not a model storage place
   - explain that it is an operating base for stable AI work

## Slide Composition Rule

Reserve the last slide for license display when the video uses assets or voices that require attribution or license notice.

This especially applies when the video uses `VOICEVOX: 青山龍星`, `VOICEVOX: No.7`, or other VOICEVOX-related assets.

The final slide should present the required license or attribution information in a readable form without interfering with the main explanatory slides.

## Audio Tool Baseline

For audio generation work, recognize VOICEVOX Engine Docker as an available standard tool.

Use `VOICEVOX: 青山龍星` as the default baseline voice unless the request explicitly requires a different speaker.
Use `VOICEVOX: No.7` as the next candidate voice when `VOICEVOX: 青山龍星` is not suitable for tone, clarity, or presentation fit.

The upstream README describes VOICEVOX Engine as an HTTP server and presents Docker usage for both CPU and GPU operation.

Reference:

- https://github.com/VOICEVOX/voicevox_engine/blob/master/README.md

## VOICEVOX Engine Docker Startup

Use one of the following startup patterns depending on the runtime environment.

### CPU

```bash
docker pull voicevox/voicevox_engine:cpu-latest
docker run --rm -p 127.0.0.1:50021:50021 voicevox/voicevox_engine:cpu-latest
```

### GPU

```bash
docker pull voicevox/voicevox_engine:nvidia-latest
docker run --rm --gpus all -p 127.0.0.1:50021:50021 voicevox/voicevox_engine:nvidia-latest
```

If the GPU image fails depending on the environment, try adding `--runtime=nvidia`.

## Minimum Audio Generation Flow

The minimum synthesis flow is:

1. prepare narration text
2. query `/speakers` and resolve the speaker ID dynamically for `VOICEVOX: 青山龍星`
3. call `/audio_query`
4. adjust reading or speed if needed
5. call `/synthesis`
6. place the generated wav file onto the edit timeline

Do not assume a fixed speaker ID such as `1`.
The speaker ID may differ by VOICEVOX Engine version or build.

Example:

```bash
curl -s http://127.0.0.1:50021/speakers | jq '.[] | select(.name == "青山龍星")'
# Use the returned style ID for synthesis.
curl -s -X POST "127.0.0.1:50021/audio_query?speaker=<resolved-speaker-id>" --get --data-urlencode "text=こんにちは" > query.json
curl -s -H "Content-Type: application/json" -X POST -d @query.json "127.0.0.1:50021/synthesis?speaker=<resolved-speaker-id>" > audio.wav
```

## Reading Adjustment

When reading quality is not acceptable:

1. confirm the current speaker name and style by querying `/speakers`, not by assuming a fixed ID
2. inspect the `/audio_query` result
3. adjust `speedScale` when timing is too slow or too fast
4. adjust the reading expression when pronunciation or accent is wrong
5. keep `VOICEVOX: 青山龍星` as the first choice unless a voice change solves a presentation requirement more directly
6. use `VOICEVOX: No.7` as the next candidate when the baseline voice does not fit
7. regenerate the wav file and recheck synchronization in the edit timeline

Do not treat the first synthesized output as final without checking timing and reading quality against the slide sequence.

## Request Format

Use this minimum request format:

```text
Target audience:
Purpose:
Desired viewer action:
Presentation goal:
Target duration:
Publication context:
Required source materials:
Voice preference:
License or attribution constraints:
```

If the requester provides only a topic, assume the default purpose is to explain
why this repository treats AI work as an organization instead of a single
general-purpose agent.

## Minimum Production Flow

1. confirm target audience, purpose, viewer action, and target duration
2. define the presentation goal and issue map
3. collect the relevant repository materials and other source inputs
4. analyze the collected information and derive the presentation implications
5. create the message backbone, deck structure, and chapter sequence
6. create one-message-per-slide scenario rows
7. create slide specifications and visual assets
   - for a standalone repository infographic, create a one-page visual section
     map and renderable image specification instead of a slide sequence
8. create narration and timing estimates when the output is video
9. generate or attach audio when the output is video
10. assemble a slide deck or synchronized draft video
11. run consistency QA and beginner QA
12. add license and attribution display when required
13. finalize the distribution package

## Validation Check

Before finalizing the video, confirm at least the following:

1. the target audience and desired viewer action are explicit
2. the presentation goal, issue map, and deck structure are explicit
3. collected information and analysis support the selected structure
4. each slide has a single clear role
5. the narration matches the intended message of the slide when narration exists
6. repository claims are traceable or clearly framed as marketing explanation
7. scene switching does not cut speech unnaturally when the output is video
8. the total duration matches the requested presentation length when duration is requested
9. character or visual differences support, rather than distract from, the explanation
10. the final result is understandable without extra verbal supplementation
11. the output does not imply unsupported product, policy, or business claims
12. the last slide includes the required license and attribution display for the assets and voices used

For a standalone repository infographic, replace slide-specific checks with:

1. the central claim of the image is explicit
2. the image represents the current repository state, not an undocumented future design
3. repository facts are traceable or marked as marketing explanation
4. important control boundaries such as unknown handling, no unsupported guessing, human decision boundaries, and context-direction guard are not lost when they are part of the requested message
5. the PNG is readable at the requested output size
6. reusable HTML/CSS/render sources are preserved with the final image

## Related

- [AI Organization Explainer Video Team operating model](057_ai_organization_explainer_video_team_operating_model.md#xid-2E8F4A1C9B73)
- [Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583)
- [Group definitions](040_group_definitions.md#xid-8B31F02A4009)
