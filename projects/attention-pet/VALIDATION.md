<!-- xid: EA41CDDB2AAB -->
<a id="xid-EA41CDDB2AAB"></a>

# Attention Pet 検証状況

更新：2026-09-27。現在のローカル版は、このチャットの発言に連動する。

- 実チャットのローカル記録で、利用者発言30件、実行設定 `gpt-6-sol / medium`、仮の対応付けSol/standard、Coverage=Partialを確認した。画面画像：[live-chat.png](evidence/live-chat.png)。最後は表情だけ表示へ戻した。
- 2026-09-27に、カードとPetだけの常時表示を実ブラウザーで確認した。画面画像：[card-only-live-chat.png](evidence/card-only-live-chat.png)。
- 2026-09-27に、Pet横の短文へPartialの範囲を統合し、評価の説明とモデル設定情報を分離した。画面画像：[wording-granularity-live-chat.png](evidence/wording-granularity-live-chat.png)。状態ごとの短文と次の行動を含む全501テストが成功した。
- 2026-09-27に、実行中のCodex設定を初期値としつつ、試算するモデルと深さを操作できることを確認した。Luna/lightへの変更で試算だけがUnderpoweredへ変わり、Codex modelはSol/mediumのまま保持された。画面画像：[comparison-controls.png](evidence/comparison-controls.png)。
- 2026-09-27に、トークンを含まない `http://127.0.0.1:8769/` で画面とGET `/api/state` を表示できることを実ブラウザーで確認した。手動更新用POSTは認証なしでは401となることを確認した。
- 2026-09-27に、provider-neutralな `attention-pet-client-v1` のhandshake、相手識別、loopback限定クライアント、セッション切替、セッション別保存、revision競合拒否、1行JSON起動情報を追加した。Codex・VS Code/Copilot固有アダプターはこの共通契約とは別の配布単位とする。
- 2026-09-27に、ブラウザーの優先言語に従う日本語・英語表示を追加した。APIのPresentation、評価理由、画面の静的・動的文言が同じ言語になり、言語を変えても機械判定値が変わらないことを確認した。
- 合成ログで発言の追加、モデルと考える深さの変更、未対応モデルのUnknown、発言本文を保存しないこと、手動更新APIを409で拒否することを確認した。画面テストで新しい発言の受信時だけ短い動きが始まることも確認した。対象チャットは起動時に固定する。
- 利用者向けの人工シナリオ操作とデモAPI・CLIはない。合成シナリオは内部テストだけに残す。画面はモデルとコストの配分カードとPetだけを常時表示し、背景画面、画面切替、手動ファイル入力、整理操作を提供しない。
- `CostFit` は `Unknown / RetryRisk / NoLowerCostCandidate / LowerCostCandidateAvailable / ReviewNeeded`。Python modelと `schema/fit.schema.json` の内容一致を確認した。
- 全テスト893件（skip 1件）が成功。JavaScript構文とJSON解析を確認し、全対象を含めたXID参照チェックは問題0件だった。

未検証：Codexクライアントからの即時セッション選択通知、GitHub Copilot組み込みChat全体のセッション選択通知、各アダプターが作るWorkingSetの妥当性、実モデルの品質・料金・総コスト。現行の判定と表示は [仕組みの説明](MECHANISM.md#xid-A4D0C1E89B73) を参照。
