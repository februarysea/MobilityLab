# Example Reports

This directory stores development-facing reports from running MobilityLab
examples. Reports preserve reproducible issues, observed behavior, and framework
gaps exposed by examples.

## Purpose

- Record what happened when an example was run.
- Preserve reproduction commands, commit information, expected behavior, and
  actual behavior.
- Track whether each issue belongs to the framework, the example, docs, or a
  missing feature.
- Provide a clear handoff document for later framework fixes.

## Naming

Use one report per example by default. Replace `/` in the example path with `-`:

```text
examples/basic/minimal_commute
-> docs/example-reports/basic-minimal-commute.md

examples/traffic_assignment/pigou_network
-> docs/example-reports/traffic-assignment-pigou-network.md
```

## Workflow

1. Read the example `README.md` and `SPEC.md`.
2. Run the documented command.
3. Write or update the example report using `TEMPLATE.md`.
4. Reproduce open issues before changing framework code when practical.
5. Fix the smallest correct layer, add tests for reusable behavior, and update
   the report.
6. Rerun the example and record verification.

## Status Values

- `open`: reported and not yet fixed
- `in-progress`: currently being investigated or fixed
- `fixed`: a fix has been implemented
- `verified`: the example was rerun and the issue no longer appears
- `deferred`: valid issue, intentionally postponed
- `wontfix`: not a bug or outside the current project scope

## Rules

- Keep user-facing tutorials in example `README.md` files.
- Keep development-facing run reports in this directory.
- Do not use reports as substitutes for ADRs. Architecture or data-contract
  decisions still belong in `docs/decisions/`.
- Do not use reports as substitutes for `CHANGELOG.md`. User-visible changes
  still belong under `## Unreleased`.
