<!-- xid: A6C3E8F1B472 -->
<a id="xid-A6C3E8F1B472"></a>
# Observation: Web visual clarity review basis

- Date: 2026-07-16
- Scope: Public XRefKit site top page and canonical Judgment Replication concept page.
- Evidence: The live top page renders a wide `.hero-shell`, while `site/sources/index.html` places only `.hero-copy` inside it. The companion `.hero-grid` CSS rule exists but is not used by that markup. At desktop width this leaves a large unoccupied right region beside the primary message. At mobile width the stylesheet switches the landing width to `calc(100vw - 20px)`, keeps the hero as one column, and stacks the actions vertically.
- Interpretation: The desktop hero has a visual-balance and attention-anchoring issue worth prioritizing, but whether the right region should be constrained or intentionally populated is a design judgment.
- Additional evidence: The Judgment Replication page has a long canonical heading and a dense mapping table; its table wrapper and mobile rules should be checked at intermediate widths before any implementation change.
- Limits: This observation does not establish WCAG conformance, keyboard behavior, real-device performance, or user-task success. Those require named tests and/or user evidence.
