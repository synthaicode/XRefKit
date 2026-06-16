import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("human-docs/ja/assets/070_ai_supportable_maintenance_package");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const html = `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <style>${css}</style>
</head>
<body>
  <main class="canvas">
    <section class="header">
      <div class="title-block">
        <h1>AIがサポートできる形で情報を残す</h1>
        <p class="subtitle">ソースコードと動作中サービスだけでは維持管理できない。<br>必要なのは、AIが支援できる形で保守情報を残すこと。</p>
      </div>
      <div class="guide-zone">
        <div class="speech">未来のチームを助けるために、今、残しましょう！</div>
        <img class="guide" src="guide_character.png" alt="" />
      </div>
    </section>

    <section class="panel-grid">
      <article class="panel blue">
        <div class="panel-head">
          <div class="index">1</div>
          <h2>問題</h2>
        </div>
        <div class="panel-body">
          <ul>
            <li>技術者がいなくなってもサービスは残る</li>
            <li>止められないが、理解者はいなくなる</li>
            <li>ここから保守不能化が始まる</li>
          </ul>
          <div class="scene">
            <div class="chips">
              <span class="chip">担当者退任</span>
              <span class="chip">稼働継続</span>
              <span class="chip">危険</span>
            </div>
            <div class="figure-row">
              <div class="person exit"></div>
              <div class="arrow-out">→</div>
              <div class="server"></div>
              <div class="screen"></div>
            </div>
            <div class="warning">!</div>
            <div class="bubble">サービスは残るのに、判断できる人だけが消えていく</div>
          </div>
        </div>
      </article>

      <article class="panel peach">
        <div class="panel-head">
          <div class="index">2</div>
          <h2>失われるもの</h2>
        </div>
        <div class="panel-body">
          <ul>
            <li>判断理由</li>
            <li>危険箇所の理解</li>
            <li>障害時の確認順</li>
            <li>例外条件</li>
          </ul>
          <div class="scene">
            <div class="chips">
              <span class="chip">資料散在</span>
              <span class="chip">新任者</span>
            </div>
            <div class="doc-stack">
              <div class="doc"></div>
              <div class="doc"></div>
              <div class="doc"></div>
            </div>
            <div class="question-card">なぜこの設計？<br>この設定の理由は？</div>
            <div class="bubble-row">
              <div class="person new"></div>
              <div class="bubble">見れば分かるはずの情報が、実際には判断文脈ごと抜け落ちる</div>
            </div>
          </div>
        </div>
      </article>

      <article class="panel mint">
        <div class="panel-head">
          <div class="index">3</div>
          <h2>AIを使う意味</h2>
        </div>
        <div class="panel-body">
          <ul>
            <li>自然言語で依頼できる</li>
            <li>AIが裏側の情報をたどる</li>
            <li>新任者の作業入口になる</li>
          </ul>
          <div class="scene">
            <div class="chips">
              <span class="chip">質問</span>
              <span class="chip">探索</span>
              <span class="chip">入口</span>
            </div>
            <div class="figure-row">
              <div class="person new"></div>
              <div class="connector"></div>
              <div class="ai">AI</div>
            </div>
            <div class="search-rail">
              <div class="search-item">設定情報</div>
              <div class="search-item">構成図</div>
              <div class="search-item">ログ</div>
            </div>
          </div>
        </div>
      </article>

      <article class="panel pink">
        <div class="panel-head">
          <div class="index">4</div>
          <h2>残すべき保守パッケージ</h2>
        </div>
        <div class="panel-body">
          <ul>
            <li>構成情報</li>
            <li>運用手順</li>
            <li>障害対応</li>
            <li>判断理由と未解決事項</li>
          </ul>
          <div class="scene">
            <div class="chips">
              <span class="chip">AI可読</span>
              <span class="chip">保守文脈</span>
            </div>
            <div class="box">
              <div class="box-title">保守パッケージ</div>
              <div class="package-tabs">
                <span class="tab blue">構成情報</span>
                <span class="tab mint">運用手順</span>
                <span class="tab peach">障害対応</span>
                <span class="tab pink">判断理由</span>
                <span class="tab blue">未解決事項</span>
              </div>
            </div>
            <div class="bubble">AIに渡すのは、作業そのものではなく、保守に必要な文脈</div>
          </div>
        </div>
      </article>
    </section>

    <div class="bottom-band">AIに渡すのは、作業そのものではなく、保守に必要な文脈。</div>
  </main>
</body>
</html>`;

await fs.mkdir(dir, { recursive: true });
await fs.writeFile(path.join(dir, "00_infographic.html"), html, "utf8");
console.log("rendered 00_infographic.html");
