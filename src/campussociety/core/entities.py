from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import NewType, Protocol, TypeAlias, runtime_checkable

EntityId = NewType("EntityId", str)

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
State: TypeAlias = dict[str, JsonValue]


@runtime_checkable
class Entity(Protocol):
    """Minimal entity contract owned by the simulation core."""

    @property
    def id(self) -> EntityId: ...

    def snapshot_state(self) -> State: ...


class DuplicateEntityError(ValueError):
    """Raised when an entity id is registered more than once."""


def copy_state(state: Mapping[str, JsonValue]) -> State:
    return deepcopy(dict(state))


class EntityRegistry:
    """Deterministic registry for simulation entities."""

    def __init__(self) -> None:
        self._entities: dict[EntityId, Entity] = {}

    def register(self, entity: Entity) -> None:
        if str(entity.id) == "":
            msg = "entity id must not be empty"
            raise ValueError(msg)
        if entity.id in self._entities:
            msg = f"entity already registered: {entity.id}"
            raise DuplicateEntityError(msg)
        self._entities[entity.id] = entity

    def unregister(self, entity_id: EntityId) -> Entity:
        try:
            return self._entities.pop(entity_id)
        except KeyError as exc:
            msg = f"unknown entity: {entity_id}"
            raise KeyError(msg) from exc

    def get(self, entity_id: EntityId) -> Entity:
        try:
            return self._entities[entity_id]
        except KeyError as exc:
            msg = f"unknown entity: {entity_id}"
            raise KeyError(msg) from exc

    def contains(self, entity_id: EntityId) -> bool:
        return entity_id in self._entities

    def ids(self) -> tuple[EntityId, ...]:
        return tuple(sorted(self._entities, key=str))

    def values(self) -> tuple[Entity, ...]:
        return tuple(self._entities[entity_id] for entity_id in self.ids())

    def snapshot(self) -> dict[str, State]:
        return {
            str(entity_id): copy_state(self._entities[entity_id].snapshot_state())
            for entity_id in self.ids()
        }

    def __len__(self) -> int:
        return len(self._entities)
