# Issue #199 Human View retrospective replay

Source: [Issue #199, R2 pre-approval review](https://github.com/synthaicode/XRefKit/issues/199#r2-pre-approval-review-and-downstream-verification).
The input is the read-only issue snapshot last updated at `2026-11-21T05:28:34Z`.
The fetched record is retained in the local session evidence. Its raw JSON SHA-256
is `66620f242979b7d3e48dbb764062f003e16cd75d332cddd0e691af4824c5e65b`.
The decision basis is the exact R2 revision in the Issue. The
[canonical finding](https://github.com/synthaicode/XRefKit/blob/f065e8decf344be66758696ff9994dfc4c505949/knowledge/source_analysis/174_xrefkit_api_execution_boundary_findings.md#xid-0A4F8C62D199)
owns the inspected source facts. GitHub Project #3 is the progress entry point
designated by the Issue.

## Before

The existing [R2 section](https://github.com/synthaicode/XRefKit/issues/199#r2-pre-approval-review-and-downstream-verification)
is the before output for the same evidence and decisions. From the R2 section marker
through the block before the next major heading, it contains 12,690 characters
of Markdown, including source verification, a three-item decision table, effect
gate requirements, reconciliation cases, downstream assignments and pinned
evidence. The status and implementation hold recur in separate places. The
review conclusion, pending human decisions and future verification must be read
together to understand what a decision would allow. The original is retained
as the evidence source for this comparison.

## After

**R2の設計判断は保留中です。** 提案段階の独立レビューは完了し、ソース調査結果は登録済みです。#200の実装と検証は未着手です。前回報告の基準点は不明です。

依頼者はR2-A〜Cごとに承認・修正・保留を記録してください。承認の範囲は設計条件までです。#200の実装開始はA199-4、外部API実行とデータ変更は各権限の別判断です。保留中は該当する設計判断と、それを前提とする作業の開始が止まります。

- **R2-A｜実行者を一人に絞る。** 最新のフロー状態と実行権を一体で確認し、送信・ツール実行のたびに一回限り許可する方針を承認するか。古い実行者が再開しても追加実行できないことを実際の送信経路で示せるまで、実行や交代は保留。Runtime・ホスト担当が設計します。
- **R2-B｜結果を安全に反映する。** Runtimeが最新の実行権と結果を照合し、反映済みか確認して二重反映を防ぐ方針を承認するか。モデルが不明・不一致なら成功の反映を保留し、操作の影響が不明な間は再割当につながる失敗の反映も保留。Runtime担当が書き込みと復旧を設計します。
- **R2-C｜結果不明の操作を保留する。** 元の操作・試行・費用枠を保持し、信頼できる結果または未送信・影響なしの証拠を得る方針を承認するか。実行の影響・出力・使用量は別々に確認し、再試行は証拠か承認済みの再実行条件があり、同じ割当の範囲に限ります。未解決の有料送信は保留し、ポリシー・復旧担当が証拠と費用精算の条件を決めます。

根拠と検証先は[R2の判断・検証記録](https://github.com/synthaicode/XRefKit/issues/199#r2-pre-approval-review-and-downstream-verification)を参照してください。依頼者の判断後、担当者が条件を記録します。設計に重要な変更があれば独立レビューに戻します。

## Evaluation

| Check | Result in the retrospective replay | Trace |
| --- | --- | --- |
| Current status | Opening shows proposal-level review, canonical registration, pending disposition and no implementation/verification. | R2 review and canonical source registration sections |
| Decisions | Separate prompts for exclusive authority, result projection and unknown effects. Each names the resolving role. | R2-A, R2-B and R2-C |
| Scope | The design choice, A199-4, live API and data-change approvals remain separate. A199-1 and A199-3 remain in the linked decision record. | R2 decisions and #200 approval criteria |
| Decision-changing risks | Stale executor, duplicate effects/projection, model mismatch, unresolved effects and paid sends remain visible. Unverified store, fencing, receipt and evidence policies retain their downstream route. | R2 effect gate, reconciliation and verification sections |
| Traceability | Full Issue snapshot and pinned canonical Knowledge remain reachable. Evidence revisions, hashes, technical trace, tool/model notes and downstream tests stay in their sources. | Source paragraph above and original Issue |
| AI handoff | Existing records retain the detailed constraints, named Issues and test evidence. The sample adds no alternate record or approval. | Original R2 and exact versioned sources |
| Reading load | One shared status/authority paragraph and three decisions replace repeated history in the human-facing sample. The complete scoped Markdown is reduced from 12,690 to 833 characters. The three decisions are individually scannable. | Before and After |
| Compatibility | The same five Skill definitions and approved bytes, package IDs, Runtime contracts and Brownfield integration are used. Local regression results are recorded below. | Package and integration checks |

This is a retrospective evaluation of the written procedure and example. It does
not test a live GitHub write or a production PM run. The evaluation does not
approve R2 or start #200. A project must confirm its evidence location and
permissions before replacing existing Issue text. If old links depend on Issue
anchors, resolve the retention and reference plan before replacement.

## Regression evidence

| Check | Result |
| --- | --- |
| XID validation and package materialization | 0 XID issues and 17 generated assets in exact parity |
| Repository materialization and Runtime governance suites | 22 passed |
| Wheel and sdist metadata and archive inspection | Both passed, including the shared procedure in both formats |
| Wheel and sdist installed tests with local Core 0.7.12 and Brownfield 0.3.1 | 54 passed per format, including the five native methods' reference and the Human View safeguards. Two existing filesystem-link tests failed in the Windows sandbox. |
| Baseline PM 0.1.0 wheel, same Core and Brownfield | 53 passed. Both existing failures reproduced with the same junction/hardlink permission errors. |

The existing Linux release workflow runs the full suite, scans the archives and
tests published Core before Trusted Publishing. Local candidate checks do not
prove that the release workflow passed or that the package was published.
