# XRefKit リポジトリ説明動画

- 目的: 現在の XRefKit が何を管理しているかを、初見向けに短く説明する
- 形式: 質問 -> 解説 の 2 状態スライド
- 出力: `xrefkit_repository_overview_ja.mp4`
- シナリオ: `../../065_xrefkit_repository_overview_script.md`
- スライド画像: `../../assets/065_xrefkit_repository_overview/`
- プレビュー: `index.html`
- 対応表: `manifest.tsv`

## メッセージ

- XRefKit は単なる文書置き場ではない
- `docs / flows / capabilities / skills / knowledge / work / sources` を役割別に分離している
- Skill は runtime envelope で管理される
- context direction guard が外部入力による方針破壊を防ぐ
- handoff は session log と closure 確認でつなぐ
- 人間は最終的なトレードオフと承認境界を持つ

## Build

レンダリング:

```powershell
node ja/docs/assets/065_xrefkit_repository_overview/render.mjs
```

PNG 作成:

```powershell
python ja/docs/assets/065_xrefkit_repository_overview/render_pngs.py
```

無音動画作成:

```powershell
python ja/docs/video/065_xrefkit_repository_overview/build_video.py
```
