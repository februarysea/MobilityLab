from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from mobilitylab.core.entities import JsonValue, copy_state


@dataclass(frozen=True, slots=True)
class ReplayStepBundle:
    """Events and UI hints for one replay time."""

    run_id: str
    time: int
    events: tuple[Mapping[str, JsonValue], ...] = ()
    previous_time: int | None = None
    next_time: int | None = None
    schema: str = "mobilitylab.visualization.replay_step_bundle.v1"

    def __post_init__(self) -> None:
        if self.run_id == "":
            msg = "run_id must not be empty"
            raise ValueError(msg)
        if self.time < 0:
            msg = "time must be non-negative"
            raise ValueError(msg)
        object.__setattr__(
            self,
            "events",
            tuple(copy_state(event) for event in self.events),
        )

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "time": self.time,
            "event_count": len(self.events),
            "previous_time": self.previous_time,
            "next_time": self.next_time,
            "events": [copy_state(event) for event in self.events],
        }


@dataclass(frozen=True, slots=True)
class ReplayTimeline:
    """Readonly replay timeline index backed by exported replay frames."""

    run_id: str
    frames: tuple[Mapping[str, JsonValue], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.run_id == "":
            msg = "run_id must not be empty"
            raise ValueError(msg)
        frames = tuple(sorted((copy_state(frame) for frame in self.frames), key=_time))
        object.__setattr__(self, "frames", frames)

    @classmethod
    def from_records(
        cls,
        records: tuple[Mapping[str, JsonValue], ...],
    ) -> ReplayTimeline:
        run_id = ""
        for record in records:
            raw_run_id = record.get("run_id")
            if isinstance(raw_run_id, str) and raw_run_id != "":
                run_id = raw_run_id
                break
        return cls(run_id=run_id, frames=records)

    @property
    def times(self) -> tuple[int, ...]:
        return tuple(_time(frame) for frame in self.frames)

    def bundle_at(self, time: int) -> ReplayStepBundle:
        times = self.times
        frame = next((item for item in self.frames if _time(item) == time), None)
        index = times.index(time) if time in times else None
        previous_time = times[index - 1] if index is not None and index > 0 else None
        next_time = (
            times[index + 1] if index is not None and index + 1 < len(times) else None
        )
        return ReplayStepBundle(
            run_id=self.run_id,
            time=time,
            events=_events(frame) if frame is not None else (),
            previous_time=previous_time,
            next_time=next_time,
        )

    def first_bundle(self) -> ReplayStepBundle | None:
        if not self.frames:
            return None
        return self.bundle_at(_time(self.frames[0]))


def _time(record: Mapping[str, JsonValue]) -> int:
    raw_time = record.get("time")
    return raw_time if isinstance(raw_time, int) else 0


def _events(record: Mapping[str, JsonValue]) -> tuple[Mapping[str, JsonValue], ...]:
    raw_events = record.get("events")
    if not isinstance(raw_events, list):
        return ()
    return tuple(event for event in raw_events if isinstance(event, dict))
