# MobilityLab Docs

This directory stores project records that are useful for architecture,
development, and example-driven iteration.

## Sections

- `decisions/`: Architecture Decision Records for long-term architecture,
  data-contract, experiment-methodology, and backend strategy decisions.
- `example-reports/`: issue-level development reports from running examples,
  including reproduction commands, observed behavior, framework gaps, and
  verification notes.

## Rules

- Use `docs/decisions/` when a decision changes long-term interfaces,
  architecture boundaries, data contracts, experiment methodology, or
  provider/backend strategy.
- Use `docs/example-reports/` when an example run exposes bugs, unclear
  behavior, missing framework capabilities, or verification results. Use one
  Markdown file per distinct issue.
- Keep user-facing example tutorials in `examples/**/README.md`.
- Keep chronological user-visible changes in `CHANGELOG.md`.
