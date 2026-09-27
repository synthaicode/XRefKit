"use strict";
const $ = id => document.getElementById(id);
$("pet-caption").textContent = "接続中";
window.addEventListener("error", event => {
  $("error").textContent = `画面の初期化に失敗しました：${event.message}`;
  $("error").hidden = false;
});
try { $("motion").checked = localStorage.getItem("attention-pet-motion") !== "off"; } catch {}
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
function setMotion() {
  document.body.dataset.motion = $("motion").checked ? "on" : "off";
  $("motion-status").textContent = !$("motion").checked ? "動き：オフ" : reducedMotion.matches ? "動き：停止中（端末の動きを減らす設定に従っています）" : "動き：オン";
  try { localStorage.setItem("attention-pet-motion", document.body.dataset.motion); } catch {}
}
$("motion").onchange = setMotion;
reducedMotion.addEventListener("change", setMotion);
setMotion();
let current = null, busy = false, polling = false, generation = 0;
let renderedSignature = "";
let lastObservedUserTurns = null, chatUpdateTimer = null;
let comparisonInitialized = false, comparisonOverridden = false;
const petExpressions = {Unknown:"unknown",Strained:"fit-strained",Balanced:"balanced",Relaxed:"relaxed",Review:"review"};
const modelNames = {luna:"Luna",terra:"Terra",sol:"Sol",astra:"Astra"};
const axisNames = {reasoning:"推論",constraint_tracking:"制約の保持",evidence_handling:"根拠の扱い"};
const behaviorNames = {exploration:"探索",dependency_expansion:"依存関係の展開",constraint_discovery:"制約の発見",uncertainty_discovery:"不確実性の発見",alternative_generation:"代替案の生成",compression:"圧縮"};
function applyPresentation(p) {
  $("dock").dataset.expression = petExpressions[p.petState];
  $("dock").dataset.trend = "unknown";
  $("state-title").textContent = p.headline;
  $("state-note").textContent = p.summary;
  $("panel-model-guide").textContent = p.modelGuide;
  $("model-guide-detail").textContent = p.modelGuideDetail;
  $("pet-caption").textContent = p.shortMessage;
  $("pet").setAttribute("aria-label", `Attention Pet：${p.shortMessage}。実験値・未校正`);
  $("symbol").textContent = "?";
  $("action-hint").textContent = p.actionHint;
  $("detail-reason").textContent = p.detailReason;
  $("model-fit").textContent = p.modelFitLabel;
  $("cost-fit").textContent = p.costFitLabel;
  $("fit-coverage").textContent = p.coverageLabel;
  $("fit-confidence").textContent = p.confidenceLabel;
}
function pendingFit(message) {
  renderedSignature = "";
  ["ral","expansion","effective","cost-fit","model-fit","fit-coverage","fit-confidence"].forEach(id => $(id).textContent = "—");
  $("cost-note").textContent = message;
  $("fit-reasons").replaceChildren();
  $("capability-rows").replaceChildren();
  $("candidate-rows").replaceChildren();
  $("behaviors").replaceChildren();
  $("depth-effects").textContent = "";
  ["causes","changes","observations","lower-cost-candidates"].forEach(id => $(id).replaceChildren());
  ["delta","coverage","sample-time"].forEach(id => $(id).textContent = "");
  $("trend-label").textContent = "評価待ち";
  $("trend-line").setAttribute("d", "");
  current = null;
  applyPresentation({petState:"Unknown",headline:message,shortMessage:message,
    summary:"新しい評価はまだ確認できていません。",scopeNote:"",confidenceNote:"評価待ち",
    actionHint:"接続と読み込みが完了してから確認してください。",detailReason:"",
    modelFitLabel:"—",costFitLabel:"—",coverageLabel:"—",confidenceLabel:"—",
    modelGuide:"",modelGuideShort:"",modelGuideDetail:"",modelGuideStatus:"Unknown"});
}
function storeProfile() {
  comparisonInitialized = comparisonOverridden = true;
  try {
    localStorage.setItem("attention-pet-comparison-model", $("model-profile").value);
    localStorage.setItem("attention-pet-comparison-effort", $("reasoning-effort").value);
  } catch {}
  generation += 1;
  renderedSignature = "";
  pendingFit("評価を更新中");
  refresh();
}
try {
  $("model-profile").value = localStorage.getItem("attention-pet-comparison-model") || "";
  $("reasoning-effort").value = localStorage.getItem("attention-pet-comparison-effort") || "standard";
  comparisonOverridden = Boolean($("model-profile").value);
} catch {}
if (!$("reasoning-effort").value) $("reasoning-effort").value = "standard";
$("model-profile").onchange = storeProfile;
$("reasoning-effort").onchange = storeProfile;
const names = {working_set:"覚えておく必要がある項目",dependency_complexity:"依存関係の複雑さ",constraint_density:"制約の結び付き",decision_depth:"判断の深さ",conflict_pressure:"矛盾・未解決事項",context_dispersion:"根拠の分散"};
const featureNames = {goal:"目的",constraint:"制約",decision:"判断",question:"未解決事項",exception:"例外",history:"探索履歴",conflict:"矛盾",active_items:"有効項目",dependency_edges:"依存関係",sources:"根拠の参照先",max_decision_depth:"最大判断深度",constraint_edges:"制約を含む依存関係"};
async function api(path, body) {
  path += `?${new URLSearchParams({model:$("model-profile").value,reasoning:$("reasoning-effort").value})}`;
  if (body) pendingFit("評価を更新中");
  const response = await fetch(path, {signal:AbortSignal.timeout(5000), method: body ? "POST" : "GET", headers: body ? {"Content-Type":"application/json"} : {}, ...(body ? {body:JSON.stringify(body)} : {})});
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || "読み込みに失敗しました");
  return value;
}
function error(err) { $("error").textContent = err.message; $("error").hidden = false; pendingFit("評価を取得できません"); }
async function perform(callback) {
  if (busy) return;
  generation += 1;
  busy = true; $("error").hidden = true;
  $("model-profile").disabled = $("reasoning-effort").disabled = true;
  try { await callback(); } catch (err) { error(err); } finally {
    busy = false; $("model-profile").disabled = $("reasoning-effort").disabled = false;
  }
}
function list(id, entries) {
  $(id).replaceChildren(...(entries.length ? entries : ["該当する観測はありません"]).map(text => { const li = document.createElement("li"); li.textContent = text; return li; }));
}
function tableRows(id, rows) {
  $(id).replaceChildren(...rows.map(values => {
    const row = document.createElement("tr");
    values.forEach(value => {const cell = document.createElement("td");cell.textContent = value;row.append(cell);});
    return row;
  }));
}
function renderFit(fit) {
  if (!fit) throw new Error("評価情報がありません。Petサーバーの更新を確認してください。");
  applyPresentation(fit.presentation);
  $("cost-note").textContent = fit.selected ? `現在：${modelNames[fit.selected.model]} / ${fit.selected.reasoning}、相対推論コスト：${fit.inferenceCostIndex}（仮の比較指数）。再試行・修正・失敗損失を含む総コストは未推定です。` : "総コストは未推定です。";
  $("expansion").textContent = fit.selected ? `+${fit.selected.expansion}` : "—";
  $("effective").textContent = fit.selected?.effectiveRal ?? "—";
  list("fit-reasons", fit.reasons);
  list("lower-cost-candidates", fit.lowerCostCandidates.length ? fit.lowerCostCandidates.map(c => `${modelNames[c.model]} / ${c.reasoning}：仮の必要能力3軸を満たす試算、相対推論コスト ${c.relativeInferenceCost}`) : ["現在の比較で該当候補なし（未判定の場合も含む）"]);
  tableRows("capability-rows", fit.selected ? Object.entries(axisNames).map(([key,label]) => [label,fit.selected.requiredCapability[key],fit.selected.capability[key]]) : []);
  tableRows("candidate-rows", fit.alternatives.map(c => [modelNames[c.model],c.effectiveRal,c.meetsRequirements ? "満たす試算" : "不足の試算",c.relativeInferenceCost]));
  list("behaviors", fit.profile ? Object.entries(behaviorNames).map(([key,label]) => `${label}：${fit.profile.behavior[key]}`) : []);
  $("depth-effects").textContent = fit.depth ? `考える深さの仮補正：能力 ${fit.depth.capability_modifier >= 0 ? "+" : ""}${fit.depth.capability_modifier}、探索 ×${fit.depth.exploration_modifier}、相対推論コスト ×${fit.depth.cost_modifier}` : "";
}
function renderSource(source) {
  const live = source?.mode === "codex-chat";
  if (live) {
    const count = source.observedUserTurns;
    if (lastObservedUserTurns !== null && count > lastObservedUserTurns) {
      clearTimeout(chatUpdateTimer);
      $("dock").dataset.chatUpdate = "on";
      chatUpdateTimer = setTimeout(() => { $("dock").dataset.chatUpdate = "off"; }, 650);
    }
    lastObservedUserTurns = count;
  } else lastObservedUserTurns = null;
  $("source-detail").textContent = live
    ? "この評価は、会話中の発言数や修正指示などから作った試算です。作業の依存関係や実際の成否は未確認です。"
    : "手動で読み込んだ作業内容を評価しています。";
  $("source-model").textContent = live
    ? `Codex model: ${source.model || "不明"} / ${source.effort || "不明"}\nDefault evaluation profile: ${source.profile ? `${modelNames[source.profile]} / ${source.reasoning}` : "未対応"}`
    : "";
  if (live && !comparisonInitialized) {
    if (!comparisonOverridden) {
      $("model-profile").value = source.profile || "";
      $("reasoning-effort").value = source.reasoning;
    }
    comparisonInitialized = true;
  }
  if (live) {
    $("model-help").textContent = "現在の実行設定を初期値にしています。ここで条件を変えてもCodexのモデルや考える深さは切り替わりません。";
  }
  $("model-profile").disabled = $("reasoning-effort").disabled = false;
}
function render(value) {
  current = value;
  renderSource(value.source);
  const s = value.state;
  const signature = `${s?.taskId}/${s?.observedAt}/${value.recoveries.length}/${$("model-profile").value}/${$("reasoning-effort").value}/${JSON.stringify(value.fit?.presentation)}`;
  if (signature === renderedSignature) return;
  renderFit(value.fit);
  renderedSignature = signature;
  if (!s) {
    $("ral").textContent = "—"; $("delta").textContent = "";
    $("actions").replaceChildren(); $("trend-line").setAttribute("d", ""); return;
  }
  $("ral").textContent = s.ral;
  $("delta").textContent = `元の複雑さの前回との差：${s.deltaRal === null ? "比較なし" : `${s.deltaRal > 0 ? "+" : ""}${s.deltaRal}`}`;
  $("trend-label").textContent = `${s.trend === "rapid_rise" ? "急な増加 · " : ""}Base RALの履歴（直近${value.history.length}件）`;
  const points = value.history.slice(-20);
  $("trend-line").setAttribute("d", points.map((p,i) => `${i ? "L" : "M"}${5 + i * 290 / Math.max(1,points.length - 1)},${50 - p.ral * .45}`).join(" "));
  list("causes", Object.entries(names).map(([key,label]) => `${label}：${(s.causes.find(c => c.type === key)?.points ?? 0).toFixed(1)} / ${s.weights[key]}点`));
  list("changes", s.changes.map(c => `${c.delta > 0 ? "+" : ""}${c.delta} ${featureNames[c.feature]}`));
  list("observations", s.trajectoryEvidence.map(o => `${o.kind} — ${o.evidence}`));
  $("coverage").textContent = `入力範囲：${s.coverage} · ${s.evaluatorVersion} · ${s.state} · trajectoryStability: ${s.trajectoryStability ?? "unknown"}`;
  $("sample-time").textContent = `観測時刻：${new Date(s.observedAt * 1000).toLocaleString()}`;
}
async function refresh() {
  if (busy || polling) return;
  polling = true;
  const startedGeneration = generation;
  try { const value = await api("/api/state"); if (!busy && generation === startedGeneration) { $("error").hidden = true; render(value); } }
  catch (err) { if (!busy && generation === startedGeneration) error(err); }
  finally { polling = false; }
}
pendingFit("評価を読み込み中");
refresh();
setInterval(refresh, 3000);
