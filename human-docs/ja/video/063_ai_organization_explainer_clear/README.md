# AI 組織説明動画 改善版

- 状態: 現行モデルへ更新済みのスライド・manifest 一式。MP4 は manifest から再生成して公開する。
- 目的: AI が途中で止まっても未完了を完了扱いにしない、継続可能な AI 作業実行を説明する
- 動画: `ai_team_explainer_clear.mp4`
- 既存の音声付き MP4 は旧ナレーションの場合がある。公開前に現行 manifest から再生成する。
- シナリオ: `../../063_ai_organization_explainer_clear_script.md`
- スライド画像: `../../assets/063_ai_organization_explainer_clear/`
- プレビュー: `index.html`
- 対応表: `manifest.tsv`
- Irodori プレビュー: `index_irodori.html`
- Irodori 対応表: `manifest_irodori.tsv`

## 改善方針

- 冒頭で結論を出す
- 特定リポジトリ名を前面に出さず、一般的な導入ストーリーとして説明する
- `Goal -> semantic routing -> Skill -> Knowledge -> workflow protocol` の関係を説明する
- Goal の最終状態管理と、Skill Run の作業漏れ検査を分けて説明する
- 聞き手が疑問を挟み、解説役が短く答える掛け合い形式にする
- 質問だけを先に表示し、ナレーションに合わせて解説側を後から表示する
- 画面上の `聞き手` / `解説` ラベルは出さず、声と表示タイミングで区別する
- 中盤で、Skill の責務境界と Knowledge の選択的な読み込みを示す
- 終盤に Before / After を置き、導入前後の違いを比較する
- `verify` が進行漏れを検査し、quality review が成果物の受入れを扱う境界を明示する
- AI が途中で止まったときに、run log から再開または handoff できることを説明する
- 1 枚 1 メッセージにする
- 背景を白基調にして、装飾を減らす
- 文字を大きくし、ポイントを番号やチェックで見せる
- 初見向けに専門語を減らす

## 動画化メモ

`build_video.py` は、`manifest.tsv` のナレーション文字数から各スライドの
表示時間を概算し、PNG から無音 mp4 を生成する。

`build_voicevox_video.py` は、起動済みの VOICEVOX Engine
`http://127.0.0.1:50021` を使い、`manifest.tsv` のナレーションを音声化して
音声付き mp4 を生成する。

既定の話者は、解説役が `VOICEVOX:四国めたん / ノーマル`、聞き手が
`VOICEVOX:ずんだもん / ノーマル`。
環境変数 `VOICEVOX_SPEAKER_NAME`、`VOICEVOX_STYLE_NAME`、
`VOICEVOX_LISTENER_SPEAKER_NAME`、`VOICEVOX_LISTENER_STYLE_NAME` で変更できる。

`build_irodori_video.py` は、ローカル clone した Irodori-TTS を呼び出し、
`manifest_irodori.tsv` のナレーションを VoiceDesign で音声化して
音声付き mp4 を生成する。

最低限、次の環境変数が必要:

- `IRODORI_REPO_DIR`: `Aratako/Irodori-TTS` のローカル clone
- `IRODORI_CHECKPOINT`: 既定は `Aratako/Irodori-TTS-500M-v2-VoiceDesign`
- `IRODORI_LISTENER_CAPTION`: 聞き手役の声質指示
- `IRODORI_EXPLAINER_CAPTION`: 解説役の声質指示

既定では、参照音声は使わず `VoiceDesign` の text prompt だけで
聞き手役と解説役を分ける。

## 公開前確認

- 文字が小さくないこと
- 背景と文字のコントラストが十分であること
- 初見で「なぜ必要か」が 30 秒以内に伝わること
- 聞き手の問いで、視聴者が疑問を置いていかれないこと
- VOICEVOX 等の音声を使う場合、必要な帰属表示を入れること
