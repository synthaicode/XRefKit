<!-- xid: 9C41D7B2A5E1 -->
<a id="xid-9C41D7B2A5E1"></a>

# Marketing Video TTS Engine Guidance

This page defines how narrated video work should choose and use TTS engines for
repository-facing marketing or explainer outputs.

## Purpose

Keep TTS selection explicit when a Skill or team produces narrated video.
The goal is to separate:

- default low-friction narration paths
- expressive Japanese narration paths
- upstream-confirmed facts
- article-level observations that still require local verification

## Engine Selection Rule

- Keep `VOICEVOX` as the default baseline for local narration when the work
  needs predictable local setup, HTTP-based synthesis, and repository-standard
  voice-credit handling.
- Use `Irodori-TTS` when the request specifically benefits from expressive
  Japanese line reading, caption-driven voice design, or reference-audio-based
  voice conditioning.
- Do not treat `Irodori-TTS` as the default real-time dialogue engine for this
  repository's video work. It is a candidate for offline segment generation.

## Upstream-Confirmed Facts

- The upstream repository exposes CLI inference plus two Gradio entrypoints:
  - `gradio_app.py` for the v3 base model
  - `gradio_app_voicedesign.py` for the v2 VoiceDesign model
- The upstream quick-start uses `uv` for environment setup and supports
  mutually exclusive backend extras such as `cu128`, `rocm`, and `cpu`.
- The `main` branch tracks the v3 codebase for the base model, while
  VoiceDesign remains on the v2 checkpoint family.
- The repository code is published under the MIT license.

## Article-Derived Observations

- The referenced Zenn article presents `Irodori-TTS` as a strong local option
  for expressive Japanese narration and highlights punctuation, text phrasing,
  and emoji-like cues as effective style signals.
- The article describes it as a good fit for narration, e-learning, podcasts,
  and voice-drama-like segment production rather than tightly real-time
  response work.
- Treat quality, latency, and commercial-use assumptions from the article as
  prompts for local verification, not as closure-ready evidence by themselves.

## Operational Guidance For Skills

- When a Skill chooses `Irodori-TTS`, keep the work segmented by narration row
  or scene so the best take can be regenerated without rebuilding the whole
  video.
- Prefer the v3 base path when reference audio is available and predictable
  duration handling matters.
- Prefer the VoiceDesign path when the request is style-led and can be
  satisfied with text-side voice description instead of reference audio.
- Keep generated intermediate wav files out of commits unless the user
  explicitly asks to preserve them.
- Record the exact checkpoint family, launch mode, and prompting approach in
  the build notes when the result depends on them.

## Minimum Setup Pointers

- Base UI example:
  - `uv run python gradio_app.py --server-name 0.0.0.0 --server-port 7860`
- VoiceDesign UI example:
  - `uv run python gradio_app_voicedesign.py --server-name 0.0.0.0 --server-port 7861`
- CLI example:
  - `uv run python infer.py --hf-checkpoint Aratako/Irodori-TTS-500M-v3 --text "<text>" --ref-wav <wav> --output-wav <out>`

## Verification Rule

- Before treating `Irodori-TTS` output as production-ready, verify:
  - reading quality against the actual script
  - segment timing against the slide sequence
  - whether the chosen checkpoint path matches the intended control method
  - whether the current model-card and distribution terms fit the intended use

## References

- Upstream repository:
  - https://github.com/Aratako/Irodori-TTS
- Operator-facing introduction article:
  - https://zenn.dev/acntechjp/articles/530307d5e9c459
