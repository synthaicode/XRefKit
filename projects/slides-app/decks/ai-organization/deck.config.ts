import path from "node:path";
import { defineDeckConfig } from "../../lib/deck-config";

const repoRoot = path.resolve(process.cwd(), "..", "..");

export default defineDeckConfig({
  slug: "ai-organization",
  title: "AI 組織 紹介",
  description:
    "既存の XRefKit 画像ベース資料を、DexCode 風の MDX スライドビューアで閲覧する最初の導入デッキです。",
  sourceLabel: "Source: ja/docs/051_ai_organization_presentation.md",
  assetDir: path.join(repoRoot, "ja", "docs", "assets", "051_ai_organization"),
});
