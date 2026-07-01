from __future__ import annotations

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR


class Clock:
    """Monotonic integer simulation clock.

    Core simulation time is represented as integer seconds.
    """

    __slots__ = ("_start_time", "_time")

    def __init__(self, start_time: int = 0) -> None:
        if start_time < 0:
            msg = "start_time must be non-negative"
            raise ValueError(msg)
        self._start_time = start_time
        self._time = start_time

    @property
    def start_time(self) -> int:
        return self._start_time

    @property
    def time(self) -> int:
        return self._time

    def advance_to(self, time: int) -> int:
        if time < self._time:
            msg = f"clock cannot move backwards from {self._time} to {time}"
            raise ValueError(msg)
        self._time = time
        return self._time

    def advance_by(self, delta: int) -> int:
        if delta < 0:
            msg = "delta must be non-negative"
            raise ValueError(msg)
        return self.advance_to(self._time + delta)

    def reset(self) -> None:
        self._time = self._start_time
