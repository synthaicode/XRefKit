# AI 組織説明動画 改善版

- 状態: 掛け合い版スライド・ナレーション一式、無音 mp4、VOICEVOX 2 話者音声付き mp4
- 目的: 初見で離脱されにくい AI Team 説明動画を作る
- 動画: `ai_team_explainer_clear.mp4`
- 音声付き動画: `ai_team_explainer_clear_voicevox.mp4`
- シナリオ: `../../063_ai_organization_explainer_clear_script.md`
- スライド画像: `../../assets/063_ai_organization_explainer_clear/`
- プレビュー: `index.html`
- 対応表: `manifest.tsv`

## 改善方針

- 冒頭で結論を出す
- 特定リポジトリ名を前面に出さず、一般的な導入ストーリーとして説明する
- `プロンプト -> Skill -> ドメイン知識 -> AI Team` の順に説明する
- 序盤で `AI Team` を作業体制として定義する
- 聞き手が疑問を挟み、解説役が短く答える掛け合い形式にする
- 質問だけを先に表示し、ナレーションに合わせて解説側を後から表示する
- 画面上の `聞き手` / `解説` ラベルは出さず、声と表示タイミングで区別する
- 各段階で「人間側に新しく増える負担」を先に出す
- 中盤で説明動画制作を例に、Skill / ドメイン知識 / AI Team の境界を示す
- 終盤に Before / After を置き、導入前後の違いを比較する
- AI Team 内の実行役とチェック役を明示する
- AI が作業を忘れることへの対策としてチェック体制を説明する
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

## 公開前確認

- 文字が小さくないこと
- 背景と文字のコントラストが十分であること
- 初見で「なぜ必要か」が 30 秒以内に伝わること
- 聞き手の問いで、視聴者が疑問を置いていかれないこと
- VOICEVOX 等の音声を使う場合、必要な帰属表示を入れること
