import path from "node:path";
import { defineDeckConfig } from "../../lib/deck-config";

const repoRoot = path.resolve(process.cwd(), "..", "..");

export default defineDeckConfig({
  slug: "effective-ai-use",
  title: "AI を効果的に使う",
  description:
    "AI を性能論ではなく運用論として捉え、成果が出る使い方を共有する画像ベース資料です。",
  sourceLabel: "Source: ja/docs/053_effective_ai_use_presentation.md",
  assetDir: path.join(repoRoot, "ja", "docs", "assets", "053_effective_ai_use"),
});
