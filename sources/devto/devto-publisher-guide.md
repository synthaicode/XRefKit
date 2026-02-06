# Dev.to Publisher Guide

Dev.to読者の行動モデルと実データに基づく記事最適化ガイド。

**検証済み**: Dev.to年間トップ記事（1788〜277 reactions）で80%以上のルール適合率を確認。

---

## 前提：読者行動モデル

### トラフィック構造（実データ）
- **外部流入が67%**（SNS、検索、アグリゲーター等）
- Dev.to内部フィード経由は33%のみ
- つまり大半の読者は「外部で見かけたタイトル」で記事を選ぶ

### 読者の行動
- 読者は常連ではなく、流入と離脱を繰り返す
- 訪問時に「たまたま自分に近いタイトル」から記事を選択
- トレンドに乗ったタイトルと角度が重要

### 外部流入の主要ソース
1. SNS（Twitter/X, LinkedIn）
2. Google検索
3. アグリゲーター（daily.dev等）
4. ダークソーシャル（Slack, Discord）

### 年間トップ記事（検証データ）
| タイトル | Reactions | 成功要因 |
|----------|-----------|----------|
| How to Use DeepSeek R1 **for Free** in VS Code | 1788 | 無料 + 具体ツール |
| 11 Practical Ways to Bring Side Income 💰 | 1506 | 数字 + 実用的価値 |
| 30+ MCP Ideas with Complete Source Code | 768 | 数字 + 完全性 |
| Agents 101: Build your first AI Agent in **30 minutes** | 682 | 時間制限 + 初心者向け |
| Every Developer **Needs** to Self-Host | 589 | 強調語 + 命令形 |

---

## ワークフロー

### Step 1: トレンド調査

web_searchで現在のトレンドを調査：

```
Dev.to内：
- "site:dev.to [メイントピック] 2025"
- "dev.to trending [関連キーワード]"

外部トレンド（外部流入対策）：
- Twitter/X: "[技術名] site:x.com"
- Hacker News: "[トピック] site:news.ycombinator.com"
- Google: "[技術名] best practices 2025"
```

調査ポイント：現在のキーワード、切り口、タイトルパターン

### Step 2: タイトル最適化

元の記事内容を維持しつつ、タイトル案を3-5個提案：
- トレンドキーワードとの接点
- 読者の「自分ごと化」しやすさ
- 具体的な価値の明示

### Step 3: 内容角度の調整

| 角度タイプ | 説明 | 例 |
|-----------|------|-----|
| Problem-First | 課題から入る | "Why your X isn't working" |
| Result-First | 成果から入る | "How I achieved X" |
| Comparison | 比較形式 | "X vs Y: Which is better" |
| Tutorial | 手順形式 | "Step-by-step guide to X" |
| Opinion | 主張形式 | "You don't need X" |
| Story | 体験談形式 | "What I learned from X" |

### Step 4: 出力

```markdown
## トレンド分析結果
[調査で見つけたトレンドキーワード・パターン]

## タイトル提案
1. [タイトル案1] - [選択理由]
2. [タイトル案2] - [選択理由]
3. [タイトル案3] - [選択理由]

## 推奨角度
[角度タイプ]: [推奨理由]

## 内容調整案（オプション）
[具体的な編集提案]
```

---

## タイトルパターン（実データ検証済み）

### 高パフォーマンス（40+ views）の共通点
| タイトル | Views | 成功要因 |
|----------|-------|----------|
| AI Does Tasks. Humans Do Deals. | 90 | 短い、対比構造、パンチライン |
| Micromanaging AI Doesn't Scale | 57 | 否定形、スケール問題に言及 |
| Giving AI Roles and Names | 42 | 具体的、好奇心を刺激 |

**効くパターン（優先度順）：**
1. **数字系**: "X Ways to...", "X Things..." （年間トップ15中47%）
2. **無料フック**: "for Free", "Free Tools"（1位記事に含まれる）
3. **時間/量の具体化**: "in 30 minutes", "10x better", "30+"
4. **対比構造**: "X Does A. Y Does B."
5. **強調形容詞**: "Every", "Must-Have", "Ultimate", "Practical"
6. **否定形の主張**: "X Doesn't Y"
7. **短い**（5-7語）

