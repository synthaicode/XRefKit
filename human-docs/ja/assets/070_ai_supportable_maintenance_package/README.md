# AIがサポートできる形で情報を残す インフォグラフィック

- 状態: 1枚絵 PNG、再生成用 `render.mjs` / `diagram.css`
- 目的: 技術者がいなくなった後の維持管理リスクと、AIが支援可能な保守情報の残し方を1枚で説明する

## ファイル構成

- `diagram.css`
  - 共通スタイル
- `render.mjs`
  - HTML を生成する
- `00_infographic.html`
  - 1枚絵の HTML
- `00_infographic.png`
  - レンダリング済み PNG
- `guide_character.png`
  - 既存アセットから流用した案内役キャラクタ

## 再生成手順

```powershell
node human-docs/ja/assets/070_ai_supportable_maintenance_package/render.mjs
```

```powershell
npx --yes playwright screenshot --browser chromium --viewport-size "1600,900" `
  "file:///$PWD/human-docs/ja/assets/070_ai_supportable_maintenance_package/00_infographic.html" `
  "human-docs/ja/assets/070_ai_supportable_maintenance_package/00_infographic.png"
```
