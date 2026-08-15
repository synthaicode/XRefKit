<!-- xid: B4F1C8D2A612 -->
<a id="xid-B4F1C8D2A612"></a>

# IPA reconstruction guide mapping

This reference maps the human-oriented IPA guidance to the brownfield workflow.
It is an external reference and does not replace the repository contract.

## Source

IPA, [システム再構築を成功に導くユーザガイド 第2版](https://www.ipa.go.jp/archive/publish/secbooks20180223.html).
The guide is intended to help user organizations choose a reconstruction
method and create a systemization plan that avoids downstream risk and gaps
between user and development organizations.

## Mapping to this Skill

| IPA perspective | Brownfield workflow use |
|---|---|
| Start from the reconstruction purpose, current-system state, and new-system requirements | Validate the existing Requirement, preserve current evidence, and state the desired behavior separately |
| Select a reconstruction method and identify risks | Reconcile current specification, current behavior, and new requirements; classify each delta and unresolved risk |
| Consider preventive measures in the planning phase | Produce the initial work policy, then refine it after delta approval into work, data, compatibility, release, rollback, test, and evidence plans |
| Share risks and countermeasures between user and development organizations | Make human decision owners, evidence, gates, handoffs, and residual-risk acceptance explicit |
| Treat ambiguous current specifications as a reconstruction risk | Do not infer business truth from implementation; keep unsupported statements as `unknown` with resolver and owner |

## Operating rule

AI may inventory evidence, compare the three sources, propose risk controls,
and derive candidate work and test items. The human approves the purpose,
protected invariants, delta meaning, risk acceptance, release conditions, and
any unresolved business or expected-result decision.

The IPA sequence is therefore used as a review lens:

`purpose/current state/new requirements -> method and risk view -> agreed countermeasures -> detailed plan -> execution evidence`

Do not mark a delta as approved merely because the current implementation
supports it. Current implementation and historical documents are evidence;
business meaning and acceptance remain human-owned decisions.
