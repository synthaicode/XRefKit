import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/073_xrefkit_organization_distribution");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const slides = [
  ["01_title", "多くの責務実行から、改善すべき実行をどう見つけるのですか。", "実行状況ダッシュボードが、改善判断の入口になります。", "状態、終了確認、未確認事項、リスク、引継ぎ、不足情報を一覧化し、人間が確認対象を絞ります。", [["観測", "work/sessionsの記録を、人間が比較できる状態へまとめます。"], ["境界", "Skill Run Dashboardは観測画面であり、責務実行や自動改訂は行いません。"]], "最初に全実行を読み込まず、異常と不足が見える実行から確認します。", "dashboard_overview.jpg"],
  ["02_unit", "一覧では、どの状態を確認対象にするのですか。", "停止、終了確認、品質確認、不足情報から対象を絞ります。", "状態だけで完了を判断せず、終了確認と品質確認、未確認事項、リスク、引継ぎ、不足情報を組み合わせて見ます。", [["進行", "進行中と停止中の状態から、確認すべき実行を見つけます。"], ["完了", "終了済みでも、終了確認と品質確認が妥当かを分けて確認します。"], ["不足", "記録不足は実行結果と分離し、改善用の観測として扱います。"]], "集計値は結論ではなく、詳細を読む対象を選ぶための入口です。"],
  ["03_package", "一件の責務実行では、何を確認するのですか。", "作業、証跡、懸念、終了判定を一件単位で確認します。", "作業項目、成果物、未確認事項、リスク、判断、引継ぎ、進行状態を見て、どこまで実行され、何が残ったかを確認します。", [["実行内容", "作業項目と進行状態から、予定した処理の進み方を確認します。"], ["根拠", "成果物と証跡から、成果と判断根拠を辿ります。"], ["未解決", "懸念と引継ぎから、人間または次のSkillへ戻す事項を確認します。"]], "AIの完了報告ではなく、構造化された実行記録から状態を判断します。"],
  ["04_generation", "どのKnowledgeが選ばれ、実際に使われたか分かりますか。", "実行識別子で記録を結び、XIDの利用段階を分けます。", "利用可能、選択、解決、読込、適用を区別し、選択後に使われなかったKnowledgeを確認します。", [["相関", "同じ実行識別子（run_id）でクライアント記録とMCP監査記録を結びます。"], ["段階", "選択・解決・読込・適用を同じ意味にまとめません。"]], "不使用XIDだけで削除を決めず、どの段階で止まったかを確認します。", "dashboard_xid_usage.jpg"],
  ["05_providers", "改善判断に必要な記録が足りない場合は、どう分かりますか。", "不足情報と相関の切れ目を、実行横断で順位付けします。", "実行識別子、routing、XID読込・適用、検索、人間の評価、実行結果、トークン使用量の不足を分けて示します。", [["一件", "選択した実行で欠けている改善材料を確認します。"], ["横断", "複数実行で繰り返す不足を、優先的な改善候補にします。"]], "記録不足を成果物の失敗と混同せず、観測設計の改善対象として扱います。", "dashboard_missing_information.jpg"],
  ["06_mcp", "実行状況ダッシュボードが、KnowledgeやSkillを自動で直すのですか。", "観測結果から何を直すかは、人間が判断します。", "繰り返す停止、誤った選択、過不足のあるKnowledge、弱い受入条件を区別し、変更先を決めます。", [["Skill", "手順、責任範囲、引継ぎ、検査項目の不足を直します。"], ["Knowledge・routing", "内容の不足・過剰と選択条件を分けて直します。"], ["受入条件", "完了と判断できない原因がGoal側なら、受入条件へ戻します。"]], "実行状況ダッシュボードは判断材料を提供し、改訂と承認の責任は人間に残します。"],
  ["07_bootstrap", "判断した改善を、次の版へどう反映するのですか。", "正本を改訂し、検証と人間の承認を通して次版にします。", "Knowledge、Skill、routing、受入条件を正本へ戻し、XID参照、契約、版、互換性を決定的に検証します。", [["改訂", "観測と判断根拠を保ったまま、管理中の正本を変更します。"], ["検証", "参照整合性、契約、互換性、パッケージ内容を確認します。"], ["承認", "人間が配布可能な次版として受け入れます。"]], "観測値から正本を直接書き換えず、改訂・検証・承認を分離します。"],
  ["08_conclusion", "検証された次版は、改善されたとどう確認するのですか。", "次版を配布し、次の責務実行を再び観測します。", "パッケージまたはMCPで承認版を届け、同じ観測項目で停止、不足、XID利用、結果の変化を確認します。", [["配布", "版管理されたKnowledge、Skill、契約を利用環境へ届けます。"], ["再実行", "次のGoalで新しい版を使い、同じ責務を実行します。"], ["再観測", "実行状況ダッシュボードで変化を確認し、次の改善判断へ戻します。"]], "観測、判断、改訂、検証、配布、再観測を一つの改善循環にします。"],
].map(([name, question, title, copy, cards, takeaway, screenshot]) => ({ name, question, title, copy, cards, takeaway, screenshot }));

function cardsHtml(cards) {
  return cards.map(([tag, text]) => `<article class="card"><div class="card-tag">${tag}</div><p>${text}</p></article>`).join("");
}

function layout(slide) {
  const body = slide.screenshot
    ? `<section style="display:grid;grid-template-columns:1.8fr 1fr;gap:24px;align-items:start"><img src="${slide.screenshot}" alt="Skill Run Dashboard" style="width:100%;border:1px solid #dbe3ee;border-radius:8px"><section class="cards" style="grid-template-columns:1fr">${cardsHtml(slide.cards)}</section></section>`
    : `<section class="summary"><div class="summary-label">問い</div><div class="summary-copy">${slide.question}</div><div class="summary-title">${slide.copy}</div></section><section class="cards">${cardsHtml(slide.cards)}</section>`;
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8" /><title>${slide.title}</title><style>${css}</style></head><body><main class="slide"><header class="header"><div><div class="eyebrow">改善と組織配布</div><h1 class="title">${slide.title}</h1></div><div class="brand">XRefKit</div></header>${body}<div class="takeaway">${slide.takeaway}</div></main></body></html>`;
}

function questionOnly(slide) {
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8" /><title>${slide.question}</title><style>${css}</style></head><body><main class="slide"><header class="header"><div><div class="eyebrow">改善と組織配布</div><h1 class="title">Skill Run Dashboardから、次版の配布までを辿ります。</h1></div><div class="brand">XRefKit</div></header><section class="question-wrap"><div class="question-box"><div class="question-label">問い</div><div class="question-text">${slide.question}</div></div></section><div class="takeaway"><strong>運用上の疑問</strong>を先に置き、観測から改善までを一つずつ確認します。</div></main></body></html>`;
}

for (const slide of slides) {
  await fs.writeFile(path.join(dir, `${slide.name}_q.html`), questionOnly(slide), "utf8");
  await fs.writeFile(path.join(dir, `${slide.name}.html`), layout(slide), "utf8");
}

console.log(`rendered ${slides.length * 2} html files`);
