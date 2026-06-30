from __future__ import annotations

from dataclasses import dataclass

from campussociety.agents.context import DecisionContext
from campussociety.agents.decisions import (
    AgentDecision,
    NoOpDecision,
    StartActivityDecision,
    StartTripDecision,
    WaitDecision,
)
from campussociety.agents.plans import TripPlan
from campussociety.agents.state import AgentLifecycleStatus


@dataclass(frozen=True, slots=True)
class RuleBasedBehavior:
    """Deterministic plan-following behavior for traditional ABM baselines."""

    behavior_id: str = "rule_based"
    default_mode: str = "walk"

    def decide(self, context: DecisionContext) -> AgentDecision:
        state = context.state
        if state.lifecycle_status is AgentLifecycleStatus.TRAVELING:
            return NoOpDecision(
                agent_id=context.agent_id,
                reason="agent is already traveling",
            )
        if state.lifecycle_status is AgentLifecycleStatus.IN_ACTIVITY:
            if state.current_activity_end_time is not None:
                return WaitDecision(
                    agent_id=context.agent_id,
                    until_time=max(context.time, state.current_activity_end_time),
                    reason="agent is in activity",
                )
            return NoOpDecision(
                agent_id=context.agent_id,
                reason="agent is in an open-ended activity",
            )

        plan = context.selected_plan
        if plan is None:
            return NoOpDecision(agent_id=context.agent_id, reason="no selected plan")

        element = plan.element_at(state.current_plan_element_index)
        if element is None:
            return NoOpDecision(agent_id=context.agent_id, reason="plan completed")

        if isinstance(element, TripPlan):
            if (
                element.departure_time is not None
                and context.time < element.departure_time
            ):
                return WaitDecision(
                    agent_id=context.agent_id,
                    until_time=element.departure_time,
                    reason="waiting for planned departure",
                )
            return StartTripDecision(
                agent_id=context.agent_id,
                origin=element.origin,
                destination=element.destination,
                mode=element.mode or self.default_mode,
                departure_time=context.time,
                movement_id=element.trip_id,
                reason="starting planned trip",
                attributes=element.attributes,
            )

        if element.start_time is not None and context.time < element.start_time:
            return WaitDecision(
                agent_id=context.agent_id,
                until_time=element.start_time,
                reason="waiting for planned activity start",
            )
        if (
            element.location is not None
            and context.observation.location != element.location
        ):
            return StartTripDecision(
                agent_id=context.agent_id,
                destination=element.location,
                mode=self._mode_for_context(context),
                departure_time=context.time,
                movement_id=f"trip-to-{element.activity_id}",
                reason="moving to planned activity location",
            )
        return StartActivityDecision(
            agent_id=context.agent_id,
            activity_id=element.activity_id,
            activity_type=element.activity_type,
            location=element.location,
            start_time=context.time,
            end_time=element.end_time,
            reason="starting planned activity",
            attributes=element.attributes,
        )

    def _mode_for_context(self, context: DecisionContext) -> str:
        if context.profile.mobility_access:
            return context.profile.mobility_access[0]
        if context.observation.available_modes:
            return context.observation.available_modes[0]
        return self.default_mode
