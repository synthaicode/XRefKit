<!-- xid: D2A8F61C9B04 -->
<a id="xid-D2A8F61C9B04"></a>

# Review Skill Loop Authoring Basis

This observation records the user decisions that shaped the private SQL review
Skill and review-skill improvement loop assets.

## Decisions

- Create a new SQL review Skill.
- Limit GitHub download targets to MIT-licensed repositories.
- Exclude large targets; reviewed source volume must not exceed 10 MB, excluding
  test code.
- Use a separate model and separate Skill for evaluation.
- Record token usage only for the review Skill side; evaluator token usage is
  not required.
- Do not commit loop outputs automatically.
- Delete downloaded source after each run.
- Preserve reports only.
- Retarget the loop toward C# + SQL business application repositories. A single
  repository containing both C# application behavior and SQL/database artifacts
  is preferred; separate C# and SQL repositories are fallback only.

## Authoring Implication

The loop is an improvement harness, not permission for automatic Skill
mutation. Skill update candidates must avoid repository-specific wording and
must be evaluated after the Skill change.
