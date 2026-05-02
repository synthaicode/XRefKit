import fs from "node:fs/promises";
import path from "node:path";

const dir = path.resolve("ja/docs/assets/xrefkit_repository_snapshot");
const css = await fs.readFile(path.join(dir, "diagram.css"), "utf8");

const html = `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>XRefKit Repository Snapshot JA</title>
  <style>${css}</style>
</head>
<body>
  <main class="canvas">
    <header class="header">
      <div>
        <h1>AI による作業を制御可能にする運用基盤。</h1>
        <p class="subtitle">現在のリポジトリ像: Skillを用いる作業では、開始時に実行ログを作成し、作業項目と証跡を残す。実行とチェックを分離し、自動ゲートを通過したものだけを完了とする。</p>
        <div class="snapshot">Repository snapshot: 2026-04-29</div>
      </div>
      <div class="brand">XRefKit</div>
    </header>

    <section class="main-grid">
      <section class="panel assets">
        <div class="panel-title">制御資産</div>
        <div class="panel-body">
          <div class="asset-list">
            <div class="asset"><div class="ico">F</div><div><strong>Flow</strong><span>作業の順序と判断の流れ</span></div></div>
            <div class="asset"><div class="ico">C</div><div><strong>Capability</strong><span>実行できる作業単位</span></div></div>
            <div class="asset"><div class="ico">S</div><div><strong>Skill</strong><span>作業手順と運用契約</span></div></div>
            <div class="asset"><div class="ico">K</div><div><strong>Knowledge</strong><span>参照すべき知識とルール</span></div></div>
            <div class="asset"><div class="ico">LOG</div><div><strong>Session</strong><span>実行状態と証跡の記録</span></div></div>
            <div class="asset"><div class="ico">XID</div><div><strong>安定参照</strong><span>文書や成果物を結ぶ固定参照</span></div></div>
          </div>
          <div class="memory-box">
            <div class="no-memory"></div>
            <h2>記憶に頼らない</h2>
            <p>作業開始時に、現在の方針、Skill の定義、知識、証跡、引き継ぎ元を読み込んでから進める。</p>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-title">Skill 実行基盤の流れ</div>
        <div class="panel-body pipeline">
          <div class="steps">
            <div class="step"><div class="ico">RUN</div><div><h3>開始ゲート</h3><p><code>fm skill run</code> がメタ情報を検査し、Skill を開く前に実行ログを作る。</p></div></div>
            <div class="flow-down">v</div>
            <div class="step"><div class="ico">WI</div><div><h3>作業リスト</h3><p>タスク固有の作業項目を追加し、完了またはエスカレーションまで追跡する。</p></div></div>
            <div class="flow-down">v</div>
            <div class="step"><div class="ico">R</div><div><h3>役割分担</h3><p>実行、チェック、引き継ぎの担当を分け、状態更新時に確認する。</p></div></div>
            <div class="flow-down">v</div>
            <div class="step"><div class="ico">ART</div><div><h3>成果物と証跡</h3><p>成果物と証跡リンクを必須にし、確認結果、判断、引き継ぎも明示する。</p></div></div>
            <div class="flow-down">v</div>
            <div class="step"><div class="ico">C</div><div><h3>不明点とリスク</h3><p>不明点、リスク、非自明な判断を本文に埋めず、完了条件として扱う。</p></div></div>
            <div class="flow-down">v</div>
            <div class="step"><div class="ico">QG</div><div><h3>完了と監査</h3><p><code>fm skill close</code> と品質ゲートが、不完全な実行ログを拒否する。</p></div></div>
          </div>
          <aside class="side-rule">
            <h3>完了できない条件</h3>
            <div class="rule-card">実行・確認・引き継ぎが未完了</div>
            <div class="rule-card">作業項目・成果物が不足</div>
            <div class="rule-card">不明点やリスクが残る</div>
            <div class="stop">STOP</div>
            <p class="small">判断は証跡に紐づけてから完了とする。</p>
          </aside>
          <div class="ai-first">
            <p><strong>先に AI 同士で検証する</strong></p>
            <p><strong>引き継ぎ元の完了を確認する</strong></p>
          </div>
        </div>
      </section>

      <section class="panel guard">
        <div class="panel-title">起動時の入力制御ガード</div>
        <div class="panel-body">
          <div class="guard-stack">
            <div class="direction">
              <div class="guard-item">起動方針</div>
              <div class="down">v</div>
              <div class="guard-item">Skill 定義 + 運用契約</div>
              <div class="down">v</div>
              <div class="guard-item">実行ログ</div>
              <div class="down">v</div>
              <div class="guard-item">外部からの依頼</div>
              <div class="down">v</div>
              <div class="guard-item">監査可能な出力</div>
            </div>
            <div>
              <div class="shield">OK</div>
              <div class="guard-copy">外部入力は上位定義を上書きできない</div>
            </div>
          </div>
          <div class="blocked">
            <p><strong>Blocked:</strong> 外部入力は、既定の flow、capability、Skill 手順、範囲、権限、エスカレーション経路を書き換えられない。</p>
            <p><strong>引き継ぎ元:</strong> 受け取る側は、元の実行ログが完了済みであることを確認してから文脈として使う。</p>
          </div>
        </div>
      </section>

      <section class="panel human">
        <div class="panel-title">人間との責任境界と成熟度</div>
        <div class="panel-body">
          <div class="human-flow">
            <div class="human-card"><div class="ico">DR</div><div><h3>Draft</h3><p>仮説段階の記録。人間との責任境界が見えるまでは運用に適用しない。</p></div></div>
            <div class="human-card"><div class="ico">TR</div><div><h3>Trial</h3><p>実行しながら観察し、弱い境界や曖昧な判断点を見つける。</p></div></div>
            <div class="human-card"><div class="ico">ST</div><div><h3>Stable</h3><p>実行ログ、ガード、参照、引き継ぎ条件が明示されている。</p></div></div>
            <div class="human-card"><div class="ico">GV</div><div><h3>Governed</h3><p>安定したSkillに、統制上の根拠と監査可能な責任境界が加わっている。</p></div></div>
            <div class="bracket">判断のトレードオフは人間に戻す</div>
            <div class="human-card"><div class="ico">H</div><div><h3>人間の判断</h3><p>リスク受容、範囲変更、優先度、業務上のトレードオフを人間が決める。</p></div></div>
            <div class="human-card"><div class="ico">A</div><div><h3>監査証跡</h3><p>判断、証跡、確認結果、懸念、承認、引き継ぎをログに残す。</p></div></div>
          </div>
        </div>
      </section>
    </section>

    <section class="xid-band">
      <div class="band-cell"><div class="ico">XID</div><p class="small"><strong>安定した参照点</strong><br>文書、方針、Skill、情報源、成果物を結ぶ。</p></div>
      <div class="band-cell"><div class="ico">LOG</div><p class="small"><strong>セッション記録</strong><br>実行状態、役割ごとの作業、完了イベントを残す。</p></div>
      <div class="band-center"><h2>実行証跡レイヤー</h2><p>Skill、成果物、確認結果、懸念、引き継ぎを横断して追跡する土台</p></div>
      <div class="band-cell"><div class="ico">JDG</div><p class="small"><strong>判断記録</strong><br>非自明な判断と人間向けの判断材料を記録する。</p></div>
      <div class="band-cell"><div class="ico">CI</div><p class="small"><strong>品質監査</strong><br>統制外のログと未完了のSkill実行を検出する。</p></div>
    </section>

  </main>
</body>
</html>`;

await fs.writeFile(path.join(dir, "xrefkit_repository_snapshot.html"), html, "utf8");
