from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from heapq import heapify, heappop, heappush
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from mobilitylab.core.simulation import RunContext

ScheduledCallback: TypeAlias = Callable[["RunContext"], None]
QueueItem: TypeAlias = tuple[int, int, int, "ScheduledTask"]


@dataclass(slots=True)
class ScheduledTask:
    """Callback scheduled for deterministic execution."""

    time: int
    priority: int
    sequence: int
    callback: ScheduledCallback
    label: str | None = None
    cancelled: bool = False

    def cancel(self) -> bool:
        """Mark this task as cancelled.

        Returns true only when this call changed the task state.
        """
        if self.cancelled:
            return False
        self.cancelled = True
        return True


@dataclass(slots=True)
class RecurringTask:
    """Handle for a callback that schedules itself repeatedly."""

    interval_seconds: int
    label: str | None = None
    cancelled: bool = False
    _next_task: ScheduledTask | None = field(default=None, repr=False)

    @property
    def next_task(self) -> ScheduledTask | None:
        return self._next_task

    def set_next_task(self, task: ScheduledTask) -> None:
        self._next_task = task
        if self.cancelled:
            task.cancel()

    def cancel(self) -> bool:
        """Cancel future executions of this recurring task."""
        if self.cancelled:
            return False
        self.cancelled = True
        if self._next_task is not None:
            self._next_task.cancel()
        return True


class Scheduler:
    """Priority queue ordered by time, priority, and insertion sequence."""

    def __init__(self) -> None:
        self._queue: list[QueueItem] = []
        self._next_sequence = 0

    def schedule(
        self,
        time: int,
        callback: ScheduledCallback,
        *,
        priority: int = 0,
        label: str | None = None,
    ) -> ScheduledTask:
        if time < 0:
            msg = "scheduled time must be non-negative"
            raise ValueError(msg)
        scheduled = ScheduledTask(
            time=time,
            priority=priority,
            sequence=self._next_sequence,
            callback=callback,
            label=label,
        )
        heappush(self._queue, (time, priority, scheduled.sequence, scheduled))
        self._next_sequence += 1
        return scheduled

    def cancel(self, task: ScheduledTask) -> bool:
        return task.cancel()

    def pop_next(self) -> ScheduledTask | None:
        while self._queue:
            task = heappop(self._queue)[3]
            if not task.cancelled:
                return task
        return None

    def peek_next_time(self) -> int | None:
        self._discard_cancelled_head()
        if not self._queue:
            return None
        return self._queue[0][0]

    def pending(self) -> tuple[ScheduledTask, ...]:
        return tuple(item[3] for item in sorted(self._queue) if not item[3].cancelled)

    def pending_count(self) -> int:
        return len(self.pending())

    def has_pending(self) -> bool:
        return self.peek_next_time() is not None

    def compact(self) -> None:
        self._queue = [item for item in self._queue if not item[3].cancelled]
        heapify(self._queue)

    def clear(self) -> None:
        self._queue.clear()

    def _discard_cancelled_head(self) -> None:
        while self._queue and self._queue[0][3].cancelled:
            heappop(self._queue)
