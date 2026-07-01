# 0012 Project Rename to MobilityLab

## Status

Accepted

## Context

The project started under the CampusSociety name when a campus-scale scenario
was the first intended testbed. The implementation direction has since shifted
toward a mobility-first experiment platform for transport benchmarks,
agent-based mobility simulation, LLM-enabled behavior policies, and public-data
scenario adapters.

The old name overemphasized the original campus scope and did not communicate
the broader mobility simulation platform direction.

## Decision

Rename the project to MobilityLab and the Python package to `mobilitylab`.

Use MobilityLab as the user-facing project name. Describe the project as an
experimental platform for traditional, agent-based, LLM-enabled, and hybrid
mobility and transportation simulation.

## Consequences

- Python imports use `mobilitylab.*`.
- Package metadata uses the `mobilitylab` distribution name.
- Schema identifiers and visualization artifacts use the `mobilitylab.*`
  namespace.
- Frontend package names, page titles, and local run-artifact environment
  variables use the MobilityLab name.
- Historical ADRs may still mention the original campus motivation when
  describing past context.
