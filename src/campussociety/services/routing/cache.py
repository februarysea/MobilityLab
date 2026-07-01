from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from campussociety.core.entities import JsonValue, State
from campussociety.environment.routing import Route, RouteRequest, RoutingService

if TYPE_CHECKING:
    from campussociety.environment.world import RuntimeWorld


@dataclass(slots=True)
class CachedRoutingService:
    """RoutingService wrapper with deterministic request/world-state cache keys."""

    backend: RoutingService
    include_world_state: bool = True
    _routes: dict[str, Route] = field(default_factory=dict, init=False)

    def route(self, request: RouteRequest, world: RuntimeWorld) -> Route:
        key = self._cache_key(request, world)
        cached = self._routes.get(key)
        if cached is not None:
            return cached
        route = self.backend.route(request, world)
        self._routes[key] = route
        return route

    @property
    def size(self) -> int:
        return len(self._routes)

    def clear(self) -> None:
        self._routes.clear()

    def _cache_key(self, request: RouteRequest, world: RuntimeWorld) -> str:
        record: State = {
            "request": request.to_record(),
            "world_state": (
                _world_route_state(world) if self.include_world_state else None
            ),
        }
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _world_route_state(world: RuntimeWorld) -> list[JsonValue]:
    return [
        {
            "link_id": link.link_id,
            "state": link.state.to_record(),
        }
        for link in world.network.links()
    ]
