from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from mobilitylab.agents.agent import RuntimeAgent
from mobilitylab.agents.behavior.base import BehaviorModel
from mobilitylab.agents.behavior.rule_based import RuleBasedBehavior
from mobilitylab.agents.cognition.state import CognitiveState
from mobilitylab.agents.plans import ActivityPlan, AgentPlan, PlanElement, TripPlan
from mobilitylab.agents.profile import AgentProfile
from mobilitylab.agents.runtime.agentset import AgentSet
from mobilitylab.agents.runtime.execution import (
    DecisionExecutor,
    SerialDecisionExecutor,
)
from mobilitylab.agents.runtime.system import (
    DEFAULT_AGENT_SYSTEM_ID,
    AgentSystem,
)
from mobilitylab.agents.state import AgentLifecycleStatus, AgentState
from mobilitylab.core.entities import EntityId, JsonValue
from mobilitylab.environment.spatial import LocationKind, LocationRef
from mobilitylab.environment.world import Environment
from mobilitylab.scenario.base import PreparedScenario
from mobilitylab.scenario.population import ActivitySpec, AgentSpec, PlanSpec


@dataclass(frozen=True, slots=True)
class AgentSystemBuilder:
    """Builds runtime agents from a prepared scenario population."""

    agent_system_id: EntityId = DEFAULT_AGENT_SYSTEM_ID
    default_mode: str = "walk"
    default_initial_location: LocationRef | None = None
    default_behavior_id: str = "rule_based"
    initial_decision_delay_seconds: int = 0
    cognition_behavior_ids: tuple[str, ...] = ("cognitive", "hybrid")
    decision_executor: DecisionExecutor = SerialDecisionExecutor()

    def build(
        self,
        scenario: PreparedScenario,
        environment: Environment,
        *,
        behavior_models: Mapping[str, BehaviorModel] | None = None,
    ) -> AgentSystem:
        behaviors = dict(behavior_models or {})
        behaviors.setdefault(
            "rule_based",
            RuleBasedBehavior(default_mode=self.default_mode),
        )
        initial_locations: dict[EntityId, LocationRef] = {}
        agents: list[RuntimeAgent] = []

        facility_ids = {
            facility.facility_id for facility in scenario.facilities.facilities
        }
        node_ids = {node.node_id for node in scenario.network.nodes}

        for agent_spec in scenario.population.agents:
            agent_id = EntityId(agent_spec.agent_id)
            behavior_id = self._behavior_id_for(agent_spec)
            behavior = behaviors.get(behavior_id)
            if behavior is None:
                behavior = behaviors[self.default_behavior_id]
            profile = self._profile_from_spec(agent_spec)
            selected_plan = self._selected_plan_from_spec(
                agent_spec,
                profile=profile,
                facility_ids=facility_ids,
                node_ids=node_ids,
            )
            state = self._state_from_spec(agent_spec)
            cognition_state = (
                CognitiveState()
                if behavior.behavior_id in self.cognition_behavior_ids
                else None
            )
            agents.append(
                RuntimeAgent(
                    id=agent_id,
                    agent_type=agent_spec.agent_type,
                    profile=profile,
                    state=state,
                    selected_plan=selected_plan,
                    behavior_model=behavior,
                    cognition_state=cognition_state,
                )
            )
            initial_location = self._initial_location_for(
                agent_spec,
                facility_ids=facility_ids,
                node_ids=node_ids,
            )
            if initial_location is not None:
                initial_locations[agent_id] = initial_location

        return AgentSystem(
            environment=environment,
            agents=AgentSet(agents),
            initial_locations=initial_locations,
            decision_executor=self.decision_executor,
            agent_system_id=self.agent_system_id,
            initial_decision_delay_seconds=self.initial_decision_delay_seconds,
        )

    def _behavior_id_for(self, agent_spec: AgentSpec) -> str:
        raw = agent_spec.attributes.get("behavior_id")
        if isinstance(raw, str) and raw != "":
            return raw
        if agent_spec.policy_id is not None:
            return agent_spec.policy_id
        return self.default_behavior_id

    def _profile_from_spec(self, agent_spec: AgentSpec) -> AgentProfile:
        raw = agent_spec.profile
        role = self._string_value(raw.get("role"), default=agent_spec.agent_type)
        return AgentProfile(
            role=role,
            demographics=self._mapping_value(raw.get("demographics")),
            preferences=self._mapping_value(raw.get("preferences")),
            mobility_access=self._string_tuple_value(raw.get("mobility_access")),
            constraints=self._mapping_value(raw.get("constraints")),
            attributes={
                key: value
                for key, value in raw.items()
                if key
                not in {
                    "role",
                    "demographics",
                    "preferences",
                    "mobility_access",
                    "constraints",
                }
            },
        )

    def _state_from_spec(self, agent_spec: AgentSpec) -> AgentState:
        initial_state = dict(agent_spec.initial_state)
        lifecycle_status = AgentLifecycleStatus.IDLE
        raw_status = initial_state.get("lifecycle_status")
        if isinstance(raw_status, str):
            lifecycle_status = AgentLifecycleStatus(raw_status)
        index = initial_state.get("current_plan_element_index", 0)
        return AgentState(
            lifecycle_status=lifecycle_status,
            current_plan_element_index=index if isinstance(index, int) else 0,
            attributes=initial_state,
        )

    def _selected_plan_from_spec(
        self,
        agent_spec: AgentSpec,
        *,
        profile: AgentProfile,
        facility_ids: set[str],
        node_ids: set[str],
    ) -> AgentPlan | None:
        if not agent_spec.plans:
            return None
        selected_plan = agent_spec.plans[0]
        return self._plan_from_spec(
            selected_plan,
            profile=profile,
            facility_ids=facility_ids,
            node_ids=node_ids,
        )

    def _plan_from_spec(
        self,
        plan_spec: PlanSpec,
        *,
        profile: AgentProfile,
        facility_ids: set[str],
        node_ids: set[str],
    ) -> AgentPlan:
        elements: list[PlanElement] = []
        mode = (
            profile.mobility_access[0] if profile.mobility_access else self.default_mode
        )
        for activity in plan_spec.activities:
            location = self._location_from_activity(
                activity,
                facility_ids=facility_ids,
                node_ids=node_ids,
            )
            if location is not None:
                elements.append(
                    TripPlan(
                        trip_id=f"trip-to-{activity.activity_id}",
                        destination=location,
                        mode=mode,
                    )
                )
            elements.append(
                ActivityPlan(
                    activity_id=activity.activity_id,
                    activity_type=activity.activity_type,
                    start_time=activity.start_time,
                    end_time=activity.end_time,
                    location=location,
                    attributes=activity.attributes,
                )
            )
        return AgentPlan(
            plan_id=plan_spec.plan_id,
            elements=tuple(elements),
            attributes=plan_spec.attributes,
        )

    def _location_from_activity(
        self,
        activity: ActivitySpec,
        *,
        facility_ids: set[str],
        node_ids: set[str],
    ) -> LocationRef | None:
        if activity.location_id is None:
            return None
        return self._location_from_id(
            activity.location_id,
            facility_ids=facility_ids,
            node_ids=node_ids,
        )

    def _initial_location_for(
        self,
        agent_spec: AgentSpec,
        *,
        facility_ids: set[str],
        node_ids: set[str],
    ) -> LocationRef | None:
        raw = (
            agent_spec.initial_state.get("location")
            or agent_spec.initial_state.get("initial_location")
            or agent_spec.initial_state.get("location_id")
        )
        if raw is None:
            return self.default_initial_location
        return self._location_from_value(
            raw,
            facility_ids=facility_ids,
            node_ids=node_ids,
        )

    def _location_from_value(
        self,
        raw: JsonValue,
        *,
        facility_ids: set[str],
        node_ids: set[str],
    ) -> LocationRef | None:
        if isinstance(raw, str):
            return self._location_from_id(
                raw,
                facility_ids=facility_ids,
                node_ids=node_ids,
            )
        if not isinstance(raw, Mapping):
            return None
        raw_id = raw.get("id")
        raw_kind = raw.get("kind")
        if not isinstance(raw_id, str):
            return None
        if raw_kind == LocationKind.NODE.value:
            return LocationRef.node(raw_id)
        if raw_kind == LocationKind.FACILITY.value:
            return LocationRef.facility(raw_id)
        if raw_kind == LocationKind.LINK.value:
            return LocationRef.link(raw_id)
        return self._location_from_id(
            raw_id,
            facility_ids=facility_ids,
            node_ids=node_ids,
        )

    def _location_from_id(
        self,
        location_id: str,
        *,
        facility_ids: set[str],
        node_ids: set[str],
    ) -> LocationRef:
        if location_id in facility_ids:
            return LocationRef.facility(location_id)
        if location_id in node_ids:
            return LocationRef.node(location_id)
        return LocationRef.facility(location_id)

    def _string_value(self, value: JsonValue, *, default: str) -> str:
        if isinstance(value, str) and value != "":
            return value
        return default

    def _string_tuple_value(self, value: JsonValue) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,)
        if isinstance(value, list):
            return tuple(item for item in value if isinstance(item, str))
        return ()

    def _mapping_value(self, value: JsonValue) -> Mapping[str, JsonValue]:
        if isinstance(value, Mapping):
            return value
        return {}
