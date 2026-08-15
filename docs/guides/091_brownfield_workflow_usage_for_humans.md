<!-- xid: D6A4C9E2F817 -->
<a id="xid-D6A4C9E2F817"></a>

# ブラウンフィールドWorkflowの使い方

このガイドは、既存のコードベースやサービスを変更するときに、
`brownfield-workflow` Skillを人間がどのフェーズでどのように使うかを
説明します。

## 目的

ブラウンフィールドでは、現在の実装がそのまま業務仕様とは限りません。
そのため、既存の挙動、変更目的、設計、テスト結果、人間の判断を分離し、
同じ upstream item を最後まで追跡します。

基本の流れは次のとおりです。

```text
requirements → planning → design → manufacturing → testing → closure
```

各フェーズでは、前のフェーズから次の情報を引き継ぎます。

- upstream item と追跡関係
- evidence と根拠
- `unknown`、リスク、未決事項
- owner と次のアクション
- 人間が行った判断と承認

## まず何を依頼するか

最初の依頼では、Skill名、対象、変更目的、現在のフェーズ、出力を明示します。

```text
Use $brownfield-workflow in <phase> phase.
Upstream item: <upstream_ref>
Target: <service, module, screen, API, database, or path>
Change objective: <what and why>
Scope: <included and excluded areas>
Output: <required report or handoff>
```

フェーズが不明な場合は、次のように依頼できます。

```text
Use $brownfield-workflow to determine the current phase and organize the
upstream item without inventing missing behavior.
```

## フェーズ別の使い方

| Phase | 目的 | 主な作業 | アウトプット | 人間の判定 | AIの役割 |
|---|---|---|---|---|---|
| `requirements` | 何を変え、何を保証するかを確定する | 既存Requirementがあれば権限、鮮度、整合性、テスト可能性を検証し、現状、望ましい状態、受入条件、正常・異常・境界条件を分ける | Requirement検証結果、要求項目、根拠、範囲、未決事項 | 業務目的、受入条件、範囲、Requirementの採用可否を判断する | 事実、仕様、推測、未決事項を分離し、不足・矛盾・陳腐化を指摘する |
| `planning` | 変更を安全に進める計画と検証条件を定め、差分確定後に詳細化する | 要求から初期作業方針を作り、仕様整合性マトリクスの承認後に差分・データ・互換性・テスト・証拠・handoffを再計画する | 初期作業方針、差分詳細計画、影響範囲、テスト準備、ゲート | 初期計画が承認済み差分を反映し、実行順・owner・停止条件・証拠方法が足りているか | 初期計画を作り、差分確定後にwork unit、依存、データ、テスト、リスクを詳細化する |
| `design` | 現行仕様・現行挙動・新規要求の整合をとり、承認された要求を実装可能な構造へ落とす | 三者の差分、保護する不変条件、互換性・下流影響、契約、状態、エラー、観測点、テスト可能性を確認する | 仕様整合性マトリクス、設計差分、design-to-test handoff、ケース候補、定義不足 | 各差分の分類・根拠・影響・owner・判断があり、設計へ進めてよいか | 三者を比較し、差分、影響、未定義、必要な判断を整理する |
| `manufacturing` | 承認済み設計を既存環境の規約内で実装する | コード・設定・DB等を変更し、整合性と競合を確認する | 変更成果物、整合性証拠、露呈した判断事項 | 設計どおりか。形式・競合・仕様整合の証拠があるか。未解決事項が残っていないか | 実装、機械的検査、証拠整理、未解決事項の報告を行う |
| `testing` | 変更による意図した差分と意図しない破壊を確認する | 変更前後の実行、証拠取得、比較、差異分類、再テストを行う | テスト結果、証拠、差異分類、残余リスク | planned differenceとunexplained differenceを区別できるか。範囲とリスクを受入可能か | ケース実行、UI/API評価、比較、分類、報告を行う |
| `closure` | 結果と残余リスクを人間が判断できる状態にする | upstream、証拠、unknown、判断、handoffを追跡する | summary-first報告、判断記録、残余リスク、handoff | 全upstreamが追跡され、unknownに対応があり、次の判断が明確か | summary-first報告とtraceabilityを整える |

