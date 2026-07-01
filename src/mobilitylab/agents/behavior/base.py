from __future__ import annotations

from typing import Protocol, runtime_checkable

from mobilitylab.agents.context import DecisionContext
from mobilitylab.agents.decisions import AgentDecision


@runtime_checkable
class BehaviorModel(Protocol):
    """Decision mechanism attached to a runtime agent."""

    @property
    def behavior_id(self) -> str: ...

    def decide(self, context: DecisionContext) -> AgentDecision: ...