### 低パフォーマンス（<25 views）の共通点
| タイトル | 問題点 |
|----------|--------|
| Designing an AI-Operable Release Workflow | 専門的すぎる、長い |
| The Hidden Trust Problem in AI-Generated Documentation | 抽象的、長い |
| Contextual Code Review | 一般的すぎる |
| Part 2, Part 3系 | シリーズ途中は単体で弱い |

**効かないパターン：**
1. "How to + 長い説明"
2. 専門用語（Workflow, Contextual, Integration）
3. シリーズ途中の明示（Part 2, Part 3）
4. 曖昧な問題提起

---

## タイトルルール集

### ルール1: 否定は「結果」を否定せよ

同じ「Micromanagement」でも結果が違う：

| タイトル | Views | 構造 |
|----------|-------|------|
| Micromanaging AI Doesn't Scale | 57 | 否定形の主張 |
| Scope Management Is Not Micromanagement | 16 | 定義の否定 |

**効く否定**: "X Doesn't Y"（行動の結果を否定）
- 読者：「なるほど、それはやめよう」

**効かない否定**: "X Is Not Y"（定義を否定）
- 読者：「だから何？」

### ルール2: 動詞（主張）または価値を示す形容詞を入れろ

| タイトル | 構造 | Views/Reactions |
|----------|------|-----------------|
| AI Does Tasks. Humans Do Deals. | 主語 + 動詞 + 目的語 | 90 views |
| Every Developer **Needs** to Self-Host | 動詞（命令形） | 589 reactions |
| The **Ultimate** Tech Stack for Startups | 価値形容詞 | 489 reactions |
| Contextual Code Review | 形容詞 + 名詞のみ | 10 views |

**問題点：**
- 名詞句だけ → 主張がない → 読者：「だから何？」
- 動詞がない = アクションがない = 興味を引かない

**ただし例外あり：**
- 「Ultimate」「Must-Have」「Practical」など**価値を示す形容詞**があれば名詞句でも機能する

**改善例：**
- ✗ "Contextual Code Review"
- ✓ "Code Review Without Context Is Useless"
- ✓ "Why Context Makes Code Review 10x Faster"
- ✓ "The **Ultimate** Code Review Checklist"（形容詞で補完）

### ルール3: 動名詞（〜ing）で始めるな

| タイトル | Views | 問題 |
|----------|-------|------|
| Designing an AI-Operable Release Workflow | 4 | 動名詞開始 + 専門用語 |

**弱いパターン：**
| 動名詞 | 例 | 問題 |
|--------|-----|------|
| "Designing..." | Designing an AI-Operable Release Workflow | プロセスの説明に見える |
| "Building..." | Building a Chat App | チュートリアル臭 |
| "Creating..." | Creating REST APIs | 初心者向けに見える |
| "Implementing..." | Implementing OAuth | 手順書に見える |

**なぜ弱いか：**
- 「やってみた」感 → 読者：「で、何がわかったの？」
- 結果・主張が見えない
- プロセスに興味はない、結果に興味がある

**改善例：**
- ✗ "Designing an AI-Operable Release Workflow"
- ✓ "AI Can Run Your Release Pipeline. Here's How."
- ✓ "Why Your Release Workflow Should Be AI-Operable"
- ✓ "Release Workflows Don't Need Humans Anymore"

### ルール4: トピック幅を考慮せよ

タイトル構造が良くても、トピック自体がニッチだと読まれない。

**実例：**
| タイトル | Views | 問題 |
|----------|-------|------|
| The 1-Second Mystery: How AI Found What Load Testing Missed | 3 | 「Load Testing」がニッチすぎ |

**トピック幅の分類：**
| トピック幅 | 潜在読者 | 例 |
|------------|----------|-----|
| 広い | 全開発者 | AI, Git, Code Review, Career |
| 中間 | 特定領域 | React, Python, DevOps |
| 狭い | 専門家のみ | Load Testing, ksqlDB, Terraform |