## Requirements

### 目的

変更の目的と、変更後に何を保証するかを人間が判断できる状態にします。

### 作業

既存のRequirement、受入仕様、チケット、契約などがある場合は、先にその内容を
検証します。確認する項目は次のとおりです。

- Requirementの識別子、source、version、更新日、owner、承認状態
- 対象範囲と除外範囲
- 現行挙動との整合
- 変更目的、設計、データフロー、既存テストとの整合
- 受入条件の正常・異常・境界条件
- 入力、期待値、観測方法、合否判定、証拠の定義

検証結果は、確認済み、不足、矛盾、陳腐化、未検証に分類し、根拠と影響を
付けます。既存RequirementをAIが勝手に修正したり、正しいとみなしたりしません。

このフェーズでは、実装を仕様とみなさず、次を分離します。

- 変更の目的
- 現在確認できる挙動
- 変更後に望む挙動
- 受入条件
- 対象範囲と除外範囲
- 正常、異常、境界条件
- 仮定と未決事項

現在のコードに書かれていない業務上の意味をAIに補完させません。
不足している場合は、理由、影響、確認者、次のアクションを持つ
`unknown` として扱います。

### 役割分担

- 人間: 変更目的、受入条件、業務上の期待値、対象範囲を決める。
- AI: 現状の証拠を集め、現在の挙動と望ましい挙動を分離し、未決事項を可視化する。

### アウトプットの判定

人間は、要求が業務目的と一致し、受入条件が検証可能で、対象範囲と除外範囲が
明確かを確認します。不足がある場合は、承認せず、確認事項とownerを付けて
`unknown` として次へ渡します。

既存Requirementを設計やテストの根拠として採用する場合は、source、version、
authority、owner、鮮度、現行挙動との整合、受入条件のテスト可能性を確認します。
重大な矛盾、期待値不足、owner不明、承認状態不明が残る場合は、採用せず、
修正、保留、またはescalationとします。

## Planning

### 目的

実装とテストを後から場当たり的に追加せず、変更を安全に進める作業条件を定めます。
計画は一度で完了せず、要求段階の初期計画と、仕様整合性確認後の詳細計画の
二つのチェックポイントを持ちます。

### 作業

このフェーズでは、まずRequirementと現行証拠から初期作業方針を定めます。

- impacted targets と downstream impact
- 依存関係と実行順
- tools、versions、environment
- fixture、test data、cleanup
- compatibility、migration、release、rollback
- result storage、evidence、owner
- stop conditions、gates、handoffs

仕様整合性マトリクスで差分が承認された後、初期作業方針を次の観点で更新します。

- 差分行から具体的なwork unit、実装点、依存、実行順、ownerを再計算する
- データ変更、互換性、migration、release、rollback、運用制御を詳細化する
- テストケース、fixture、期待値、証拠、変更前ベースライン、retestを詳細化する
- 差分、work unit、test、evidence、handoffをtraceabilityで結び付ける

差分が計画の範囲、挙動、互換性、データ伝播、テスト影響を変える場合、
要求段階の初期計画をそのまま最終計画として扱いません。

ここでテストツールを準備し、テスト実行は `testing` で行います。

さらに、テストケースを作る前にテスト可能性を確認します。

- 対象が特定できるか
- 前提と入力データがあるか
- 期待値とその根拠があるか
- UI、API、log、event、DBなどの観測手段があるか
- 合否判定方法があるか
- 変更点と証拠を追跡できるか

不足がある場合、AIはケースを推測で完成させず、定義不足として返します。

### 役割分担

- 人間: 優先度、制約、owner、停止条件、リスク受容を承認する。
- AI: 影響範囲、依存、実行順、テスト準備、テスト可能性の不足を整理する。

