# AIに作業を引き継ぐとは何か キャラクタ版アセット

- 状態: 画像ベーススライド 8 枚、再生成用 `render.mjs` / `diagram.css`
- シナリオ: `../../068_ai_handoff_continuity_slide_script.md`
- プレゼン資料: `../../069_ai_handoff_continuity_presentation.md`
- 元説明資料: `../../067_ai_handoff_continuity_material.md`

## 目的

人間の異動で知識継承が劣化する問題に対して、
`AIに作業を引き継ぐ` とは何かを、
知的な男性ガイドキャラクタ付きのスライドで説明する。

この版では、次の価値を明示する。

- AI 可読な形で業務文脈を残す
- 次の担当者がその文脈を参照して継続できる
- AI が相手の経験や役割に合わせて説明レベルを調整できる

## ファイル構成

- `diagram.css`
  - 共通スタイル
- `render.mjs`
  - 8 枚分の HTML を生成する
- `01_title.html` - `08_conclusion.html`
  - 各スライドの HTML
- `01_title.png` - `08_conclusion.png`
  - 各スライドの PNG

## 再生成手順

```powershell
node human-docs/ja/assets/068_ai_handoff_continuity/render.mjs
```

```powershell
$files = '01_title','02_split_experience','03_hard_to_handoff','04_information_drift','05_ai_handoff','06_repository_reason','07_next_person','08_conclusion'
foreach ($name in $files) {
  npx --yes playwright screenshot --browser chromium --viewport-size "1600,900" `
    "file:///$PWD/human-docs/ja/assets/068_ai_handoff_continuity/$name.html" `
    "human-docs/ja/assets/068_ai_handoff_continuity/$name.png"
}
```

## 現在の表現上の注意

- キャラクタは `guide_character.png` を使っている
- 元画像は `C:\Users\seiji_yfc8940\.codex\generated_images\019e0b65-be5e-7ff3-8bc4-d04abd633891\ig_0ed6f4f9e3f91c3b0169feec8f921c81918865370502623b2e.png`
- 同じレイアウトで、将来ほかの立ち絵へ差し替えることもできる
- 画面下部の青帯に、そのスライドの短い結論を固定している

## 確認済み

- HTML 8 枚生成
- PNG 8 枚生成
- `python -m xrefkit xref fix` 通過
