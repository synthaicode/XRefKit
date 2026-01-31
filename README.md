# XRefKit

XRefKit is an OSS knowledge-ops toolkit for sharing knowledge with AI.

It keeps original sources (PDF/Excel/Web snapshots, etc.) in-repo, and maintains an AI-readable knowledge base as small Markdown “fragments”. Cross-document references use stable IDs (**XIDs**) so links keep working across rename/move/split/merge operations.

**Entry points**

- Human entry: `docs/000_index.md`
- Agent contract (always read): `agent/000_agent_entry.md`

## Why XIDs

When knowledge is split across many files, links break easily. XRefKit treats the `#xid-...` fragment as the primary key and rewrites only the *path* portion when files move.

Each managed Markdown file carries an XID block:

```md
<!-- xid: 1A2B3C4D5E6F -->
<a id="xid-1A2B3C4D5E6F"></a>
```

## Commands

```powershell
# Add/replace missing XIDs
python -m fm xref init

# Rewrite managed links that contain #xid-... to correct relative paths
python -m fm xref rewrite

# Validate XIDs and managed links
python -m fm xref check

# Human-review hints (best-effort)
python -m fm xref check --review

# Search and read only what you need
python -m fm xref search "query"
python -m fm xref show 1A2B3C4D5E6F

# Build a small context pack (seed + neighbors)
python -m fm ctx pack --seed 7C6C2B46A9D1 --depth 1 --out .xref\\pack.md
```
