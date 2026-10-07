<!-- xid: EA41CDDB2AAB -->
<a id="xid-EA41CDDB2AAB"></a>

# Attention Pet 検証状況

更新：2026-09-28。現在のローカル版は、このチャットの発言に連動し、モデル × reasoning effort の組合せを比較する。

用語整理後の確認：利用者向けの `Profile Fit` と互換APIの `modelFit` を分離し、旧 `light|standard` 入力の `selectedProfile` は標準名 `low|medium` になること、Pet横に短い候補案内が表示・消去されることを確認した。Attention Pet対象は118 passed、全体は895 passed、1 skipped、2 subtests passed。対象worktreeからポート8770で起動した実ブラウザーで、Profile FitのラベルとAstra / highからSol / mediumへの候補がPet横に表示されることを確認した。別AIによる再実装結果は未検証。

今回の変更では、対応する全Execution Profileを探索し、同一モデルの深さ変更、異なるモデル・深さの横断比較、能力不足時の候補抑制、失敗記録時のReview優先、Partial/Unknown、未知の組合せ、旧 `light|standard` 入力をテストした。`/api/profiles` のモデル別対応深さ、GET未知値のUnknown、更新APIの拒否、schemaとPython modelの一致も確認した。全テストは895 passed、1 skipped、2 subtests passed。`node --check` と `git diff --check` は成功。数値の実能力・価格・総コストは未校正。

- 過去の実チャットのローカル記録で、利用者発言30件、実行設定 `gpt-6-sol / medium`、旧版の仮対応付けSol/standard、Coverage=Partialを確認した。現行アダプターはSol/mediumへ対応付ける。画面画像：[live-chat.png](evidence/live-chat.png)。
- 2026-09-27に、カードとPetだけの常時表示を実ブラウザーで確認した。画面画像：[card-only-live-chat.png](evidence/card-only-live-chat.png)。
- 2026-09-27に、Pet横の短文へPartialの範囲を統合し、評価の説明とモデル設定情報を分離した。画面画像：[wording-granularity-live-chat.png](evidence/wording-granularity-live-chat.png)。状態ごとの短文と次の行動を含む全501テストが成功した。
- 2026-09-27に、通常は実行中のCodex設定に追従し、手動比較では試算するモデルと深さを固定できることを確認した。Luna/lightへの変更で試算だけがUnderpoweredへ変わり、Codex modelはSol/mediumのまま保持された。画面画像：[comparison-controls.png](evidence/comparison-controls.png)。
- 2026-09-27に、トークンを含まない `http://127.0.0.1:8769/` で画面とGET `/api/state` を表示できることを実ブラウザーで確認した。手動更新用POSTは認証なしでは401となることを確認した。
- 2026-09-27に、provider-neutralな `attention-pet-client-v1` のhandshake、相手識別、loopback限定クライアント、セッション切替、セッション別保存、revision競合拒否、1行JSON起動情報を追加した。Codex・VS Code/Copilot固有アダプターはこの共通契約とは別の配布単位とする。
- 2026-09-27に、ブラウザーの優先言語に従う日本語・英語表示を追加した。APIのPresentation、評価理由、画面の静的・動的文言が同じ言語になり、言語を変えても機械判定値が変わらないことを確認した。
- 合成ログで発言の追加、モデルと考える深さの変更、未対応モデルのUnknown、発言本文を保存しないこと、手動更新APIを409で拒否することを確認した。画面テストで新しい発言の受信時だけ短い動きが始まることも確認した。対象チャットは起動時に固定する。
- 利用者向けの人工シナリオ操作とデモAPI・CLIはない。合成シナリオは内部テストだけに残す。画面は実行条件とコストの配分カードとPetだけを常時表示し、背景画面、画面切替、手動ファイル入力、整理操作を提供しない。
- `CostFit` は `Unknown / RetryRisk / NoLowerCostCandidate / LowerCostCandidateAvailable / ReviewNeeded`。Python modelと `schema/fit.schema.json` の内容一致を確認した。
- 旧版では全テスト893件（skip 1件）が成功した。今回の全テスト結果は冒頭の検証記録を参照。

2026-09-28の再レビュー対応：アクティブなセッションがSol/mediumからAstra/highへ切り替わると自動比較が新しい実行条件を使用し、手動比較中は選択値を維持し、比較解除後は追従に戻ることを画面のDOMテストで確認した。総コストの表示に待ち時間を加え、未定義のreasoning levelをModelProfile構築時に拒否するテストを追加した。対象85テストと全体896テストが成功した（全体は1 skipped、2 subtests passed）。ポート8769の起動済みサービスを修正版で再起動し、画面の新しい配信内容とこのチャットのSol/mediumへの連動をHTTPで確認した。

2026-09-28のR4対応：クライアントの有効セッションについて、作業内容・試算条件・表示元を同じロック下で取得するようにした。取得後に別セッションへ切り替えても応答が旧セッション内で揃うこと、取得中の切替通知が完了まで待つことをテストした。全体898件成功、1件スキップ、2 subtests passed。ポート8769のサービスを修正版で再起動し、現在のCodexチャットのSol/medium表示を確認した。実クライアントでの競合頻度と独立した再レビューは未確認。

未検証：Codexクライアントからの即時セッション選択通知、GitHub Copilot組み込みChat全体のセッション選択通知、各アダプターが作るWorkingSetの妥当性、実モデルの品質・料金・総コスト。現行の判定と表示は [仕組みの説明](MECHANISM.md#xid-A4D0C1E89B73) を参照。
