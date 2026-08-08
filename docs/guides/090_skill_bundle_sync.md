<!-- xid: 8D7F2A6C4B10 -->
<a id="xid-8D7F2A6C4B10"></a>

# GitHub ReleaseからSkill Bundleを同期する

PyPIに未登録のSkillを管理者がまとめて取得する場合は、XRefKitの同期CLIを
使う。利用者がZIPを探して個別に展開する必要はない。

## 同期

現在のリポジトリへ、C#用のSkill専用タグに対応する最新GitHub Releaseを取得して登録する。

```powershell
python -m xrefkit skills sync --bundle csharp
```

複数bundleを同期する場合は、次のように指定する。

```powershell
python -m xrefkit skills sync --bundle csharp --bundle brownfield
python -m xrefkit skills sync --all
```

対象リポジトリを変更する場合は `--repo` を指定する。

```powershell
python -m xrefkit skills sync `
  --repo C:\dev\itsm\XRefKit `
  --source-repository synthaicode/XRefKit `
  --bundle csharp
```

## 安全確認

同期状態は `.xrefkit/skill-sync/` に保存する。前回同期したファイルは更新
できるが、手作業で存在するファイルを確認なしに上書きしない。

```powershell
python -m xrefkit skills sync --bundle csharp --dry-run --json
```

どうしても既存ファイルを置換する場合だけ、差分を確認して `--force` を使う。

```powershell
python -m xrefkit skills sync --bundle csharp --force
```

同期後にMCPサーバーを再起動すると、リポジトリのライブカタログがSkillと
Knowledgeをセマンティックルーティング対象として読み込む。同期は管理者の
登録操作であり、通常の利用者が個別Skillを選択する操作ではない。

## GitHub Releaseのbundle

Skill Packageのタグを公開すると、Workflowが次の形式のZIPを生成してReleaseへ
添付する。

```text
xrefkit-skills-csharp-0.1.0.zip
└─ xrefkit-skills-csharp/
   ├─ skills/
   ├─ knowledge/
   ├─ review_axes/
   ├─ schemas/
   └─ package_manifest.yaml
```

bundleはドメイン単位で作成し、PyPIのPython Packageとは別に、管理者向けの
導入・レビュー用成果物として扱う。

`--release latest` は通常のXRefKit Releaseではなく、指定したbundleの
`xrefkit-skills-<bundle>-v<version>` タグに対応する公開Releaseから最新を選ぶ。
特定のタグを固定する場合は、`--release xrefkit-skills-csharp-v0.1.0` のように
指定する。