**2つの戦略：**
1. **広いトピック × 良いタイトル** → 高トラフィック狙い
2. **ニッチトピック × SEO重視** → 長期的に検索で拾われる（第2波期待）

### ルール5: 「Free」「無料」は最強フック

| タイトル | Reactions | 
|----------|-----------|
| How to Use DeepSeek R1 **for Free** in VS Code | 1788（年間1位）|

**なぜ効くか：**
- 開発者はコスト意識が高い
- 「無料で使える」は即座にクリック理由になる
- 有料ツールの無料代替も強い

**使い方：**
- ✓ "How to Use X for Free"
- ✓ "Free Alternatives to [有料ツール]"
- ✓ "X Without Paying a Dime"

### ルール6: 時間・量・倍率を具体化せよ

抽象的な「効果がある」より具体的数値が効く。

| パターン | 例 | Reactions |
|----------|-----|-----------|
| 時間制限 | "in 30 minutes" | 682 |
| 倍率 | "10x better" | 461 |
| 量 | "30+ Ideas" | 768 |

**改善例：**
- ✗ "How to Build an AI Agent Quickly"
- ✓ "How to Build an AI Agent in 30 Minutes"
- ✗ "Make Your Project Better"
- ✓ "Make Your Project 10x Better"

### ルール7: 強調形容詞を使え

| 強調語 | 例 | Reactions |
|--------|-----|-----------|
| Every | "Every Developer Needs to..." | 589 |
| Must-Have | "The Must-Have SEO Checklist" | 346 |
| Ultimate | "The Ultimate Tech Stack" | 489 |
| Practical | "11 Practical Ways..." | 1506 |

**効く強調語リスト：**
- Every, All（全員対象感）
- Must-Have, Essential（必須感）
- Ultimate, Complete（網羅感）
- Practical, Actionable（実用感）
- Real, Honest（本音感）

---

## 高CTRパターン集（優先度順）

### 🥇 数字系（最強パターン）
- "X Practical Ways to..."（1506 reactions実績）
- "X Things I Regret Not Knowing Earlier"
- "X APIs to Make your Project 10x better"
- "X steps to building [成果]"
- "X mistakes to avoid..."

### 🥈 無料・コスト系
- "How to Use X for Free"（1788 reactions実績）
- "Free Alternatives to [有料ツール]"
- "X Without [コスト/痛み]"

### 🥉 時間制限系
- "Build X in 30 minutes"（682 reactions実績）
- "How I [成果] in [短期間]"
- "Learn X in One Weekend"

### 強調語系
- "Every Developer Needs to..."（589 reactions実績）
- "The Ultimate [対象] for [用途]"
- "The Must-Have [リスト] for [対象]"

### 対比・変換系
- "From Zero to Hero: [成果]"（470 reactions実績）
- "Turn [悪い状態] Into [良い状態]"
- "X vs Y: [判断軸]"
- "Why I switched from X to Y"

### 問いかけ系
- "Why your X isn't working"
- "Are you making this X mistake?"
- "What nobody tells you about X"

### 主張系
- "You don't need X"
- "Stop doing X"
- "X is overrated"

### 体験談系
- "What I learned from [経験]"
- "My journey to..."
- "The real cost of..."

---

## タイトル技術ガイドライン

### キーワード配置
重要なキーワードは先頭に配置：
- ✓ "React Hooks: A Complete Guide"
- ✗ "A Complete Guide to React Hooks"

### 長さガイドライン
- 理想: 40-60文字
- 最大: 70文字（それ以上は切れる）

### Dev.to特有の傾向
- 技術名は正確に（React, Vue, etc.）
- 年号を入れると新鮮さアピール
- 「for beginners」は初心者向けに有効
- 絵文字は控えめに（1つまで）

### 避けるべきパターン
- 曖昧なタイトル（"About X"）
- 過度な誇張（"AMAZING", "INCREDIBLE"）
- 質問だけで価値が不明（"What is X?"）
- 長すぎる（80文字超）

---

## 公開タイミング

