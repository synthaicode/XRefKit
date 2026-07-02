# Structural Feedback Record

- feedback_id: `FB-MKT-001`
- triggered_from: `marketing_video_production_review`
- observed_defect_pattern: the Marketing Group video-production function has strong written scope and completion rules, but the actual video packages and build scripts are inconsistent and weakly enforced
- affected_owner_group: `Marketing Group`
- suspected_root_workflow: `marketing_video_production_workflow`
- suspected_failed_lifecycle_layer: `Monitoring and Control`
- severity: `high`
- evidence:
  - team policy defines a stable default VOICEVOX baseline as `Aoyama Ryusei` with `No.7` as fallback, but the Japanese 063 package defaults to `四国めたん` and `ずんだもん`
  - team policy says the default purpose is to explain XRefKit's AI organization model and OR Team value, but the English 063 package README explicitly says it does not explain XRefKit or OR Team
  - the team skill and usage guide require verification of fps, duration, audio presence, and communication quality, but the current build scripts only assemble output files and print their paths
  - implementation is fragmented by package: Japanese 063 has a VOICEVOX pipeline, English 063 has an Azure TTS pipeline, and English 064 has only a silent-video builder
- immediate_containment_action:
  - keep using the current assets as package-specific outputs, not as a stable generic video-production baseline
  - document the current gaps before assigning new marketing-video work as if the capability were uniform
- upstream_corrective_action:
  - define one canonical production contract for slide rendering, narration schema, TTS selection, QA evidence, and output verification
  - align package defaults with the documented voice policy or revise the policy to match the real baseline
  - separate package-specific message choices from team-level default purpose so README text cannot silently diverge from the team contract
  - add machine-checkable verification for output presence, audio presence, duration, and required credit slides
- next_responsible_group: `Marketing Group`
- or_improvement_id_and_execution_owner: `OR-MKT-001 / Marketing Group owner`
- approval_owner: `Human decision layer`
- first_seen: `2026-04-30`
- last_updated: `2026-04-30`
- recovery_condition:
  - the marketing video function has one documented and reproducible baseline that matches real package defaults and emits explicit QA evidence
- re_observation_condition:
  - complete at least one new explainer-video update on top of the unified baseline without reintroducing policy drift, package divergence, or missing QA evidence
- human_approval_required: `no`

## Diagnosis

The current Marketing Group video-production function is defined as a broad operating capability, not just a one-off asset bundle. On paper, it owns audience definition, explanation structure, narration, audio generation, QA, licensing, and final packaging.

In practice, the repository currently contains several package-local pipelines whose behavior differs by language and explainer series. That makes the feature look mature at the document level while remaining ad hoc at the implementation and verification level.

## Problem Breakdown

### 1. Policy Drift On Default Voices

- documented rule:
  - [Group definitions](../../docs/040_group_definitions.md#xid-8B31F02A4009) and [usage guide](../../docs/051_parapara_video_creation_team_usage_guide.md#xid-5A7C31D9E842) define `VOICEVOX: 青山龍星` as the baseline and `VOICEVOX: No.7` as the next candidate
- implementation state:
  - [ja/docs/video/063_ai_organization_explainer_clear/README.md](../../ja/docs/video/063_ai_organization_explainer_clear/README.md) and [build_voicevox_video.py](../../ja/docs/video/063_ai_organization_explainer_clear/build_voicevox_video.py) default to `四国めたん` and `ずんだもん`
- issue:
  - a user cannot tell whether the true standard is the team policy or the package-local script defaults

### 2. Team Purpose Drift From Shipped Package Messaging

- documented rule:
  - [AI Organization Explainer Video Team operating model](../../docs/057_ai_organization_explainer_video_team_operating_model.md#xid-2E8F4A1C9B73) says the team exists to explain the repository's AI organization model
  - [usage guide](../../docs/051_parapara_video_creation_team_usage_guide.md#xid-5A7C31D9E842) includes XRefKit structure and OR Team in the default presentation sequence
- implementation state:
  - [en/docs/video/063_ai_organization_explainer_clear/README.md](../../en/docs/video/063_ai_organization_explainer_clear/README.md) says the video does not explain XRefKit and does not explain OR Team
- issue:
  - package-local messaging can now contradict the team-level contract without any explicit override mechanism

### 3. QA And Completion Rules Are Not Enforced

- documented rule:
  - the team operating model defines Consistency QA AI, Beginner QA AI, and explicit completion conditions
  - the team skill requires verification of resolution, fps, duration, final file path, and audio presence when TTS is expected
- implementation state:
  - [ja/docs/video/063_ai_organization_explainer_clear/build_video.py](../../ja/docs/video/063_ai_organization_explainer_clear/build_video.py), [ja/docs/video/063_ai_organization_explainer_clear/build_voicevox_video.py](../../ja/docs/video/063_ai_organization_explainer_clear/build_voicevox_video.py), [en/docs/video/063_ai_organization_explainer_clear/build_video.py](../../en/docs/video/063_ai_organization_explainer_clear/build_video.py), [en/docs/video/063_ai_organization_explainer_clear/build_azure_voice_video.py](../../en/docs/video/063_ai_organization_explainer_clear/build_azure_voice_video.py), and [en/docs/video/064_ai_team_operating_boundary/build_video.py](../../en/docs/video/064_ai_team_operating_boundary/build_video.py) build files but do not emit machine-readable QA results
- issue:
  - completion currently depends on manual discipline, so the documented control model is not actually protecting the feature

### 4. Pipeline Capability Is Fragmented By Package

- implementation state:
  - Japanese 063 supports silent video and VOICEVOX audio
  - English 063 supports silent video and Azure TTS audio
  - English 064 supports only silent video
- issue:
  - the repository presents one marketing-video function, but the actual capability varies by package, language, and series number
  - this increases maintenance cost and makes reuse difficult because the common contract lives mostly in prose, not in shared code or shared validation

## Immediate Implication

The current feature is usable for specific checked-in explainer packages, but it is not yet a stable reusable Marketing Group production baseline.

The main risk is not that videos cannot be produced at all. The main risk is that future production work will assume a team-level contract that the implementation does not yet enforce.
