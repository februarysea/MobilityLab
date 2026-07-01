from __future__ import annotations

from dataclasses import dataclass

import pytest

from mobilitylab.core.entities import (
    DuplicateEntityError,
    EntityId,
    EntityRegistry,
    State,
)
from mobilitylab.core.events import Event, EventBus


@dataclass
class MutableEntity:
    id: EntityId
    value: int

    def snapshot_state(self) -> State:
        return {"value": self.value}


def test_entity_registry_rejects_duplicate_ids_and_snapshots_state() -> None:
    registry = EntityRegistry()
    entity = MutableEntity(id=EntityId("entity-1"), value=1)

    registry.register(entity)
    snapshot = registry.snapshot()
    entity.value = 2

    assert registry.ids() == (EntityId("entity-1"),)
    assert snapshot == {"entity-1": {"value": 1}}

    with pytest.raises(DuplicateEntityError):
        registry.register(entity)


def test_event_bus_records_events_and_notifies_subscribers() -> None:
    bus = EventBus()
    seen: list[str] = []

    def handler(event: Event) -> None:
        seen.append(event.topic)

    bus.subscribe("entity.updated", handler)
    emitted = bus.emit(
        Event(
            time=3,
            topic="entity.updated",
            payload={"value": 4},
            source=EntityId("entity-1"),
        )
    )

    assert seen == ["entity.updated"]
    assert emitted.to_record() == {
        "time": 3,
        "sequence": 1,
        "topic": "entity.updated",
        "schema_version": "core.event.v1",
        "payload": {"value": 4},
        "source": "entity-1",
    }
    assert bus.records() == (emitted.to_record(),)

    second = bus.emit(Event(time=4, topic="entity.updated"))
    assert second.sequence == 2

    bus.clear()
    reset = bus.emit(Event(time=5, topic="entity.updated"))
    assert reset.sequence == 1
