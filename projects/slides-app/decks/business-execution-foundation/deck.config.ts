import path from "node:path";
import { defineDeckConfig } from "../../lib/deck-config";

const repoRoot = path.resolve(process.cwd(), "..", "..");

export default defineDeckConfig({
  slug: "business-execution-foundation",
  title: "業務実行基盤への業務取り込み",
  description:
    "業務実行基盤として使うための考え方と、業務をどの粒度から棚卸しして切り分けるかを説明する資料です。",
  sourceLabel: "Source: ja/docs/066_business_execution_foundation_slide_script.md",
  assetDir: path.join(
    repoRoot,
    "ja",
    "docs",
    "assets",
    "066_business_execution_foundation",
  ),
});
