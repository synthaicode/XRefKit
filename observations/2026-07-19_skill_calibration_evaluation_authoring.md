<!-- xid: 7E4B2C9A61D0 -->
<a id="xid-7E4B2C9A61D0"></a>

# Skill calibration evaluation authoring observation

- date: `2026-07-19`
- skill_id: `skill_calibration_evaluation`
- basis: user-directed design for PyPI-bundled Skill evaluation and calibration protection
- decision: keep evaluation discovery and fixture isolation at the installed package boundary; do not use repository-relative runtime paths
- decision: keep expected answers and calibration rules outside the evaluated target and model context
- decision: public package cases are smoke coverage; held-out evaluation belongs to a separate controlled evaluator boundary
- unresolved: common xrefkit runtime command for invoking each package Skill and the final score schema
