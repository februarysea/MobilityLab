from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable
from random import Random
from typing import Any

from mobilitylab.agents.agent import RuntimeAgent
from mobilitylab.agents.errors import AgentValidationError
from mobilitylab.core.entities import EntityId, State


class AgentSet:
    """Deterministic runtime collection for agents."""

    def __init__(self, agents: Iterable[RuntimeAgent] = ()) -> None:
        self._agents: dict[EntityId, RuntimeAgent] = {}
        for agent in agents:
            self.register(agent)

    def register(self, agent: RuntimeAgent) -> None:
        if agent.id in self._agents:
            msg = f"agent already registered: {agent.id}"
            raise AgentValidationError(msg)
        self._agents[agent.id] = agent

    def get(self, agent_id: EntityId) -> RuntimeAgent:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            msg = f"unknown agent: {agent_id}"
            raise KeyError(msg) from exc

    def contains(self, agent_id: EntityId) -> bool:
        return agent_id in self._agents

    def ids(self) -> tuple[EntityId, ...]:
        return tuple(sorted(self._agents, key=str))

    def values(self) -> tuple[RuntimeAgent, ...]:
        return tuple(self._agents[agent_id] for agent_id in self.ids())

    def select(self, predicate: Callable[[RuntimeAgent], bool]) -> AgentSet:
        return AgentSet(agent for agent in self.values() if predicate(agent))

    def by_type(self, agent_type: str) -> AgentSet:
        return self.select(lambda agent: agent.agent_type == agent_type)

    def groupby(
        self,
        key: Callable[[RuntimeAgent], Hashable],
    ) -> dict[Hashable, AgentSet]:
        groups: dict[Hashable, list[RuntimeAgent]] = {}
        for agent in self.values():
            groups.setdefault(key(agent), []).append(agent)
        return {group_key: AgentSet(values) for group_key, values in groups.items()}

    def do(self, method_name: str, *args: Any, **kwargs: Any) -> AgentSet:
        for agent in self.values():
            getattr(agent, method_name)(*args, **kwargs)
        return self

    def shuffle_do(
        self,
        method_name: str,
        rng: Random,
        *args: Any,
        **kwargs: Any,
    ) -> AgentSet:
        agents = list(self.values())
        rng.shuffle(agents)
        for agent in agents:
            getattr(agent, method_name)(*args, **kwargs)
        return self

    def snapshot_state(self) -> dict[str, State]:
        return {str(agent.id): agent.snapshot_state() for agent in self.values()}

    def __len__(self) -> int:
        return len(self._agents)
