# Example Reports

This directory stores issue-level development reports from running MobilityLab
examples. Reports preserve reproducible issues, observed behavior, and framework
gaps exposed by examples.

## Purpose

- Record one distinct issue exposed by an example run.
- Preserve reproduction commands, commit information, expected behavior, and
  actual behavior.
- Track whether the issue belongs to the framework, the example, docs, or a
  missing feature.
- Provide a clear handoff document for later framework fixes.

## Naming

Use one Markdown file per distinct issue. Group issue reports by example slug.
Replace `/` in the example path with `-`:

```text
examples/basic/minimal_commute
-> docs/example-reports/basic-minimal-commute/

examples/traffic_assignment/pigou_network
-> docs/example-reports/traffic-assignment-pigou-network/
```

Name each issue report with a stable issue id:

```text
docs/example-reports/basic-minimal-commute/EX-BASIC-MINCOMM-001.md
docs/example-reports/basic-minimal-commute/EX-BASIC-MINCOMM-002.md
docs/example-reports/traffic-assignment-pigou-network/EX-TA-PIGOU-001.md
```

If one run exposes multiple unrelated issues, create multiple files. If several
symptoms likely share the same root cause, keep them in one issue report.

## Workflow

1. Read the example `README.md` and `SPEC.md`.
2. Run the documented command.
3. Create one issue report per distinct issue using `TEMPLATE.md`.
4. Reproduce open issues before changing framework code when practical.
5. Fix the smallest correct layer, add tests for reusable behavior, and update
   the issue report.
6. Rerun the example and record verification in the issue report.

## Status Values

- `open`: reported and not yet fixed
- `in-progress`: currently being investigated or fixed
- `fixed`: a fix has been implemented
- `verified`: the example was rerun and the issue no longer appears
- `deferred`: valid issue, intentionally postponed
- `wontfix`: not a bug or outside the current project scope

## Rules

- Keep user-facing tutorials in example `README.md` files.
- Keep development-facing issue reports in this directory.
- Do not mix unrelated issues in one Markdown file.
- Do not use reports as substitutes for ADRs. Architecture or data-contract
  decisions still belong in `docs/decisions/`.
- Do not use reports as substitutes for `CHANGELOG.md`. User-visible changes
  still belong under `## Unreleased`.