### アウトプットの判定

人間は、計画どおりに実行できる環境、データ、ツール、証拠取得方法、担当者が
揃っているかを確認します。影響範囲が不明なまま、または停止条件とhandoffが
ない場合は、計画を承認せず修正します。

さらに、仕様整合性確認後の詳細計画について、承認済みの差分行がすべて
work unit、テスト、証拠、owner、実行順に反映されているかを確認します。
差分後の影響が初期計画に反映されていない場合は、manufacturingやtestingへ
進めず、計画を更新します。

## Design

### 目的

現行仕様・現行挙動・新規要求の整合をとり、承認済み要求を実装・観測・
テストが可能な構造と契約に変換します。

### 作業

設計差分を決める前に、次の三者を比較します。

- 現行仕様：承認された既存の要求・契約
- 現行挙動：source、test、UI、API、log、dataなどで確認した実際の動き
- 新規要求：今回追加・変更する要求と受入条件

各項目を次のいずれかに分類し、仕様整合性マトリクスに記録します。

- `preserve`: 現行仕様を維持
- `change`: 現行仕様を変更
- `add`: 新規に追加
- `deprecate`: 廃止
- `incompatible`: 互換性に影響する変更
- `unknown`: 判断材料が不足

さらに、保護する不変条件、設計差分、互換性、下流影響、migration、rollback、
テスト影響、ownerを記録します。

このフェーズでは、承認済み要求に対応する構造差分だけを整理します。

- service、API、message、DB、data contract
- processing、state、transaction
- idempotency、concurrency
- error、retry、timeout、rollback
- compatibility、migration
- observability と変更点
- design-to-test handoff

設計レビューの最後に、変更された各挙動について、再現可能なテストケースを
定義できるかを確認します。期待値、観測点、fixture、ownerが不足する場合は、
実装へ進めず、必要な判断を明示します。

### 役割分担

- 人間: 構造、データ契約、業務ルール、期待値・判定基準の意味を承認する。
- AI: 変更点、依存関係、状態・エラー経路、観測点を整理し、テスト定義不足を指摘する。

### アウトプットの判定

人間は、設計が要求と影響範囲に整合し、変更された挙動ごとに対象、条件、入力、
期待値、観測方法、合否基準、証拠を定義できるかを確認します。定義できない
ケースは推測で承認せず、設計または要求へ差し戻します。

加えて、仕様整合性マトリクスの各行について、現行仕様、現行挙動、新規要求の
差分分類が妥当で、根拠、保護する不変条件、互換性・下流影響、owner、判断が
揃っているかを確認します。重大な`incompatible`または`unknown`が残る場合は、
設計を承認せず、修正、保留、またはescalationとします。

## Manufacturing

### 目的

承認された設計だけを、既存システムの規約と変更安全性を守って実装します。

### 作業

実装では、承認済み設計にない判断をコードで新たに決めません。

既存ファイルを変更する場合は、次を確認します。

- encoding、BOM、newline
- 編集前のrevisionとbytes
- 仕様とのalignment
- concurrent editの有無
- 既存の未コミット変更
- 新規ファイルのローカル規約

実装中に要求、設計、互換性、データに関する未解決事項が現れたら、
推測で進めず `unknown` または `blocked` として返します。

### 役割分担

- 人間: 実装方針の変更、仕様解釈、例外、未解決事項の判断を行う。
- AI: 承認済み設計に沿って変更し、形式、revision、競合、仕様整合の証拠を残す。

### アウトプットの判定

人間は、実装が承認済み設計の範囲内で、ファイル形式、同時編集、仕様整合性を
損なっていないかを証拠で確認します。実装中に新しい業務判断が発生している
場合は、完了扱いにせず要求または設計へ戻します。

## Testing

### 目的

変更による意図した差分と、意図しない既存挙動の破壊を区別します。

### 作業

テストでは、変更前のベースラインまたは事前テストスイートを用意し、
変更後に同じ入力とデータ状態で再実行します。

