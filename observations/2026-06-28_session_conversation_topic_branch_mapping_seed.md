# Session: conversation_topic_branch_mapping seed

- date: `2026-06-28`
- source_request: `複数人のコミュニケーションでは一つのトピックから枝分かれすることがある。これを整理し、各トピックへの参加者のかかわり度、中心人物を抽出できるようにしたい。`
- authored_skill: `skills/packs/business-intake/conversation_topic_branch_mapping/meta.md`
- publication_boundary: public Skill owned by `business-intake`
- maturity_basis: `trial`; the procedure is runnable, includes sample input/output, and needs real conversation runs before stable promotion.
- anti_forgetting_focus:
  - preserve root topic and branch lineage
  - bind branch labels to evidence
  - classify participant involvement per branch without employee evaluation
  - identify central participant candidates as coordination signals only
  - keep handling classification, unknowns, and human review explicit
