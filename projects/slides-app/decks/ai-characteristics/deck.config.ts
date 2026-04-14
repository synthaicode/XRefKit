import path from "node:path";
import { defineDeckConfig } from "../../lib/deck-config";

const repoRoot = path.resolve(process.cwd(), "..", "..");

export default defineDeckConfig({
  slug: "ai-characteristics",
  title: "AI の特性",
  description:
    "AI を過大評価も過小評価もせず、運用上どう扱うべきかを共有する画像ベース資料です。",
  sourceLabel: "Source: ja/docs/052_ai_characteristics_presentation.md",
  assetDir: path.join(repoRoot, "ja", "docs", "assets", "052_ai_characteristics"),
});
