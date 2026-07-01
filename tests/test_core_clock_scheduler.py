from __future__ import annotations

import pytest

from mobilitylab.core.clock import (
    SECONDS_PER_DAY,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
    Clock,
)
from mobilitylab.core.scheduler import Scheduler


def test_core_time_constants_use_integer_seconds() -> None:
    assert SECONDS_PER_MINUTE == 60
    assert SECONDS_PER_HOUR == 3_600
    assert SECONDS_PER_DAY == 86_400


def test_clock_advances_monotonically() -> None:
    clock = Clock(start_time=2)

    assert clock.time == 2
    assert clock.advance_by(3) == 5
    assert clock.advance_to(5) == 5

    with pytest.raises(ValueError, match="backwards"):
        clock.advance_to(4)


def test_scheduler_orders_by_time_priority_and_sequence() -> None:
    scheduler = Scheduler()

    def noop() -> None:
        return None

    scheduler.schedule(3, lambda _context: noop(), priority=0, label="third")
    scheduler.schedule(1, lambda _context: noop(), priority=1, label="second")
    scheduler.schedule(1, lambda _context: noop(), priority=0, label="first")
    scheduler.schedule(1, lambda _context: noop(), priority=1, label="stable")

    labels: list[str | None] = []
    while scheduler.has_pending():
        scheduled = scheduler.pop_next()
        assert scheduled is not None
        labels.append(scheduled.label)

    assert labels == ["first", "second", "stable", "third"]


def test_scheduler_lazily_skips_cancelled_tasks() -> None:
    scheduler = Scheduler()

    first = scheduler.schedule(1, lambda _context: None, label="cancelled")
    second = scheduler.schedule(2, lambda _context: None, label="active")

    assert scheduler.cancel(first) is True
    assert scheduler.cancel(first) is False
    assert first.cancelled is True
    assert scheduler.pending_count() == 1
    assert scheduler.peek_next_time() == 2

    scheduled = scheduler.pop_next()
    assert scheduled == second
    assert scheduler.pop_next() is None


def test_scheduler_compacts_cancelled_tasks() -> None:
    scheduler = Scheduler()

    scheduler.schedule(1, lambda _context: None, label="active")
    cancelled = scheduler.schedule(2, lambda _context: None, label="cancelled")
    scheduler.schedule(3, lambda _context: None, label="later")

    cancelled.cancel()
    assert len(scheduler._queue) == 3  # noqa: SLF001

    scheduler.compact()

    assert len(scheduler._queue) == 2  # noqa: SLF001
    assert [task.label for task in scheduler.pending()] == ["active", "later"]
