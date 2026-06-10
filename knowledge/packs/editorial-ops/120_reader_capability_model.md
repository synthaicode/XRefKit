<!-- xid: 125B6C5E3630 -->
<a id="xid-125B6C5E3630"></a>

# Reader Capability Model

## Purpose

This knowledge defines how the `editorial-ops` pack should represent assumed
reader capability before evaluating article clarity, omission, and pacing.

Reader experience is not only about audience identity.
It also depends on what the reader can already parse without extra support.

## Required Reader Capability Fields

- `reader_profile_id`
  - stable short label such as `zenn_learner` or `zenn_practitioner_web_ai`
- `domain_familiarity`
  - which topic families the reader already knows at a working level
- `implementation_depth`
  - whether the reader can follow code-level reasoning without extra scaffolding
- `operations_depth`
  - whether the reader can follow runtime, failure, and system-behavior reasoning
- `abstraction_tolerance`
  - whether the reader can follow conceptual discussion without diagram or code support
- `expected_explanatory_support`
  - what the article must provide for this reader to stay oriented

## Baseline Levels

### `learner`

- domain_familiarity:
  - basic tool and framework names may be known
- implementation_depth:
  - can follow simple examples but not dense implementation tradeoff discussion
- operations_depth:
  - do not assume TCP, process, queue, port, retry, or concurrency behavior
- abstraction_tolerance:
  - low to medium
- expected_explanatory_support:
  - define terms
  - explain why the problem matters
  - use concrete examples before abstraction

### `practitioner`

- domain_familiarity:
  - can follow day-to-day engineering topics in the target area
- implementation_depth:
  - can follow code and library tradeoffs
- operations_depth:
  - may follow practical failure stories, but low-level runtime and OS details should not be assumed
- abstraction_tolerance:
  - medium
- expected_explanatory_support:
  - provide one bridge from local code behavior to system behavior
  - qualify environment-dependent values
  - explain component role changes when multiple libraries or layers appear

### `specialist`

- domain_familiarity:
  - can follow the target technical area at deep working level
- implementation_depth:
  - high
- operations_depth:
  - high
- abstraction_tolerance:
  - high
- expected_explanatory_support:
  - minimal restatement
  - focus on edge cases, tradeoffs, and boundary decisions

## Zenn-Oriented Defaults

These are not official Zenn classifications.
They are working assumptions derived from public Zenn positioning and observed
topic bias.

### `zenn_learner`

- base_level: `learner`
- notes:
  - suitable when the article is introductory or tool-first

### `zenn_practitioner_web_ai`

- base_level: `practitioner`
- notes:
  - suitable default when the article targets Zenn readers interested in web development and AI-assisted engineering
  - do not assume deep knowledge of TCP, OS port behavior, or concurrency internals
  - do assume familiarity with normal implementation and library usage discussion

### `zenn_specialist`

- base_level: `specialist`
- notes:
  - use only when the article clearly targets an expert subcommunity

## Review Implications

- If the article jumps above the assumed `operations_depth`, flag missing bridge explanation.
- If the article uses multiple technical layers, flag missing role clarification when the reader cannot safely infer the shift.
- If the article depends on environment-specific values, require qualification unless the assumed reader is specialist and the scope is explicitly narrow.
- If the article omits concrete examples while `abstraction_tolerance` is low, flag likely reader drop-off.
