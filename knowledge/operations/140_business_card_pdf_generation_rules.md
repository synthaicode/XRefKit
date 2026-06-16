<!-- xid: 9142A8CDCF76 -->
<a id="xid-9142A8CDCF76"></a>

# Business Card PDF Generation Rules

This fragment captures the reusable implementation rules from the Zenn article
about replacing Illustrator-based name-card operations with a CSV-to-PDF
pipeline.

## Operating Pattern

- Separate mutable employee data, semi-fixed business settings, rendering
  logic, and vendor template evidence.
- Let business-side operators update `employees.csv`; keep engineering
  ownership on layout logic, build pipeline, and print-readiness validation.
- Treat the print vendor template as the positional source of truth rather than
  approximating trim, bleed, and crop marks by eye.

## Recommended Layer Split

- mutable per-person data -> CSV
- semi-fixed company values such as address, colors, and labels -> TOML or
  similar config
- rendering and validation logic -> Python package / CLI
- print-vendor positional truth -> source PDF template
- release automation -> CI workflow that rebuilds all cards from controlled
  inputs

## Print-Readiness Rules

- Reproduce page size, bleed, and crop-mark positions from the vendor template
  exactly.
- If the template geometry is read from PDF with PyMuPDF and rendered with
  ReportLab, convert the coordinate system explicitly because PyMuPDF uses a
  top-origin Y axis and ReportLab uses a bottom-origin Y axis.
- Prefer measured extraction of crop-mark lines from the template PDF over
  manual hardcoding when the vendor template is the contractual print target.
- Produce CMYK-oriented output for commercial printing.
- When the rendering library cannot outline fonts directly, run a post-process
  step such as Ghostscript with font-output suppression and CMYK conversion.
- Keep a debuggable non-outlined path available when text-selectable PDFs help
  local verification.
- Expect generic SVG importers to fail on some logo features such as
  `linearGradient`; use a constrained custom parser or another controlled
  fallback when the logo rendering must match the brand asset exactly.

## Domain Constraints That Should Live In Code

- Enforce minimum font-size thresholds in code or runtime assertions.
- Avoid Light/Thin font weights for low-cost offset printing when stroke loss
  is a known physical risk.
- Keep print-specific rationale close to the constants or validation logic so
  it does not disappear into stale documentation.

## Automation Boundary

- `make build`-style full regeneration is appropriate for all-employee output.
- A filtered single-employee path is useful for local verification.
- CI should rebuild when controlled inputs such as employee CSV, config,
  assets, source code, or workflow definition change.
- Release the generated PDFs as a packaged artifact so the business-side owner
  can consume outputs without running the toolchain locally.

## Review And Quality Pattern

- Use separate review viewpoints for visual layout, implementation correctness,
  and print-domain constraints.
- Do not assume AI can infer physical print constraints from screen output
  alone.
- Keep human print-domain judgments explicit when they define acceptance
  boundaries such as minimum font size, acceptable weights, or vendor-specific
  submission requirements.

## Sources

- source_type: web
- source_url: https://zenn.dev/minedia/articles/business-card-pdf-generator
- captured_path: ../sources/web/zenn.dev/business-card-pdf-generator-2026-05-19.html
- captured_at: 2026-05-19