### 避けるべき日（明確に読まれない）
- **クリスマス（12/25）**: ほぼ0
- **クリスマス直後（12/26-27）**: ほぼ0
- **年末年始（12/31-1/1）**: 低い
- **主要祝日全般**（米国: MLK Day, Thanksgiving等）

### 読者層の特性
Dev.toの読者は「仕事中に読む開発者」が多い：
- 平日の方が安定したトラフィック
- ただし週末にピークが出ることもある
- 祝日は明確に避けるべき

### 推奨戦略
1. **祝日を避ける**（最重要）
2. **平日の公開**（木-金が比較的良い傾向）
3. **週末は様子見**（土曜に高い日もある）

### タイムゾーン考慮
- Dev.toは英語圏読者が多い
- 米国東部時間（EST）の朝〜昼に公開が有利
- 日本時間だと夜〜深夜に公開

---

## 2段階流入モデル

良いタイトルの記事は「公開直後」だけでなく「後日」も読まれる。

### 実例："AI Does Tasks. Humans Do Deals."（90 views）
- **第1波（公開直後）**: 約38 reads
- **第2波（数日後）**: 1/13-15に10前後の波

### 実例："Micromanaging AI Doesn't Scale"（57 views）
- **第1波（公開直後）**: 約23 reads
- **第2波（数日後）**: 1/5-7、1/12-14に小さな波が継続

### 流入フェーズ
| フェーズ | タイミング | ソース（推測） |
|----------|-----------|---------------|
| 第1波 | 公開直後 | Dev.toフィード、初期SNSシェア |
| 第2波 | 数日〜1週間後 | Googleインデックス完了、SNS再シェア、アグリゲーター |

### 示唆
- **良いタイトルは「長く効く」** - 検索・SNSで後から発見される
- **エバーグリーン性** - 時事ネタでない普遍的内容は長期間読まれる
- **SEO対策の重要性** - 後日流入の多くはGoogle検索経由

---

## ルール早見表

| 優先度 | ルール | 実績 |
|--------|--------|------|
| 🥇 | **数字系タイトル** - "X Ways...", "X Things..." | 年間トップ47% |
| 🥇 | **「Free」フック** - 無料は最強の訴求 | 1位記事に含有 |
| 🥈 | **時間/量の具体化** - "in 30 min", "10x", "30+" | 682+ reactions |
| 🥈 | **強調形容詞** - Every, Must-Have, Ultimate | 589+ reactions |
| 🥉 | **対比構造** - "X Does A. Y Does B." | 90 views実績 |
| 🥉 | **否定形の主張** - "X Doesn't Y"（結果を否定） | 57 views実績 |
| ⚠️ | **動名詞で始めるな** - Building..., Creating... | トップ15に0件 |
| ⚠️ | **動詞/価値を入れろ** - 名詞句だけは弱い | 適合率67% |
| 📅 | **祝日を避けろ** - クリスマス/年末年始はほぼ0 | — |
| 🌍 | **広いトピック** - AI, Git, Career, 一般ツール | 高トラフィック |

---

## 注意事項

- 元の記事の本質・メッセージは変えない
- クリックベイトにならない範囲で最適化
- 著者の専門領域との一貫性を維持
- 継続的にデータを見て調整すること

---

## AI向けタイトル生成チェックリスト

タイトル案を生成する際、以下を順番にチェック：

```
□ 数字は入っているか？（最優先）
□ 「Free」や具体的な数値（時間/倍率）は入れられるか？
□ 強調形容詞（Every, Must-Have, Ultimate, Practical）は使えるか？
□ 動名詞（〜ing）で始まっていないか？
□ 動詞または価値を示す形容詞が入っているか？
□ トピック幅は適切か？（広い=高トラフィック、狭い=SEO長期戦）
□ 40-60文字に収まっているか？
□ 年号（2025）を入れると新鮮さが出るか？
```

**優先度の高い組み合わせ:**
1. 数字 + 実用的価値 + 強調形容詞
2. 無料 + 具体的ツール名 + 時間制限
3. 対比構造 + 短いパンチライン
