"use strict";
const $ = id => document.getElementById(id);
const preferredLanguages = typeof navigator === "undefined" ? ["ja"] : (navigator.languages?.length ? navigator.languages : [navigator.language]);
const locale = preferredLanguages.find(language => /^ja\b/i.test(language) || /^en\b/i.test(language));
const lang = locale && /^ja\b/i.test(locale) ? "ja" : "en";
const text = {
  ja:{connecting:"接続中",initFailed:"画面の初期化に失敗しました",motionOff:"動き：オフ",motionReduced:"動き：停止中（端末の動きを減らす設定に従っています）",motionOn:"動き：オン",pendingSummary:"新しい評価はまだ確認できていません。",pendingConfidence:"評価待ち",pendingAction:"接続と読み込みが完了してから確認してください。",updating:"評価を更新中",loadFailed:"読み込みに失敗しました",evaluationFailed:"評価を取得できません",noObservation:"該当する観測はありません",missingFit:"評価情報がありません。Petサーバーの更新を確認してください。",totalUnknown:"総コストは未推定です。",noCandidate:"現在の比較で該当候補なし（未判定の場合も含む）",meets:"満たす試算",shortfall:"不足の試算",waitingClient:"クライアントからのセッション通知を待っています。",clientSource:"この評価は、クライアントが送った構造化情報から作った試算です。評価範囲は、クライアントが確認して送信できた情報に限られます。",chatSource:"この評価は、会話中の発言数や修正指示などから作った試算です。作業の依存関係や実際の成否は未確認です。",manualSource:"手動で読み込んだ作業内容を評価しています。",unknown:"不明",unsupported:"未対応",liveHelp:"通常はアクティブなチャットの実行条件に追従します。手動の比較条件は試算だけに反映され、クライアントのモデルや考える深さは切り替わりません。",noComparison:"比較なし",rapidRise:"急な増加 · ",history:"Base RALの履歴",inputRange:"入力範囲",observedAt:"観測時刻",points:"点"},
  en:{connecting:"Connecting",initFailed:"The screen could not be initialized",motionOff:"Motion: off",motionReduced:"Motion: paused by your device's reduced-motion setting",motionOn:"Motion: on",pendingSummary:"A new evaluation is not available yet.",pendingConfidence:"Waiting for evaluation",pendingAction:"Check again after the connection and loading complete.",updating:"Updating evaluation",loadFailed:"Loading failed",evaluationFailed:"Could not retrieve the evaluation",noObservation:"No applicable observations",missingFit:"Evaluation data is missing. Check the Pet server update.",totalUnknown:"Total cost has not been estimated.",noCandidate:"No matching candidate in the current comparison (including undetermined cases)",meets:"Estimated to meet",shortfall:"Estimated shortfall",waitingClient:"Waiting for the client to identify the active session.",clientSource:"This estimate uses structured information supplied by the client. Its scope is limited to information the client could confirm and send.",chatSource:"This estimate uses message counts and correction signals from the conversation. Work dependencies and actual outcomes are unverified.",manualSource:"Evaluating manually loaded work information.",unknown:"Unknown",unsupported:"Unsupported",liveHelp:"By default, the estimate follows the active chat's execution profile. Manual comparison settings affect only the estimate, not the client's model or reasoning depth.",noComparison:"No comparison",rapidRise:"Rapid rise · ",history:"Base RAL history",inputRange:"Input scope",observedAt:"Observed",points:"points"}
};
const t = key => text[lang][key];
if (lang === "en") {
  const staticEn = {panelAria:"Execution profile fit",eyebrow:"Profile and cost allocation",waiting:"Waiting for observations",loadWork:"Load work information to begin.",checkingChat:"Checking the connected chat",calibration:"Experimental and uncalibrated — not measured capability or price",modelFit:"Capability fit / Profile Fit",costFit:"Cost comparison / Cost Fit",coverage:"Input scope / Coverage",confidence:"Evaluation confidence / Confidence",undetermined:"Not determined",noInput:"No input",confidenceUnknown:"Not evaluated / Unknown",settingsAria:"Execution profile settings",estimateModel:"Model to estimate",chooseModel:"Select a model",lunaProfile:"Luna (experimental profile)",terraProfile:"Terra (experimental profile)",solProfile:"Sol (experimental profile)",astraProfile:"Astra (experimental profile)",estimateDepth:"Reasoning depth to estimate",light:"Light",standard:"Standard",high:"Deep",modelHelp:"By default, the estimate follows the active chat's execution profile. Manual comparison settings affect only the estimate, not the Codex model or reasoning depth. Model generations and pricing plans are not included.",showEvaluation:"Show values, candidates, and reasons",baseRal:"Base complexity<br>Base RAL",workExpansion:"Estimated work expansion",effectiveRal:"Expanded complexity",expansionDisclaimer:"Work expansion is a hypothesis. It does not mean that actual items or dependencies increased.",why:"Why this evaluation was produced",costComparison:"Inference-cost comparison",lowerCandidates:"Lower inference-cost fit candidates",costDisclaimer:"Total cost = inference + retries + corrections + waiting time + failure losses. Amounts, counts, and success probabilities are not estimated. Lower inference cost does not establish equal quality or lower total cost. No candidate also does not establish that the current profile has better quality or total cost.",showCapabilities:"Show required capability and comparison candidates",capabilityItem:"Capability",requiredEstimated:"Required (estimated)",selectedEstimated:"Selected profile (estimated)",sameDepth:"Compares compatible model and reasoning combinations, including each candidate's estimated work expansion.",candidate:"Candidate",expanded:"Expanded",requiredCapability:"Requirement",relativeCost:"Relative inference cost",behaviorHypothesis:"Selected model behavior (hypothesis, 0–1)",changeHistory:"Change history",loadChange:"Workload change",animatePet:"Animate the pet",showRal:"Show RAL breakdown and evidence",sixContributions:"All six contributions / maximum",changesSincePrevious:"Changes since previous",outcomeRecords:"Outcome records",loadingEvaluation:"Loading evaluation",petLoading:"Attention Pet: loading evaluation"};
  document.documentElement.lang = "en";
  document.title = "Attention Pet · Work outlook";
  document.querySelectorAll("[data-i18n]").forEach(node => { node.innerHTML = staticEn[node.dataset.i18n]; });
  document.querySelectorAll("[data-i18n-aria]").forEach(node => { node.setAttribute("aria-label", staticEn[node.dataset.i18nAria]); });
}
$("pet-caption").textContent = t("connecting");
window.addEventListener("error", event => {
  $("error").textContent = `${t("initFailed")}: ${event.message}`;
  $("error").hidden = false;
});
try { $("motion").checked = localStorage.getItem("attention-pet-motion") !== "off"; } catch {}
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
function setMotion() {
  document.body.dataset.motion = $("motion").checked ? "on" : "off";
  $("motion-status").textContent = !$("motion").checked ? t("motionOff") : reducedMotion.matches ? t("motionReduced") : t("motionOn");
  try { localStorage.setItem("attention-pet-motion", document.body.dataset.motion); } catch {}
}
$("motion").onchange = setMotion;
reducedMotion.addEventListener("change", setMotion);
setMotion();
let current = null, busy = false, polling = false, generation = 0;
let renderedSignature = "";
let lastObservedUserTurns = null, chatUpdateTimer = null;
let comparisonOverridden = false;
let supportedProfiles = null;
function syncReasoningOptions(coerce = false) {
  if (!supportedProfiles || !$("reasoning-effort").options) return;
  const entry = supportedProfiles.find(profile => profile.id === $("model-profile").value);
  for (const option of $("reasoning-effort").options) option.disabled = Boolean(entry && !entry.reasoning.includes(option.value));
  if (coerce && entry && !entry.reasoning.includes($("reasoning-effort").value)) $("reasoning-effort").value = entry.reasoning[0];
}
async function loadProfiles() {
  try {
    const response = await fetch("/api/profiles", {signal:AbortSignal.timeout(5000)});
    if (!response.ok) return;
    const value = await response.json();
    if (Array.isArray(value.models)) {
      supportedProfiles = value.models;
      const selected = $("model-profile").value;
      const choose = document.createElement("option");
      choose.value = "";
      choose.textContent = lang === "ja" ? "モデルを選ぶ" : "Select a model";
      const options = value.models.map(profile => {
        modelNames[profile.id] = profile.label;
        const option = document.createElement("option");
        option.value = profile.id;
        option.textContent = `${profile.label}${lang === "ja" ? "（実験プロファイル）" : " (experimental profile)"}`;
        return option;
      });
      $("model-profile").replaceChildren(choose, ...options);
      $("model-profile").value = selected;
      const selectedEffort = $("reasoning-effort").value;
      const levels = [...new Set(value.models.flatMap(profile => profile.reasoning))];
      $("reasoning-effort").replaceChildren(...levels.map(level => {
        const option = document.createElement("option");
        option.value = option.textContent = level;
        return option;
      }));
      $("reasoning-effort").value = selectedEffort;
      syncReasoningOptions();
    }
  } catch { /* The current evaluation remains usable without profile metadata. */ }
}
const petExpressions = {Unknown:"unknown",Strained:"fit-strained",Balanced:"balanced",Relaxed:"relaxed",Review:"review"};
const modelNames = {luna:"Luna",terra:"Terra",sol:"Sol",astra:"Astra"};
const axisNames = lang === "ja" ? {reasoning:"推論",constraint_tracking:"制約の保持",evidence_handling:"根拠の扱い"} : {reasoning:"Reasoning",constraint_tracking:"Constraint tracking",evidence_handling:"Evidence handling"};
const behaviorNames = lang === "ja" ? {exploration:"探索",dependency_expansion:"依存関係の展開",constraint_discovery:"制約の発見",uncertainty_discovery:"不確実性の発見",alternative_generation:"代替案の生成",compression:"圧縮"} : {exploration:"Exploration",dependency_expansion:"Dependency expansion",constraint_discovery:"Constraint discovery",uncertainty_discovery:"Uncertainty discovery",alternative_generation:"Alternative generation",compression:"Compression"};
function applyPresentation(p) {
  $("dock").dataset.expression = petExpressions[p.petState];
  $("dock").dataset.trend = "unknown";
  $("state-title").textContent = p.headline;
  $("state-note").textContent = p.summary;
  $("panel-model-guide").textContent = p.modelGuide;
  $("model-guide-detail").textContent = p.modelGuideDetail;
  $("pet-caption").textContent = p.shortMessage;
  $("pet-model-guide").textContent = p.modelGuideShort;
  $("pet-model-guide").hidden = !p.modelGuideShort;
  $("pet").setAttribute("aria-label", lang === "ja" ? `Attention Pet：${p.shortMessage}。実験値・未校正` : `Attention Pet: ${p.shortMessage}. Experimental and uncalibrated`);
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
  $("trend-label").textContent = t("pendingConfidence");
  $("trend-line").setAttribute("d", "");
  current = null;
  applyPresentation({petState:"Unknown",headline:message,shortMessage:message,
    summary:t("pendingSummary"),scopeNote:"",confidenceNote:t("pendingConfidence"),
    actionHint:t("pendingAction"),detailReason:"",
    modelFitLabel:"—",costFitLabel:"—",coverageLabel:"—",confidenceLabel:"—",
    modelGuide:"",modelGuideShort:"",modelGuideDetail:"",modelGuideStatus:"Unknown"});
}
function storeProfile() {
  syncReasoningOptions(true);
  comparisonOverridden = Boolean($("model-profile").value);
  try {
    localStorage.setItem("attention-pet-comparison-model", $("model-profile").value);
    localStorage.setItem("attention-pet-comparison-effort", $("reasoning-effort").value);
  } catch {}
  generation += 1;
  renderedSignature = "";
  pendingFit(t("updating"));
  refresh();
}
try {
  $("model-profile").value = localStorage.getItem("attention-pet-comparison-model") || "";
  const savedEffort = localStorage.getItem("attention-pet-comparison-effort") || "medium";
  $("reasoning-effort").value = ({light:"low",standard:"medium"})[savedEffort] || savedEffort;
  comparisonOverridden = Boolean($("model-profile").value);
} catch {}
if (!$("reasoning-effort").value) $("reasoning-effort").value = "medium";
$("model-profile").onchange = storeProfile;
$("reasoning-effort").onchange = storeProfile;
const names = lang === "ja" ? {working_set:"覚えておく必要がある項目",dependency_complexity:"依存関係の複雑さ",constraint_density:"制約の結び付き",decision_depth:"判断の深さ",conflict_pressure:"矛盾・未解決事項",context_dispersion:"根拠の分散"} : {working_set:"Items to retain",dependency_complexity:"Dependency complexity",constraint_density:"Constraint density",decision_depth:"Decision depth",conflict_pressure:"Conflicts and unresolved items",context_dispersion:"Evidence dispersion"};
const featureNames = lang === "ja" ? {goal:"目的",constraint:"制約",decision:"判断",question:"未解決事項",exception:"例外",history:"探索履歴",conflict:"矛盾",active_items:"有効項目",dependency_edges:"依存関係",sources:"根拠の参照先",max_decision_depth:"最大判断深度",constraint_edges:"制約を含む依存関係"} : {goal:"Goal",constraint:"Constraint",decision:"Decision",question:"Unresolved item",exception:"Exception",history:"Exploration history",conflict:"Conflict",active_items:"Active items",dependency_edges:"Dependencies",sources:"Evidence sources",max_decision_depth:"Maximum decision depth",constraint_edges:"Dependencies with constraints"};
async function api(path, body) {
  path += `?${new URLSearchParams({model:comparisonOverridden ? $("model-profile").value : "",reasoning:$("reasoning-effort").value,lang})}`;
  if (body) pendingFit(t("updating"));
  const response = await fetch(path, {signal:AbortSignal.timeout(5000), method: body ? "POST" : "GET", headers: body ? {"Content-Type":"application/json"} : {}, ...(body ? {body:JSON.stringify(body)} : {})});
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || t("loadFailed"));
  return value;
}
function error(err) { $("error").textContent = err.message; $("error").hidden = false; pendingFit(t("evaluationFailed")); }
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
  $(id).replaceChildren(...(entries.length ? entries : [t("noObservation")]).map(text => { const li = document.createElement("li"); li.textContent = text; return li; }));
}
function tableRows(id, rows) {
  $(id).replaceChildren(...rows.map(values => {
    const row = document.createElement("tr");
    values.forEach(value => {const cell = document.createElement("td");cell.textContent = value;row.append(cell);});
    return row;
  }));
}
function renderFit(fit) {
  if (!fit) throw new Error(t("missingFit"));
  applyPresentation(fit.presentation);
  $("cost-note").textContent = fit.selected ? (lang === "ja" ? `現在：${modelNames[fit.selected.model]} / ${fit.selected.reasoning}、相対推論コスト：${fit.inferenceCostIndex}（仮の比較指数）。再試行・修正・待ち時間・失敗損失を含む総コストは未推定です。` : `Current: ${modelNames[fit.selected.model]} / ${fit.selected.reasoning}; relative inference cost: ${fit.inferenceCostIndex} (experimental comparison index). Total cost including retries, corrections, waiting time, and failure losses is not estimated.`) : t("totalUnknown");
  $("expansion").textContent = fit.selected ? `+${fit.selected.expansion}` : "—";
  $("effective").textContent = fit.selected?.effectiveRal ?? "—";
  list("fit-reasons", fit.reasons);
  list("lower-cost-candidates", fit.lowerCostCandidates.length ? fit.lowerCostCandidates.map(c => lang === "ja" ? `${modelNames[c.model]} / ${c.reasoning}：仮の必要能力3軸を満たす試算、相対推論コスト ${c.relativeInferenceCost}` : `${modelNames[c.model]} / ${c.reasoning}: estimated to meet all three requirements; relative inference cost ${c.relativeInferenceCost}`) : [t("noCandidate")]);
  tableRows("capability-rows", fit.selected ? Object.entries(axisNames).map(([key,label]) => [label,fit.selected.requiredCapability[key],fit.selected.capability[key]]) : []);
  tableRows("candidate-rows", fit.alternatives.map(c => [`${modelNames[c.model]} / ${c.reasoning}`,c.effectiveRal,c.meetsRequirements ? t("meets") : t("shortfall"),c.relativeInferenceCost]));
  list("behaviors", fit.profile ? Object.entries(behaviorNames).map(([key,label]) => `${label}：${fit.profile.behavior[key]}`) : []);
  $("depth-effects").textContent = fit.depth ? (lang === "ja" ? `考える深さの仮補正：能力 ${fit.depth.capability_modifier >= 0 ? "+" : ""}${fit.depth.capability_modifier}、探索 ×${fit.depth.exploration_modifier}、相対推論コスト ×${fit.depth.cost_modifier}` : `Estimated reasoning-depth adjustment: capability ${fit.depth.capability_modifier >= 0 ? "+" : ""}${fit.depth.capability_modifier}; exploration ×${fit.depth.exploration_modifier}; relative inference cost ×${fit.depth.cost_modifier}`) : "";
}
function renderSource(source) {
  const clientState = source?.mode === "client-state";
  const live = source?.mode === "codex-chat" || (clientState && source.connected);
  if (live) {
    const count = source.observedUserTurns ?? source.activationRevision;
    if (lastObservedUserTurns !== null && count > lastObservedUserTurns) {
      clearTimeout(chatUpdateTimer);
      $("dock").dataset.chatUpdate = "on";
      chatUpdateTimer = setTimeout(() => { $("dock").dataset.chatUpdate = "off"; }, 650);
    }
    lastObservedUserTurns = count;
  } else lastObservedUserTurns = null;
  $("source-detail").textContent = clientState && !source.connected
    ? t("waitingClient")
    : clientState
      ? t("clientSource")
      : live
        ? t("chatSource")
        : t("manualSource");
  $("source-model").textContent = live
    ? `${clientState ? `Client: ${source.provider}` : "Codex"} model: ${source.model || t("unknown")} / ${source.effort || t("unknown")}\nDefault evaluation profile: ${source.profile ? `${modelNames[source.profile]} / ${source.reasoning}` : t("unsupported")}`
    : "";
  if (live && !comparisonOverridden) {
    $("model-profile").value = source.profile || "";
    $("reasoning-effort").value = source.reasoning;
    syncReasoningOptions();
  }
  if (live) {
    $("model-help").textContent = t("liveHelp");
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
  $("delta").textContent = lang === "ja" ? `元の複雑さの前回との差：${s.deltaRal === null ? t("noComparison") : `${s.deltaRal > 0 ? "+" : ""}${s.deltaRal}`}` : `Change in base complexity since previous: ${s.deltaRal === null ? t("noComparison") : `${s.deltaRal > 0 ? "+" : ""}${s.deltaRal}`}`;
  $("trend-label").textContent = `${s.trend === "rapid_rise" ? t("rapidRise") : ""}${t("history")} (${lang === "ja" ? `直近${value.history.length}件` : `latest ${value.history.length}`})`;
  const points = value.history.slice(-20);
  $("trend-line").setAttribute("d", points.map((p,i) => `${i ? "L" : "M"}${5 + i * 290 / Math.max(1,points.length - 1)},${50 - p.ral * .45}`).join(" "));
  list("causes", Object.entries(names).map(([key,label]) => `${label}: ${(s.causes.find(c => c.type === key)?.points ?? 0).toFixed(1)} / ${s.weights[key]} ${t("points")}`));
  list("changes", s.changes.map(c => `${c.delta > 0 ? "+" : ""}${c.delta} ${featureNames[c.feature]}`));
  list("observations", s.trajectoryEvidence.map(o => `${o.kind} — ${o.evidence}`));
  $("coverage").textContent = `${t("inputRange")}: ${s.coverage} · ${s.evaluatorVersion} · ${s.state} · trajectoryStability: ${s.trajectoryStability ?? "unknown"}`;
  $("sample-time").textContent = `${t("observedAt")}: ${new Date(s.observedAt * 1000).toLocaleString(lang === "ja" ? "ja-JP" : "en")}`;
}
async function refresh() {
  if (busy || polling) return;
  polling = true;
  const startedGeneration = generation;
  try { const value = await api("/api/state"); if (!busy && generation === startedGeneration) { $("error").hidden = true; render(value); } }
  catch (err) { if (!busy && generation === startedGeneration) error(err); }
  finally { polling = false; }
}
pendingFit(lang === "ja" ? "評価を読み込み中" : "Loading evaluation");
loadProfiles();
refresh();
setInterval(refresh, 3000);
