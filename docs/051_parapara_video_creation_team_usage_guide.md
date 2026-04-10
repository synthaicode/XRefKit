<!-- xid: 5A7C31D9E842 -->
<a id="xid-5A7C31D9E842"></a>

# Parapara Video Creation Team Usage Guide

This page explains the minimum operating memo for the Parapara Video Creation Team.

This page is a team-specific usage guide.
It is not a general repository operating model and not a system integration design page.
For the boundary among operating models, usage guides, and design pages, see [Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583).

## Purpose

Use this team when you need to produce a short slide-based video with explicit role separation across composition, audio, visual, editing, and validation.

## Recommended Presentation Structure

Use the following structure as the default chapter sequence when explaining what an AI team repository manages:

1. title:
   - `AIチームのリポジトリは何を管理しているのか`
2. purpose of this repository:
   - show that the repository is not a place to make AI look smart
   - show that it manages roles, knowledge, and work flow
3. why AI is organized as a team:
   - explain that a single AI tends to mix responsibilities
   - explain that planning, production, and inspection should be separated
4. team overview:
   - show a bird's-eye view of each AI responsibility
5. end-to-end flow:
   - `題材入力 -> 読解 -> シナリオ -> スライド -> 音声 -> QA -> 公開`
6. repository contents:
   - show the repository through elements such as `knowledge / skill / workflow / templates / outputs`
7. actual work unit:
   - show how a single slide is produced as an example
8. quality control:
   - cover beginner-friendly expression
   - cover content consistency
   - cover synchronization between narration and screen
   - cover terminology consistency
9. value of this repository:
   - reduce person-dependence
   - align explanation quality
   - make improvement possible
10. conclusion:
   - explain that an AI team repository is not a model storage place
   - explain that it is an operating base for producing explanations in a stable way

## Team Roles

The team is composed of the following roles:

1. planning lead AI:
   - main responsibility:
     - manage the overall purpose, target audience, and completion criteria
   - input:
     - purpose
     - target
     - source materials
   - output:
     - work instructions
     - chapter structure
     - completion criteria
2. learner model AI:
   - main responsibility:
     - organize understanding gaps for beginner and intermediate learners
   - input:
     - assumed audience
     - terminology list
   - output:
     - explanation-level definition
     - prohibited and supplemental term list
3. repository reading AI:
   - main responsibility:
     - organize repository structure and responsibility boundaries
   - input:
     - `README`
     - `docs/`
     - structure information
   - output:
     - repository explanation memo
     - glossary
     - issue list
4. scenario AI:
   - main responsibility:
     - build the order of the story
   - input:
     - repository reading memo
     - target explanation level
   - output:
     - chapter structure
     - one-message-per-slide script
5. slide design AI:
   - main responsibility:
     - decide what appears on screen
   - input:
     - script
   - output:
     - slide specification
6. narration AI:
   - main responsibility:
     - prepare the spoken script
   - input:
     - script
     - slide specification
   - output:
     - narration script
     - duration estimate
7. diagram and direction AI:
   - main responsibility:
     - design diagrams, icons, and screen density
   - input:
     - slide specification
   - output:
     - visual instructions
8. consistency QA AI:
   - main responsibility:
     - check content, order, and expression consistency
   - input:
     - all deliverables
   - output:
     - issue list
     - whether correction is required
9. beginner QA AI:
   - main responsibility:
     - check whether the material is too difficult
   - input:
     - script
     - slides
   - output:
     - beginner-perspective review
10. final editing AI:
   - main responsibility:
     - integrate outputs
   - input:
     - corrected deliverable set
   - output:
     - distribution slide deck
     - narration script
     - public release version

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

## Validation Check

Before finalizing the video, confirm at least the following:

1. each slide has a single clear role
2. the narration matches the intended message of the slide
3. scene switching does not cut speech unnaturally
4. the total duration matches the requested presentation length
5. character or visual differences support, rather than distract from, the explanation
6. the final result is understandable without extra verbal supplementation
7. the last slide includes the required license and attribution display for the assets and voices used

## Related

- [Operating models, usage guides, and design pages](022_operating_models_guides_and_designs.md#xid-9C4E2A71D583)
- [Group definitions](040_group_definitions.md#xid-8B31F02A4009)
