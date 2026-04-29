<!-- xid: A6B923E41178 -->
<a id="xid-A6B923E41178"></a>

# Skill Meta: marketing-explainer-video

- skill_id: `marketing-explainer-video`
- summary: create repository-ready narrated marketing explainer videos with staged slide reveals, TTS audio, licensing credits, previews, and README placement
- use_when: user needs a short product overview video, AI/team explainer video, narrated slide video, Japanese or English marketing video, README-linked MP4, or conversion of a message flow into a video package
- input: target audience, message flow, language, voice/TTS choice, required credits, asset directory, video directory, and publication target
- output: HTML/CSS slide sources, PNG slide states, narration manifest, preview HTML, video build scripts, final MP4, and optional README/docs link
- execution_mode: `local_default`
- guard_policy: `required`
- os_contract:
  - version: `1`
  - worklist_policy: `required`
  - execution_role: `required`
  - check_role: `required`
  - logging_policy: `session_required`
  - judgment_log_policy: `required_when_non_trivial`
  - unknown_risk_policy: `explicit`
  - closure_gate: `required`
  - handoff_policy: `explicit`
- constraints: keep secrets out of source files; include required audio/voice credits; use staged reveals when narration has question and explanation parts; commit final assets and source scripts but not intermediate audio or segment files unless requested
- lifecycle:
  - startup: clarify purpose, audience, language, voice/TTS engine, and publication target
  - planning: design a problem-to-solution flow with early definition, concrete example, and Before / After comparison
  - execution: render HTML/CSS slide states, capture PNGs, build narration manifest, synthesize audio when needed, and generate MP4
  - monitoring_and_control: inspect representative PNGs, verify timing and metadata, check visible credits, and run repository validation
  - closure: provide final paths, duration, voice credits, and commit only the intended video package when asked
- tags: `marketing`, `video`, `explainer`, `tts`, `voicevox`, `azure-speech`, `slides`, `readme`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
