# Example Reports

This directory stores structured reports produced while running MobilityLab
examples. Reports are the handoff boundary between Example Agent sessions and
Framework Agent sessions.

## Purpose

- Record what happened when an example was run.
- Preserve reproduction commands, environment details, expected behavior, and
  actual behavior.
- Track whether each issue belongs to the framework, the example, docs, or a
  missing feature.
- Give Framework Agent sessions a precise repair queue.

## Naming

Use one report per example by default. Replace `/` in the example path with `-`:

```text
examples/basic/minimal_commute
-> docs/example-reports/basic-minimal-commute.md

examples/traffic_assignment/pigou_network
-> docs/example-reports/traffic-assignment-pigou-network.md
```

## Workflow

1. Example Agent reads the example `README.md` and `SPEC.md`.
2. Example Agent runs the documented command.
3. Example Agent writes or updates the example report using `TEMPLATE.md`.
4. Framework Agent reads the report and reproduces open issues.
5. Framework Agent fixes the smallest correct layer, adds tests, and updates the
   report.
6. Example Agent reruns the example and marks fixed issues as verified when
   appropriate.

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
