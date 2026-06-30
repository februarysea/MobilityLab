from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TypeAlias, cast

from campussociety.agents.agent import RuntimeAgent
from campussociety.agents.context import DecisionContext
from campussociety.agents.decisions import (
    AgentDecision,
    AgentDecisionType,
    CommunicateDecision,
    EndActivityDecision,
    NoOpDecision,
    StartActivityDecision,
    StartTripDecision,
    WaitDecision,
)
from campussociety.agents.errors import AgentDecisionError
from campussociety.agents.runtime.agentset import AgentSet
from campussociety.agents.state import AgentLifecycleStatus
from campussociety.core.entities import EntityId, JsonValue, State
from campussociety.core.events import Event
from campussociety.core.scheduler import ScheduledTask
from campussociety.core.simulation import RunContext
from campussociety.environment.movement import MovementIntent
from campussociety.environment.observation import ObservationRequest
from campussociety.environment.spatial import LocationRef
from campussociety.environment.world import Environment

AgentSystemInitializer: TypeAlias = Callable[[RunContext], None]
DEFAULT_AGENT_SYSTEM_ID = EntityId("agents")


@dataclass(slots=True)
class AgentSystem:
    """Runtime manager that activates agents and executes decisions."""

    environment: Environment
    agents: AgentSet
    initial_locations: Mapping[EntityId, LocationRef] = field(default_factory=dict)
    agent_system_id: EntityId = DEFAULT_AGENT_SYSTEM_ID
    initial_decision_delay_seconds: int = 0
    _context: RunContext | None = field(default=None, init=False, repr=False)
    _pending_activations: dict[EntityId, ScheduledTask] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _activity_end_tasks: dict[EntityId, ScheduledTask] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _next_movement_sequence: int = field(default=1, init=False, repr=False)
    _subscribed: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self.initial_locations = dict(self.initial_locations)

    @property
    def id(self) -> EntityId:
        return self.agent_system_id

    def create_initializer(
        self,
        *,
        register_entity: bool = True,
    ) -> AgentSystemInitializer:
        def initialize(context: RunContext) -> None:
            self.install(context, register_entity=register_entity)

        return initialize

    def install(
        self,
        context: RunContext,
        *,
        register_entity: bool = True,
    ) -> None:
        self._context = context
        if register_entity:
            context.entities.register(self)
        self._install_initial_locations()
        if not self._subscribed:
            context.event_bus.subscribe("movement.arrived", self._on_movement_arrived)
            context.event_bus.subscribe("movement.failed", self._on_movement_failed)
            self._subscribed = True
        for agent in self.agents.values():
            self._schedule_activation(
                agent.id,
                context,
                time=context.clock.time + self.initial_decision_delay_seconds,
            )
        context.emit(
            "agents.initialized",
            {
                "agent_system_id": str(self.id),
                "agent_count": len(self.agents),
            },
            source=self.id if register_entity else None,
        )

    def activate_agent(self, agent_id: EntityId, context: RunContext) -> AgentDecision:
        agent = self.agents.get(agent_id)
        if agent.state.lifecycle_status in {
            AgentLifecycleStatus.COMPLETED,
            AgentLifecycleStatus.FAILED,
        }:
            inactive_decision = NoOpDecision(
                agent_id=agent_id,
                reason="agent is not active",
            )
            self._emit_decision(inactive_decision, context, agent=agent)
            return inactive_decision

        observation = self.environment.observe(
            ObservationRequest(agent_id=agent_id),
            context,
        )
        decision_context = DecisionContext(
            agent_id=agent.id,
            time=context.clock.time,
            profile=agent.profile,
            state=agent.state,
            selected_plan=agent.selected_plan,
            observation=observation,
            rng=context.rng,
            recent_events=context.event_bus.events()[-10:],
            cognition_state=agent.cognition_state,
        )
        decision = agent.decide(decision_context)
        self._emit_decision(decision, context, agent=agent)
        self.execute_decision(decision, context)
        return decision

    def execute_decision(
        self,
        decision: AgentDecision,
        context: RunContext,
    ) -> None:
        agent = self.agents.get(decision.agent_id)
        if isinstance(decision, NoOpDecision):
            if self._plan_completed(agent):
                agent.state.lifecycle_status = AgentLifecycleStatus.COMPLETED
            return
        if isinstance(decision, WaitDecision):
            if decision.until_time < context.clock.time:
                msg = (
                    "cannot wait until a past time: "
                    f"{decision.until_time} < {context.clock.time}"
                )
                raise AgentDecisionError(msg)
            agent.state.lifecycle_status = AgentLifecycleStatus.WAITING
            self._schedule_activation(
                decision.agent_id,
                context,
                time=decision.until_time,
            )
            return
        if isinstance(decision, StartActivityDecision):
            self._start_activity(agent, decision, context)
            return
        if isinstance(decision, EndActivityDecision):
            self._end_activity(
                agent,
                context,
                requested_activity_id=decision.activity_id,
            )
            return
        if isinstance(decision, StartTripDecision):
            self._start_trip(agent, decision, context)
            return
        if isinstance(decision, CommunicateDecision):
            context.emit("agent.message.sent", decision.to_record(), source=agent.id)
            return
        if decision.decision_type is AgentDecisionType.REPLAN:
            context.emit(
                "agent.replan.requested",
                decision.to_record(),
                source=agent.id,
            )
            return

        msg = f"unsupported agent decision: {decision.decision_type}"
        raise AgentDecisionError(msg)

    def snapshot_state(self) -> State:
        return {
            "entity_type": "agent_system",
            "schema": "campussociety.agents.system.v1",
            "agent_count": len(self.agents),
            "agents": cast(JsonValue, self.agents.snapshot_state()),
        }

    def _install_initial_locations(self) -> None:
        for agent_id, location in self.initial_locations.items():
            if not self.environment.world.has_agent_location(agent_id):
                self.environment.world.set_agent_location(agent_id, location)

    def _schedule_activation(
        self,
        agent_id: EntityId,
        context: RunContext,
        *,
        time: int,
    ) -> ScheduledTask:
        if time < context.clock.time:
            msg = f"cannot schedule agent activation in the past: {time}"
            raise AgentDecisionError(msg)
        existing = self._pending_activations.get(agent_id)
        if existing is not None and not existing.cancelled:
            existing.cancel()

        def activate(inner_context: RunContext) -> None:
            self._pending_activations.pop(agent_id, None)
            self.activate_agent(agent_id, inner_context)

        task = context.schedule_at(
            time,
            activate,
            label=f"agent.activate:{agent_id}",
        )
        self._pending_activations[agent_id] = task
        return task

    def _emit_decision(
        self,
        decision: AgentDecision,
        context: RunContext,
        *,
        agent: RuntimeAgent,
    ) -> None:
        context.emit("agent.decision", decision.to_record(), source=agent.id)

    def _start_activity(
        self,
        agent: RuntimeAgent,
        decision: StartActivityDecision,
        context: RunContext,
    ) -> None:
        agent.state.lifecycle_status = AgentLifecycleStatus.IN_ACTIVITY
        agent.state.current_activity_id = decision.activity_id
        agent.state.current_activity_end_time = decision.end_time
        agent.state.current_trip_id = None
        agent.state.current_plan_element_index += 1
        context.emit("activity.started", decision.to_record(), source=agent.id)

        if decision.end_time is not None:
            self._schedule_activity_end(agent.id, context, time=decision.end_time)

    def _schedule_activity_end(
        self,
        agent_id: EntityId,
        context: RunContext,
        *,
        time: int,
    ) -> ScheduledTask:
        end_time = max(time, context.clock.time)
        existing = self._activity_end_tasks.get(agent_id)
        if existing is not None and not existing.cancelled:
            existing.cancel()

        def end_activity(inner_context: RunContext) -> None:
            self._activity_end_tasks.pop(agent_id, None)
            agent = self.agents.get(agent_id)
            self._end_activity(agent, inner_context)
            self._schedule_activation(
                agent_id,
                inner_context,
                time=inner_context.clock.time,
            )

        task = context.schedule_at(
            end_time,
            end_activity,
            label=f"agent.activity.end:{agent_id}",
        )
        self._activity_end_tasks[agent_id] = task
        return task

    def _end_activity(
        self,
        agent: RuntimeAgent,
        context: RunContext,
        *,
        requested_activity_id: str | None = None,
    ) -> None:
        activity_id = agent.state.current_activity_id
        if requested_activity_id is not None and activity_id != requested_activity_id:
            msg = (
                "cannot end non-current activity: "
                f"{requested_activity_id} != {activity_id}"
            )
            raise AgentDecisionError(msg)
        if activity_id is None:
            return
        context.emit(
            "activity.ended",
            {
                "agent_id": str(agent.id),
                "activity_id": activity_id,
            },
            source=agent.id,
        )
        agent.state.lifecycle_status = AgentLifecycleStatus.IDLE
        agent.state.current_activity_id = None
        agent.state.current_activity_end_time = None

    def _start_trip(
        self,
        agent: RuntimeAgent,
        decision: StartTripDecision,
        context: RunContext,
    ) -> None:
        if (
            decision.departure_time is not None
            and decision.departure_time > context.clock.time
        ):
            agent.state.lifecycle_status = AgentLifecycleStatus.WAITING
            self._schedule_activation(
                decision.agent_id,
                context,
                time=decision.departure_time,
            )
            return

        movement_id = decision.movement_id or self._new_movement_id(agent.id)
        agent.state.lifecycle_status = AgentLifecycleStatus.TRAVELING
        agent.state.current_trip_id = movement_id
        agent.state.current_activity_id = None
        agent.state.current_activity_end_time = None
        agent.state.current_plan_element_index += 1
        context.emit(
            "trip.requested",
            {
                **decision.to_record(),
                "movement_id": movement_id,
            },
            source=agent.id,
        )
        self.environment.start_movement(
            MovementIntent(
                agent_id=agent.id,
                origin=decision.origin,
                destination=decision.destination,
                mode=decision.mode,
                movement_id=movement_id,
                departure_time=context.clock.time,
                attributes=decision.attributes,
            ),
            context,
        )

    def _new_movement_id(self, agent_id: EntityId) -> str:
        movement_id = f"agent-movement:{agent_id}:{self._next_movement_sequence}"
        self._next_movement_sequence += 1
        return movement_id

    def _on_movement_arrived(self, event: Event) -> None:
        context = self._require_context()
        agent_id = self._agent_id_from_event(event)
        if agent_id is None or not self.agents.contains(agent_id):
            return
        agent = self.agents.get(agent_id)
        agent.state.lifecycle_status = AgentLifecycleStatus.IDLE
        agent.state.current_trip_id = None
        context.emit(
            "trip.arrived",
            {
                "agent_id": str(agent_id),
                "movement_id": event.payload.get("movement_id"),
                "destination": event.payload.get("destination"),
            },
            source=agent.id,
        )
        self._schedule_activation(agent_id, context, time=context.clock.time)

    def _on_movement_failed(self, event: Event) -> None:
        context = self._require_context()
        agent_id = self._agent_id_from_event(event)
        if agent_id is None or not self.agents.contains(agent_id):
            return
        agent = self.agents.get(agent_id)
        agent.state.lifecycle_status = AgentLifecycleStatus.FAILED
        context.emit(
            "agent.failed",
            {
                "agent_id": str(agent_id),
                "reason": event.payload.get("reason"),
            },
            source=agent.id,
        )

    def _agent_id_from_event(self, event: Event) -> EntityId | None:
        raw_agent_id = event.payload.get("agent_id")
        if not isinstance(raw_agent_id, str):
            return None
        return EntityId(raw_agent_id)

    def _require_context(self) -> RunContext:
        if self._context is None:
            msg = "agent system has not been installed"
            raise AgentDecisionError(msg)
        return self._context

    def _plan_completed(self, agent: RuntimeAgent) -> bool:
        if agent.selected_plan is None:
            return True
        return agent.state.current_plan_element_index >= agent.selected_plan.size