AIには次を依頼できます。

- 承認済みテストケースの生成補助
- UI、API、log、event、DBの証拠取得
- 個別項目の期待値比較
- 変更前後の結果比較
- 差異の分類
- retestと残余リスクの整理
- overview/detail報告の作成

結果は、少なくとも次の分類を区別します。

- preserved behavior
- approved/planned difference
- unexplained difference
- invalid/upstream-absent
- uncertain
- system error
- not executed

UIテストでは、画面のハードコピー、期待値、実結果、個別判定、総合評価を
紐付けます。期待値表がUIラベルと一致しなくても、意味、値、表示規則、根拠が
追跡できれば評価できます。

### 役割分担

- 人間: テスト範囲、期待値、差異の意味、残余リスク、受入可否を判断する。
- AI: 承認済みケースを実行し、画面・API・ログ等を比較して証拠付きで報告する。

### アウトプットの判定

人間は、実行範囲が変更影響に対して十分か、結果が再現可能か、planned differenceと
unexplained differenceが混同されていないかを確認します。未実行、uncertain、
system errorを合格として扱わず、再実行、追加調査、または残余リスクとして判断します。

## Closure

### 目的

変更結果、未解決事項、証拠、残余リスクを人間が判断できる形で閉じます。

### 作業

最後に、次の順序で人間向け報告を作成します。

1. `Status`
2. `Result`
3. `Evidence`
4. `Open Items`
5. `Handoff`

closure前に、すべてのin-scope upstream itemが結果と証拠に結び付いていること、
すべての`unknown`に理由、影響、resolver、ownerがあることを確認します。

### 役割分担

- 人間: 残余リスク、リリース可否、次のowner、未解決事項の扱いを決める。
- AI: upstream itemから結果・証拠・判断・handoffまでの追跡関係を整える。

### アウトプットの判定

人間は、すべてのin-scope upstream itemが結果と証拠に結び付いているか、
`unknown`に理由・影響・resolver・ownerがあるか、残余リスクを受容できるかを
確認します。未解決の重要事項がある場合は、closureではなくhandoffまたは
escalationとします。

## 人間が判断すること

AIは調査、整理、ケース生成、反復実行、比較、証拠化を支援します。
次の判断は人間が行います。

- 業務上の期待値
- 変更範囲とリスクの受容
- 要求・設計の承認
- 期待値・判定基準の意味上の正しさ
- unexplained differenceの扱い
- 残余リスクとリリース可否

## 詳細手順

- 参考：[IPA「システム再構築を成功に導くユーザガイド 第2版」](https://www.ipa.go.jp/archive/publish/secbooks20180223.html)
- IPAの観点は、目的・現行状態・新規要求からリスクを明らかにし、対策を合意して計画へ落とすための人間向けレビュー軸として使います。Repositoryの判断は、証拠、差分、owner、gate、human decisionとして記録します。
- [Brownfield Workflow Skill](../../skills/brownfield-workflow/SKILL.md#xid-A17C4E8B2D91)
- [フェーズ手順](../../skills/brownfield-workflow/references/phase-workflow.md#xid-B4F1C8D2A601)
- [既存Requirementの検証](../../skills/brownfield-workflow/references/requirements-validation.md#xid-B4F1C8D2A608)
- [仕様整合性の確認](../../skills/brownfield-workflow/references/specification-reconciliation.md#xid-B4F1C8D2A609)
- [差分確定後の詳細計画](../../skills/brownfield-workflow/references/delta-detail-planning.md#xid-B4F1C8D2A610)
- [テスト可能性ゲートとAIケース生成](../../skills/brownfield-workflow/references/testability-and-case-generation.md#xid-B4F1C8D2A607)
- [変更影響型テスト](../../skills/brownfield-workflow/references/change-test-suite.md#xid-B4F1C8D2A604)
- [報告とclosure](../../skills/brownfield-workflow/references/reporting-and-closure.md#xid-B4F1C8D2A605)
