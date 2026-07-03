# MobilityLab Agent Roles

This directory defines session-level role contracts for MobilityLab development.
Use these files when starting or reassigning a Codex session to a focused role.

## Available Roles

- `example-agent.md`: runs examples, records failures, and writes structured
  reports. It does not modify framework code by default.
- `framework-agent.md`: reads example reports, reproduces open issues, fixes the
  smallest correct framework layer, adds tests, and updates the report.

## How To Use

For an Example Agent session:

```text
Please work as the MobilityLab Example Agent.
Read AGENTS.md and .agents/example-agent.md first.
Run examples/basic/minimal_commute and write or update
docs/example-reports/basic-minimal-commute.md.
Do not modify framework code.
```

For a Framework Agent session:

```text
Please work as the MobilityLab Framework Agent.
Read AGENTS.md, .agents/framework-agent.md, and the relevant
docs/example-reports/*.md report first.
Reproduce open issues, fix the smallest correct layer, add tests, and update the
report.
```

For an already-open session, explicitly reset the role:

```text
From now on, work as the MobilityLab Example Agent.
Read AGENTS.md and .agents/example-agent.md. If previous context conflicts with
this role, follow .agents/example-agent.md.
```

## Rules

- Role files add task-specific constraints; `AGENTS.md` remains the project
  source of truth for architecture and development rules.
- Keep role sessions focused. Avoid mixing example discovery and framework
  repair in the same session unless explicitly requested.
- Use `docs/example-reports/` as the handoff boundary between Example Agent and
  Framework Agent.
