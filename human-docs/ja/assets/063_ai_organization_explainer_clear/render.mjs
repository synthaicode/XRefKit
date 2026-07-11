import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/063_ai_organization_explainer_clear");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const escape = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;");

const page = ({ kicker, title, question, answer, summary }) => `<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body>
  <main class="canvas">
    <div class="kicker">${escape(kicker)}</div>
    <h1>${escape(title)}</h1>
    <section class="stage">
      <div class="dialogue-grid${answer ? "" : " question-only"}">
        <div class="bubble question"><div class="card-label">問い</div><h2>${escape(question)}</h2></div>
        ${answer ? `<div class="bubble answer"><div class="card-label">答え</div><p>${escape(answer)}</p></div>` : "<!-- question only -->"}
      </div>
    </section>
    <div class="summary">${escape(summary)}</div>
  </main>
</body></html>`;

const slides = {
  "01_title_q": ["XRefKitの業務実行モデル", "Goalから受入れまで、限定責務をどう接続するか", "業務実行ループは何をつなぐ?", "", "この資料は仕組みの接続関係だけを説明する"],
  "01_title": ["XRefKitの業務実行モデル", "Goalから受入れまで、限定責務をどう接続するか", "全体像は?", "Goal、Semantic routing、Skill、Knowledge参照、Workflow protocol、Evidence、Human acceptanceとHandoffを順に接続する。", "個別作業を、業務の受入れまで切らさずにつなぐ"],
  "02_team_definition_q": ["Goal・目標と受入条件", "Goalは作業一覧ではなく、達成後の状態を持つ", "Goalは何を定義する?", "", "実行回数ではなく、望ましい状態と受入条件を固定する"],
  "02_team_definition": ["Goal・目標と受入条件", "Goalは作業一覧ではなく、達成後の状態を持つ", "何を確認する?", "達成状態と受入条件を保持し、一つのSkillの終了だけでGoalを完了させない。", "業務完了の判定を、AIの停止から分離する"],
  "03_problem_q": ["Skill・限定責務", "Goalへ進むには、複数のSkillが必要になる", "なぜ分割する?", "", "AIが一つの判断方法と成果物へ集中できる単位を作る"],
  "03_problem": ["Skill・限定責務", "Goalへ進むには、複数のSkillが必要になる", "何を分ける?", "判断方法、入力、出力、必要なKnowledge、Handoff境界がまとまる限定責務へ分ける。", "分割は目的を小さくするのではなく、責任を明確にする"],
  "03_prompt_skill_limit": ["業務実行ループ", "GoalとSkillを、Semantic routingとEvidenceでつなぐ", "何を先に決める?", "Goalの終点、Skillの範囲、次を選ぶ条件、未了を残す方法、Human acceptanceの地点を分けて定義する。", "ここから各構成要素を順に見る"],
  "04_work_q": ["Skill・限定責務", "Skillは、AIに任せる範囲を限定する", "限定すると何が変わる?", "", "一つの判断方法と一つの成果物に集中できる"],
  "04_work": ["Skill・限定責務", "Skillは、AIに任せる範囲を限定する", "何を持つ?", "目的、判断範囲、入力、出力、必要なKnowledge、Handoff境界を定義する。", "大きな依頼を、責任を持てる仕事の単位に分ける"],
  "05_not_one_ai_q": ["Semantic routing・意味による次作業選択", "次のSkillは、Goalと現在状態から選ぶ", "何が次のSkillを選ぶ?", "", "人が毎回一覧から手作業で選ぶ運用にしない"],
  "05_not_one_ai": ["Semantic routing・意味による次作業選択", "次のSkillは、Goalと現在状態から選ぶ", "どう選ぶ?", "Semantic routingが、Skillの目的、判断範囲、事前条件を照合して次の限定責務を選ぶ。", "Skillの完了後は、新しい状態から次を選ぶ"],
  "06_repository_q": ["Knowledge・組織固有知識", "Skillは方法を持ち、Knowledgeは判断材料を持つ", "なぜ分ける?", "", "手順と組織固有情報を一つの長い依頼文に混ぜない"],
  "06_repository": ["Knowledge・組織固有知識", "Skillは方法を持ち、Knowledgeは判断材料を持つ", "どう読む?", "Knowledge候補の一覧から選び、必要なXID本文だけを読み込む。", "不要な文脈を減らし、古い知識は更新可能にする"],
  "07_handoff_q": ["Workflow protocol・作業進行規約", "Skillが閉じても、Goalが完了したとは限らない", "途中の仕事はどう管理する?", "", "Skillの完了性とGoalの達成は別に確認する"],
  "07_handoff": ["Workflow protocol・作業進行規約", "Workflow protocolが、Skill実行の作業漏れを検査する", "何を記録する?", "作業項目、成果物、Evidence、unknown、risk、judgment、進行状態、Handoffを実行記録に残す。", "AIの自己申告ではなく、記録から未了を見つける"],
  "08_burden_flow": ["業務実行ループ", "Goal → Semantic routing → Skill → Workflow protocol → Evidence → Handoff", "どこで止める?", "Skillは作業項目とEvidenceを記録し、Workflow protocolが進行漏れを検査する。不足は修復またはHandoffに戻る。", "未完了を成功扱いにせず、次のAIまたは人が再開できる"],
  "08_or_team_q": ["検査", "進行検証は、成果物の内容を自動承認する機能ではない", "進行検証が通れば品質も保証されますか?", "", "進行の完全性と、成果物の受入れは別の軸である"],
  "08_or_team": ["検査", "進行検証は、成果物の内容を自動承認する機能ではない", "何を確認する?", "進行検証は作業項目、根拠、未解決事項、役割、進行記録を検査する。成果物の受入れは必要に応じて品質確認と人が担う。", "検査の対象を分けることで、確認漏れを減らす"],
  "09_value_q": ["中断", "AI が途中で止まっても、仕事を失わない", "中断したらどうする?", "", "止まったことを隠さず、状態を残して再開または引き継ぐ"],
  "09_value": ["Evidence・証跡", "AIが途中で止まっても、仕事を失わない", "何が残る?", "Evidenceに完了済み、未了、根拠、unknown、次の担当を残す。Goalは受入条件が満たされるまで継続する。", "会話履歴や担当者の記憶を再構築する時間を減らす"],
  "10_conclusion_q": ["Human acceptance・人間による受入れ", "人間の仕事は、すべてを監視することではない", "人間は何を担う?", "", "Goalの達成、受入れ、承認、例外判断を担う"],
  "10_conclusion": ["Human acceptance・人間による受入れ", "人間の仕事は、すべてを監視することではない", "どこを見る?", "人はGoalの達成、品質受入れ、承認、例外を判断する。AIの作業状態はWorkflow protocolとEvidenceから確認する。", "人の注意力を、判断が必要な場所へ使う"],
  "11_before_after_q": ["導入前後", "個人の会話から、継続可能な業務実行へ", "何が変わる?", "", "導入前後の違いは、AIの数ではなく仕事の管理方法"],
  "11_before_after": ["導入前後", "個人の会話から、継続可能な業務実行へ", "導入後はどう違う?", "Goalが終点を管理し、Semantic routingが次のSkillを選び、Workflow protocolが漏れを検査し、Knowledgeが判断を支え、EvidenceをHuman acceptanceへ渡す。", "AIの速さを、手戻り削減と継続性へ変える"],
  "12_license_q": ["結論", "AI 活用の効率は、出力速度だけでは決まらない", "なぜこの構造が必要?", "", "再説明、再調査、確認漏れ、引き継ぎ漏れを減らすため"],
  "12_license": ["結論", "AI活用を、管理できる業務実行へ変える", "何を実現する?", "Goal、Semantic routing、Skill、Knowledge、Workflow protocol、Evidence、Human acceptanceを分けて接続し、途中終了を管理して成果を受け入れられる状態にする。", "次は、ツール・AI・人間がそれぞれ何を決めるかを確認する"],
  "13_voicevox_credit": ["クレジット", "音声ライセンス", "VOICEVOX", "VOICEVOX:ずんだもん / VOICEVOX:四国めたん", "音声クレジット"],
  "13_irodori_credit": ["クレジット", "音声クレジット", "Irodori-TTS", "Irodori-TTS VoiceDesign", "音声クレジット"]
};

await fs.mkdir(dir, { recursive: true });
for (const [name, [kicker, title, question, answer, summary]] of Object.entries(slides)) {
  await fs.writeFile(path.join(dir, `${name}.html`), page({ kicker, title, question, answer, summary }), "utf8");
}
console.log(`rendered ${Object.keys(slides).length} html files`);
