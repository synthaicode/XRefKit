# AI Team Explainer Video

This is the English version of the AI Team explainer.

## Message

- The flow is Prompt -> Skill -> domain knowledge -> AI Team.
- The video does not explain XRefKit.
- The video does not explain OR Team.
- Each topic is split into a question-only state and an explanation state.
- The visual labels for questioner/explainer are intentionally removed.
- The key claim is that AI does not simply remove work. It can move management work onto humans unless the operating structure is designed.

## Outputs

- `ai_team_explainer_clear_en.mp4`: silent English video with staged reveals.
- `ai_team_explainer_clear_en_azure.mp4`: English video with Azure Neural TTS audio.
- `index.html`: slide preview with English narration text.
- `manifest.tsv`: source order and narration text.

## Build

Render slides:

```powershell
node en/docs/assets/063_ai_organization_explainer_clear/render.mjs
```

Capture PNGs:

```powershell
$dir='en/docs/assets/063_ai_organization_explainer_clear'
foreach ($name in @('01_title_q','01_title','02_team_definition_q','02_team_definition','03_problem_q','03_problem','04_work_q','04_work','05_not_one_ai_q','05_not_one_ai','06_repository_q','06_repository','07_handoff_q','07_handoff','08_or_team_q','08_or_team','09_value_q','09_value','10_conclusion_q','10_conclusion','11_before_after_q','11_before_after','12_license_q','12_license')) {
  npx --yes playwright screenshot --viewport-size='1600,900' "$dir/$name.html" "$dir/$name.png"
}
```

Build video:

```powershell
python en/docs/video/063_ai_organization_explainer_clear/build_video.py
```

Build Azure voice video:

```powershell
$env:AZURE_SPEECH_KEY="..."
$env:AZURE_SPEECH_REGION="japanwest"
python en/docs/video/063_ai_organization_explainer_clear/build_azure_voice_video.py
```

Optional voices:

```powershell
$env:AZURE_SPEECH_QUESTION_VOICE="en-US-GuyNeural"
$env:AZURE_SPEECH_ANSWER_VOICE="en-US-JennyNeural"
```
