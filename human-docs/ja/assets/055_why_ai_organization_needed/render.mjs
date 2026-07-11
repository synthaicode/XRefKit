import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/055_why_ai_organization_needed");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const frame = (title, subtitle, body, summary) => `<div class="canvas">
  <h1 class="title">${title}</h1>
  <p class="subtitle">${subtitle}</p>
  ${body}
  <div class="summary-band"><strong>${summary}</strong></div>
</div>`;

const node = (title, body, tone = "soft-blue") => `<div class="diagram-node ${tone}"><h3>${title}</h3><p>${body}</p></div>`;
const arrow = (label = "") => `<div class="diagram-arrow"><span>${label}</span>→</div>`;
const row = (...parts) => `<div class="flow-row">${parts.join("")}</div>`;

const renderers = {
  "00_intro": () => frame(
    "通常のAI利用だけでは、継続的な業務実行にならない",
    "AIの特性を前提に問題を分け、それぞれに異なる仕組みを用意する",
    `<div class="hero-flow">
      ${node("通常のAI利用", "その都度、依頼文と会話で作業を進める")}
      ${arrow("AIの特性を確認")}
      ${node("問題を細分化", "完了、責務、進行、知識、接続の問題に分ける", "soft-orange")}
      ${arrow("問題ごとに設計")}
      ${node("業務実行の仕組み", "一つの万能機能ではなく、独立した解決策を持つ", "soft-green")}
    </div>`,
    "最初に仕組みを並べるのではなく、AIの特性から解くべき問題を分ける。"
  ),
  "01_title": () => frame(
    "AIの特性から、業務実行上の問題を分ける",
    "異なる問題を一つの仕組みで解こうとしない",
    `<div class="trait-map">
      ${row(node("局所作業を終えられる", "業務全体の完了は分からない"), arrow(), node("完了の問題", "何を満たせば業務完了か", "soft-orange"))}
      ${row(node("目的を絞ると能力を発揮する", "大きな依頼では判断範囲が広がる"), arrow(), node("責務の問題", "何を担当させるか", "soft-orange"))}
      ${row(node("途中でも応答を終了する", "未完了が会話に埋もれる"), arrow(), node("進行の問題", "作業漏れをどう残すか", "soft-orange"))}
      ${row(node("一般化された知識で応答する", "組織固有の判断材料は持たない"), arrow(), node("知識の問題", "何を判断材料にするか", "soft-orange"))}
    </div>`,
    "AIの弱点を一括りにせず、業務実行で現れる問題ごとに扱う。"
  ),
  "02_individual_limit": () => frame(
    "細分化した問題には、それぞれ別の解決策がある",
    "各仕組みは役割が異なり、相互の代用品ではない",
    `<div class="solution-map">
      ${row(node("業務完了を認識できない", "局所作業の終了と業務完了が混ざる"), arrow("解決"), node("Goal", "目標と受入条件を定義する", "soft-green"))}
      ${row(node("大きな目的では範囲が広すぎる", "判断と成果物が拡散する"), arrow("解決"), node("Skill", "限定責務へ分ける", "soft-green"))}
      ${row(node("途中で作業を終了する", "未完了や根拠が残らない"), arrow("解決"), node("Workflow protocol", "作業状態と終了条件を管理する", "soft-green"))}
      ${row(node("組織の判断を再現できない", "一般知識だけでは材料が不足する"), arrow("解決"), node("Knowledge", "組織固有知識を参照する", "soft-green"))}
      ${row(node("細分化した作業がつながらない", "次に何を行うか選ぶ必要がある"), arrow("解決"), node("Semantic routing", "目標と現在状態から次を選ぶ", "soft-green"))}
    </div>`,
    "全体像は対応関係として示し、各解決策の詳細は別々に確認する。"
  ),
  "03_input_organization": () => frame(
    "目標と受入条件は、業務の完了を定義する",
    "AIが停止した時点ではなく、達成後の状態で完了を判断する",
    `<div class="decision-flow">
      ${node("局所作業の終了", "AIが依頼された出力を返す")}
      ${arrow("業務完了ではない")}
      ${node("受入条件を確認", "達成状態を満たしているか", "soft-orange")}
      <div class="branch-grid">
        ${node("未達", "目標を継続し、残りの作業を明示する", "soft-red")}
        ${node("達成", "人が業務成果として受け入れる", "soft-green")}
      </div>
    </div>`,
    "目標が解くのは、局所作業の終了と業務完了を混同する問題である。"
  ),
  "04_scattered_controls": () => frame(
    "限定責務は、大きな目標をAIが集中できる単位へ分ける",
    "担当範囲、判断方法、入力、出力を一つの目的に限定する",
    `<div class="decomposition-flow">
      ${node("大きな業務目標", "複数の判断と成果物を含む", "soft-orange")}
      ${arrow("必要な作業へ細分化")}
      <div class="responsibility-grid">
        ${node("限定責務 1", "一つの判断方法と成果物")}
        ${node("限定責務 2", "一つの判断方法と成果物")}
        ${node("限定責務 3", "一つの判断方法と成果物", "soft-green")}
      </div>
    </div>`,
    "限定責務が解くのは、AIの担当範囲が広がりすぎる問題である。"
  ),
  "05_organization_role": () => frame(
    "作業進行規約は、途中終了を完了として扱わない",
    "責務を決めるのではなく、担当した作業の進行と終了を管理する",
    `<div class="decision-flow">
      ${node("AIが作業を終了", "応答が終わっても未完了の可能性がある")}
      ${arrow("進行状態を検査")}
      ${node("作業項目・成果物・根拠・未確定事項", "必要な記録と終了条件を確認する", "soft-orange")}
      <div class="branch-grid">
        ${node("不足あり", "未完了として残し、修復または引継ぎへ戻す", "soft-red")}
        ${node("不足なし", "責務単位の作業を終了できる", "soft-green")}
      </div>
    </div>`,
    "作業進行規約が解くのは、作業途中の終了と作業漏れの問題である。"
  ),
  "06_organization_value": () => frame(
    "組織固有知識は、実務判断に必要な材料を与える",
    "AIの一般知識と、組織のルールや例外を混同しない",
    `<div class="knowledge-flow">
      ${node("AIの一般知識", "一般的な概念、方法、事例")}
      <div class="plus">＋</div>
      ${node("組織固有知識", "ルール、対象、例外、過去の判断", "soft-green")}
      ${arrow("必要なXIDだけ参照")}
      ${node("組織の業務判断", "固有の条件に基づいて判断する", "soft-orange")}
    </div>`,
    "組織固有知識が解くのは、一般知識だけでは組織の判断を再現できない問題である。"
  ),
  "07_human_control_unit": () => frame(
    "意味による次作業選択は、細分化した限定責務をつなぐ",
    "限定責務そのものではなく、細分化によって生じた接続問題を解く",
    `<div class="routing-flow">
      <div class="input-stack">
        ${node("目標", "どの達成状態へ向かうか")}
        ${node("現在状態", "何が完了し、何が未了か")}
      </div>
      ${arrow("照合")}
      ${node("意味による次作業選択", "次に必要な責務を選ぶ", "soft-orange")}
      ${arrow("選択")}
      ${node("次の限定責務", "現在必要な判断と成果物", "soft-green")}
    </div>`,
    "次作業選択が解くのは、分割した仕事を目標へ向けて接続する問題である。"
  ),
  "08_ai_control_unit": () => frame(
    "人は、成果物の受入れと例外判断を担う",
    "機械的な進行検証と、業務として採用する判断を分ける",
    `<div class="acceptance-map">
      ${node("進行検証", "作業項目、記録、未解決事項の完全性を確認する")}
      ${node("品質確認", "成果物が要求する品質を満たすか確認する", "soft-orange")}
      ${node("人による受入れ", "承認、例外、トレードオフを判断する", "soft-green")}
    </div>`,
    "作業が漏れなく進んだことと、業務成果として受け入れることは別の判断である。"
  ),
  "09_conclusion": () => frame(
    "通常のAI利用を、継続可能な業務実行へ変える",
    "問題ごとの仕組みを、EvidenceとHuman acceptanceまで接続する",
    `<div class="conclusion-grid">
      ${node("Goal", "目標と受入条件")}
      ${node("Skill", "限定責務")}
      ${node("Workflow protocol", "作業進行規約")}
      ${node("Knowledge", "組織固有知識")}
      ${node("Semantic routing", "意味による次作業選択", "soft-green")}
      ${node("Evidence", "証跡")}
      ${node("Human acceptance", "人間による受入れ")}
    </div>`,
    "これらの異なる仕組みは、どのように一つの業務完了へ接続されるのでしょうか。"
  )
};

const html = (body) => `<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`;
for (const [name, render] of Object.entries(renderers)) {
  await fs.writeFile(path.join(dir, `${name}.html`), html(render()), "utf8");
}
console.log(`rendered ${Object.keys(renderers).length} slides`);
