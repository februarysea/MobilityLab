from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import TYPE_CHECKING, Protocol

from campussociety.core.entities import EntityId, JsonValue
from campussociety.environment._utils import (
    copy_json_mapping,
    require_non_empty,
    require_non_negative,
    require_positive,
)
from campussociety.environment.errors import RouteNotFoundError
from campussociety.environment.spatial import LocationRef

if TYPE_CHECKING:
    from campussociety.environment.network import TraversalEdge
    from campussociety.environment.world import RuntimeWorld


DEFAULT_MODE_SPEEDS_MPS: Mapping[str, float] = {
    "walk": 1.4,
    "bike": 4.2,
    "bus": 8.0,
    "vehicle": 8.0,
}
DEFAULT_SPEED_MPS = 1.4


@dataclass(frozen=True, slots=True)
class RouteRequest:
    """Readonly request for a route over the current runtime world."""

    origin: LocationRef
    destination: LocationRef
    mode: str
    departure_time: int
    agent_id: EntityId | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.mode, "mode")
        require_non_negative(self.departure_time, "departure_time")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "origin": self.origin.to_record(),
            "destination": self.destination.to_record(),
            "mode": self.mode,
            "departure_time": self.departure_time,
            "agent_id": None if self.agent_id is None else str(self.agent_id),
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class RouteLeg:
    """One traversed network link in a route."""

    link_id: str
    from_node_id: str
    to_node_id: str
    mode: str
    length_meters: float
    travel_time_seconds: int
    reversed: bool = False

    def __post_init__(self) -> None:
        require_non_empty(self.link_id, "link_id")
        require_non_empty(self.from_node_id, "from_node_id")
        require_non_empty(self.to_node_id, "to_node_id")
        require_non_empty(self.mode, "mode")
        require_non_negative(self.length_meters, "length_meters")
        require_non_negative(self.travel_time_seconds, "travel_time_seconds")

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "link_id": self.link_id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "mode": self.mode,
            "length_meters": self.length_meters,
            "travel_time_seconds": self.travel_time_seconds,
            "reversed": self.reversed,
        }


@dataclass(frozen=True, slots=True)
class Route:
    """Deterministic route response used by the movement kernel."""

    request: RouteRequest
    legs: tuple[RouteLeg, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "legs", tuple(self.legs))
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    @property
    def total_length_meters(self) -> float:
        return sum(leg.length_meters for leg in self.legs)

    @property
    def total_travel_time_seconds(self) -> int:
        return sum(leg.travel_time_seconds for leg in self.legs)

    @property
    def arrival_time(self) -> int:
        return self.request.departure_time + self.total_travel_time_seconds

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "request": self.request.to_record(),
            "legs": [leg.to_record() for leg in self.legs],
            "total_length_meters": self.total_length_meters,
            "total_travel_time_seconds": self.total_travel_time_seconds,
            "arrival_time": self.arrival_time,
            "metadata": copy_json_mapping(self.metadata),
        }


class RoutingService(Protocol):
    """Route calculation contract.

    Implementations must not mutate the runtime world.
    """

    def route(self, request: RouteRequest, world: RuntimeWorld) -> Route: ...


class SimpleNetworkRouter:
    """Deterministic shortest-travel-time router over RuntimeNetwork."""

    def __init__(
        self,
        *,
        default_mode_speeds_mps: Mapping[str, float] | None = None,
    ) -> None:
        self._default_mode_speeds_mps = dict(
            default_mode_speeds_mps or DEFAULT_MODE_SPEEDS_MPS
        )
        for mode, speed in self._default_mode_speeds_mps.items():
            require_non_empty(mode, "mode")
            require_positive(speed, "speed")

    def route(self, request: RouteRequest, world: RuntimeWorld) -> Route:
        origin_node_id = world.resolve_location_node(request.origin)
        destination_node_id = world.resolve_location_node(
            request.destination,
            use_destination=True,
        )
        if origin_node_id == destination_node_id:
            return Route(request=request)

        path = self._shortest_path(
            request,
            world,
            origin_node_id=origin_node_id,
            destination_node_id=destination_node_id,
        )
        legs = tuple(self._edge_to_leg(edge, request, world) for edge in path)
        return Route(request=request, legs=legs)

    def default_speed_for_mode(self, mode: str) -> float:
        return self._default_mode_speeds_mps.get(mode, DEFAULT_SPEED_MPS)

    def _shortest_path(
        self,
        request: RouteRequest,
        world: RuntimeWorld,
        *,
        origin_node_id: str,
        destination_node_id: str,
    ) -> tuple[TraversalEdge, ...]:
        heap: list[tuple[int, int, str, int, tuple[TraversalEdge, ...]]] = []
        counter = 0
        best_cost: dict[str, int] = {origin_node_id: 0}
        heappush(heap, (0, 0, origin_node_id, counter, ()))

        while heap:
            cost, steps, node_id, _sequence, path = heappop(heap)
            if cost != best_cost.get(node_id):
                continue
            if node_id == destination_node_id:
                return path

            for edge in world.network.outgoing_edges(node_id, request.mode):
                link = world.network.get_link(edge.link_id)
                travel_time = link.travel_time_seconds(
                    request.mode,
                    self.default_speed_for_mode(request.mode),
                )
                next_cost = cost + travel_time
                if next_cost >= best_cost.get(edge.to_node_id, 10**18):
                    continue
                best_cost[edge.to_node_id] = next_cost
                counter += 1
                heappush(
                    heap,
                    (
                        next_cost,
                        steps + 1,
                        edge.to_node_id,
                        counter,
                        (*path, edge),
                    ),
                )

        msg = (
            "no route found: "
            f"{origin_node_id} -> {destination_node_id} by {request.mode}"
        )
        raise RouteNotFoundError(msg)

    def _edge_to_leg(
        self,
        edge: TraversalEdge,
        request: RouteRequest,
        world: RuntimeWorld,
    ) -> RouteLeg:
        link = world.network.get_link(edge.link_id)
        return RouteLeg(
            link_id=edge.link_id,
            from_node_id=edge.from_node_id,
            to_node_id=edge.to_node_id,
            mode=request.mode,
            length_meters=link.length_meters,
            travel_time_seconds=link.travel_time_seconds(
                request.mode,
                self.default_speed_for_mode(request.mode),
            ),
            reversed=edge.reversed,
        )
