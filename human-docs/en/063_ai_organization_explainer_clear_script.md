<!-- xid: C4C18E540D44 -->
<a id="xid-C4C18E540D44"></a>

# AI Work Execution Explainer Script

This explainer describes the current XRefKit operating model for turning AI
output speed into continuous, reviewable work execution.

## Core Message

AI can stop midway. The operational problem is not interruption itself; it is
allowing unfinished or unchecked work to look complete.

- A Goal manages the desired state and acceptance conditions across Skills.
- Semantic routing selects the next Skill from the Goal and current state.
- A Skill narrows the delegated responsibility to a method and output boundary.
- Knowledge provides only the selected domain material needed for that judgment.
- The workflow protocol records and verifies each Skill Run before handoff or closure.

`verify` checks process completeness. Quality review and people accept output
content when that is required.

## Story Flow

1. AI can accelerate individual work, but output is not completed work.
2. Interruption loses context unless work state, evidence, and next ownership are explicit.
3. Prompts alone leave repeated explanation and completion judgment to people.
4. Goals hold the destination; Skills hold bounded responsibilities.
5. Routing selects the next responsibility from the current state.
6. Skills use selected Knowledge rather than loading an entire corpus.
7. The workflow protocol records work, evidence, uncertainty, verification, and handoff.
8. Verification catches process omissions; it does not automatically approve quality.
9. A stopped run can resume or hand off without reconstructing the whole conversation.
10. People own goals, acceptance, approvals, and exceptions.

## Closing Line

This is not a system for preventing AI from stopping. It is a system for
preventing work from being lost, or treated as complete, when AI stops.
