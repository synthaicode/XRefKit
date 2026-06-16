import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/068_ai_handoff_continuity");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const html = (body) => `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <style>${css}</style>
</head>
<body>${body}</body>
</html>`;

const wrap = ({ kicker, title, lead = "", body = "", summary = "", overlay = "", variant = "" }) => `
    <main class="canvas ${variant}">
      ${kicker ? `<div class="kicker">${kicker}</div>` : ""}
      <h1>${title}</h1>
      ${lead ? `<p class="lead">${lead}</p>` : ""}
      <section class="stage">${body}</section>
    ${overlay}
    ${summary ? `<div class="bottom-bar">${summary}</div>` : ""}
    </main>`;

const softList = (items) => `
  <div class="soft-list">
    ${items.map((item) => `<div class="soft-item"><div class="dot"></div><span>${item}</span></div>`).join("")}
  </div>`;

const note = (title, text) => `
  <div class="mini-note">
    <h2>${title}</h2>
    <p>${text}</p>
  </div>`;

const sticker = (title, text) => `
  <div class="sticker">
    <h3>${title}</h3>
    <p>${text}</p>
  </div>`;

const panel = (title, items, tone = "") => `
  <div class="panel ${tone}">
    <h2>${title}</h2>
    <ul>
      ${items.map((item) => `<li>${item}</li>`).join("")}
    </ul>
  </div>`;

const slides = {
  "01_title": wrap({
    kicker: "問題提起",
    title: "技術者がいなくなっても、サービスは残る",
    lead: "システムは止められない。しかし、理解している人はいなくなる。",
    body: `
      <div class="hero">
        <div class="copy-block">
          ${softList([
            "サービスは事業上残り続ける",
            "担当者は異動や退職でいなくなる",
            "理解している人だけが消えると、保守不能化が始まる"
          ])}
        </div>
        <div class="scene">
          <div class="scene-grid">
            <div class="scene-main">
              ${note("残るもの", "本番で動くサービス、ソースコード、設定、DB は残る。")}
              ${note("消えるもの", "判断理由、運用の勘所、危険箇所の理解は人と一緒に消えやすい。")}
              <div class="label-row">
                <div class="label yellow">サービスは残る</div>
                <div class="label pink">理解者はいなくなる</div>
                <div class="label mint">ここが危機</div>
              </div>
            </div>
            <div class="sticker-col">
              ${sticker("管理者視点", "AIの便利さではなく、継続性の危機として問題を置く。")}
            </div>
          </div>
        </div>
      </div>`,
    summary: "サービスは残るが、理解している人はいなくなる。この非対称性が管理上の危機になる"
  }),
  "02_split_experience": wrap({
    kicker: "残るもの / 失われるもの",
    title: "残るのは実体、失われるのは判断理由と運用文脈",
    lead: "ソースコードは残るが、維持管理に必要な文脈は自然には残らない。",
    body: `
      <div class="four-panel">
        ${panel("残るもの", ["ソースコード", "本番環境", "DB", "設定ファイル", "リリース済みサービス"], "blue")}
        ${panel("失われるもの", ["なぜこの設計なのか", "どこを触ると危険なのか", "障害時に何を見るのか"], "pink")}
        ${panel("さらに抜けるもの", ["リリース時の確認点", "過去に何で失敗したのか", "業務上の例外条件"], "yellow")}
        <div class="panel mint">
          <h2>つまり</h2>
          <p>技術的な実体は残る。しかし運用と判断に必要な文脈は、担当者と一緒に失われやすい。</p>
        </div>
      </div>`,
    summary: "サービスの実体は残るが、維持管理に必要な判断理由と運用文脈は自然には残らない"
  }),
  "03_hard_to_handoff": wrap({
    kicker: "管理上のリスク",
    title: "文脈がないサービスは、動いていても管理できない",
    lead: "問題は今動いているかではなく、次の変更と次の障害に耐えられるかです。",
    body: `
      <div class="hero single">
        <div class="scene">
          <div class="scene-grid wide-note">
            <div class="scene-main">
              ${note("資産としてのサービス", "動いているサービスは事業上の資産であり、簡単には止められない。")}
              ${note("負債化するサービス", "維持管理できないまま残ると、次の変更や障害対応で大きな負債になる。")}
              <div class="label-row">
                <div class="label yellow">今動いているか</div>
                <div class="label peach">次の変更に耐えられるか</div>
                <div class="label mint">次の障害に耐えられるか</div>
              </div>
            </div>
            <div class="sticker-col">
              ${sticker("管理者に刺す表現", "動いているサービスは資産だが、維持管理できないサービスは負債になる。")}
            </div>
          </div>
        </div>
      </div>`,
    summary: "文脈のないサービスは、停止していなくても管理不能化のリスクを抱える"
  }),
  "04_information_drift": wrap({
    kicker: "従来の対策の限界",
    title: "ドキュメントを残すだけでは足りない",
    lead: "設計書、手順書、引き継ぎメモだけでは、新任者は状況に応じて使いこなせません。",
      body: `
        <div class="four-panel">
          <div class="panel blue">
          <h2>設計書</h2>
          <p>読む前提なので、必要箇所をその場で案内してはくれない。</p>
        </div>
        <div class="panel yellow">
          <h2>手順書</h2>
          <p>標準手順は書けるが、例外や状況分岐への対応は弱い。</p>
        </div>
        <div class="panel pink">
          <h2>引き継ぎメモ</h2>
          <p>断片情報は残るが、確認、整理、判断補助まではしてくれない。</p>
        </div>
        <div class="panel mint">
          <h2>必要なもの</h2>
          <p>読むだけの資料ではなく、状況に応じて確認・説明・整理・判断補助してくれる入口。</p>
        </div>
      </div>`,
    summary: "ドキュメントは残せても、新任者が状況に応じて使いこなせる入口にはなりにくい"
  }),
  "05_ai_handoff": wrap({
    kicker: "AI を使う意味",
    title: "AIを、残されたサービスを読むための作業 IF にする",
    lead: "人は自然言語で依頼し、AI が裏側の情報をたどりながら説明と整理を行います。",
    body: `
      <div class="hero single">
        <div class="scene">
          <div class="scene-grid">
            <div class="scene-main">
              ${note("AI にこう聞ける", "このサービスの構成を説明して / 本番障害時に最初に見る場所を教えて / この画面を直す場合の影響範囲を出して")}
              ${note("さらに聞ける", "Azure App Service と Azure SQL の関係を整理して / リリース手順を確認して / このエラーが出た場合の確認順を出して")}
            </div>
            <div class="sticker-col">
              ${sticker("入口になる", "Git、Azure、.NET Framework、DB、CI/CD を全部深く知らなくても、AI を入口に維持管理へ入れる。")}
              ${sticker("作業 IF", "人は自然言語で依頼し、AI が必要な情報を裏側でたどる。")}
            </div>
          </div>
        </div>
      </div>`,
    summary: "AI は、残されたサービスを読むための作業入口として機能させられる"
  }),
  "06_repository_reason": wrap({
    kicker: "保守パッケージ",
    title: "必要なのは、AI に渡す保守パッケージ",
    lead: "ドキュメント整備ではなく、AI が読んで新任者を支援できる保守基盤を残します。",
    body: `
      <div class="four-panel">
        ${panel("サービスと構成", ["サービス概要", "構成情報", "ソース情報", "DB 情報"], "blue")}
        ${panel("運用と変更", ["リリース手順", "障害対応", "ログの場所", "初動手順"], "mint")}
        ${panel("判断の文脈", ["判断理由", "触ってはいけない箇所", "既知の失敗", "業務例外"], "pink")}
        ${panel("未解決", ["技術的負債", "既知の不具合", "今後の改善候補"], "yellow")}
      </div>`,
    summary: "必要なのは、AI が読んで新任者を支援できる保守パッケージ"
  }),
  "07_next_person": wrap({
    kicker: "引き継ぎ情報をまとめる効果",
    title: "引き継ぎ情報をまとめると、説明と問題解決に使える",
    lead: "AI が要約し、相手に合わせて説明し、次の確認点を提示できます。",
    body: `
      <div class="hero single">
        <div class="scene">
          <div class="scene-grid wide-note">
            <div class="scene-main">
              <div class="label-row">
                <div class="label yellow">要約する</div>
                <div class="label mint">説明する</div>
                <div class="label pink">解決を補助する</div>
              </div>
              ${note("要約する", "背景を短く整理し、全体像をすぐに伝えられる。")}
              ${note("説明する", "初心者には概要から、経験者には判断点中心から返せる。")}
              ${note("解決を補助する", "何を確認すべきか、どこから調べるべきかを提示できる。")}
            </div>
            <div class="sticker-col">
              ${sticker("相手に合わせる", "新任者にも経験者にも使いやすい。")}
              ${sticker("文脈を再利用する", "断片メモではなく継続利用できる保守文脈になる。")}
            </div>
          </div>
        </div>
      </div>`,
    summary: "引き継ぎ情報は、保存物ではなく、説明と問題解決に使える保守文脈へ変わる"
  }),
  "08_conclusion": wrap({
    kicker: "結論",
    title: "AI導入とは、既存サービスを人がいなくなっても管理可能な状態に変える継続性対策",
    lead: "便利だから使うのではなく、保守不能化を防ぐために使います。",
    body: `
      <div class="hero single">
        <div class="scene">
          <div class="scene-grid wide-note">
            <div class="scene-main">
              ${note("中心メッセージ", "技術者がいなくなる現場では、ソースコードと動作中サービスだけを残しても維持管理できません。構成情報、運用手順、判断理由、障害対応知識を AI が読める形で残し、AI を新任者の作業入口にする必要があります。")}
              <div class="label-row">
                <div class="label yellow">サービスは残る</div>
                <div class="label mint">文脈を残す</div>
                <div class="label peach">AI を入口にする</div>
              </div>
            </div>
            <div class="sticker-col">
              ${sticker("締めの一文", "AI導入とは、既存サービスを人がいなくなっても管理可能な状態に変えるための継続性対策です。")}
            </div>
          </div>
        </div>
      </div>`,
    summary: "AI は、既存サービスを人がいなくなっても管理可能な状態へ近づける継続性対策になる"
  }),
  "00_infographic": wrap({
        kicker: "",
        title: "技術者がいなくなっても、サービスを管理可能にする",
        lead: "ソースコードと稼働環境だけでは足りない。AIが読める保守パッケージを残す。",
      variant: "one-sheet",
    body: `
      <div class="infographic-layout">
        <div class="flow-area">
          <div class="flow-row">
            <div class="flow-step soft-blue">
              <span class="step-no">1</span>
              <strong>技術者が<br>離れる</strong>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step soft-gray">
              <span class="step-no">2</span>
              <strong>サービス・ソース<br>DB・環境は残る</strong>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step soft-pink">
              <span class="step-no">3</span>
              <strong>判断理由・危険箇所<br>運用文脈が失われる</strong>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step soft-red">
              <span class="step-no">4</span>
              <strong>保守不能化<br>リスク</strong>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-step soft-green final">
              <span class="step-no">5</span>
              <strong>AIが読める<br>保守パッケージを残す</strong>
            </div>
          </div>
          <div class="transform-note">
            <span>残る実体</span>
            <div class="transform-line"></div>
            <span>管理できる状態</span>
          </div>
          </div>
          <aside class="package-side">
            <div class="package-box">
              <h2>AIに渡す<br>保守パッケージ</h2>
            <ul>
              <li>サービス概要</li>
              <li>構成情報</li>
              <li>ソース／DB情報</li>
              <li>リリース手順</li>
              <li>障害対応</li>
              <li>判断理由</li>
              <li>未解決事項</li>
            </ul>
          </div>
          <div class="guide-wrap">
            <div class="speech-bubble">AIに渡すのは、作業ではなく保守に必要な文脈です。</div>
            <img class="guide-presenter" src="guide_character.png" alt="" />
          </div>
        </aside>
      </div>
        `,
      summary: ""
    })
};

await fs.mkdir(dir, { recursive: true });

for (const [name, body] of Object.entries(slides)) {
  await fs.writeFile(path.join(dir, `${name}.html`), html(body), "utf8");
}

console.log(`rendered ${Object.keys(slides).length} html files`);
