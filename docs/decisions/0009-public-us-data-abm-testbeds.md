# 0009 Public U.S. Data ABM Testbeds

## Status

Accepted

## Context

The original project direction treated a campus-scale adapter as the first
testbed. In practice, campus-scale mobility, schedule, and facility data can be
hard to obtain, validate, and share.

The project needs early experiments that are reproducible, easier to audit, and
grounded in data that other researchers can obtain. U.S. public datasets provide
a stronger first path for classic ABM and mobility experiments, including
Census geography and demographics, LEHD/LODES home-work flows, NHTS travel
behavior priors, GTFS transit feeds, and EPA built-environment indicators.

## Decision

Use openly available U.S. public datasets as the initial testbed family.

Prioritize classic ABM and mobility experiments before domain-specific campus
implementation:

- Schelling-style residential sorting.
- LODES-informed commuting and departure-time simulation.
- NHTS-informed mode-choice and travel behavior experiments.
- Activity schedule simulation.
- Accessibility, transit service, road closure, facility disruption, or pricing
  interventions.

Keep the existing layered architecture. Public-data loaders and transformations
belong in scenario adapters and data services. Core simulation, agent runtime,
environment execution, experiments, visualization, and provider services remain
domain-neutral.

## Consequences

- Project guidance and README should describe public U.S. data ABM testbeds as
  the first implementation target.
- Test fixtures should use generic ABM or commuting names instead of
  campus-specific names.
- Data connector, schema validation, and scenario adapter work becomes a near
  term priority.
- Existing framework contracts remain valid because domain-specific assumptions
  were already kept outside the simulation core.
