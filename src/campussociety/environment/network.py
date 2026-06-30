from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from math import ceil

from campussociety.core.entities import JsonValue
from campussociety.environment._utils import (
    copy_json_mapping,
    optional_bool,
    optional_float,
    require_non_empty,
    require_non_negative,
)
from campussociety.environment.errors import EnvironmentValidationError
from campussociety.environment.spatial import Position
from campussociety.scenario.world import NetworkSpec


@dataclass(frozen=True, slots=True)
class RuntimeNode:
    """Runtime network node."""

    node_id: str
    position: Position | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.node_id, "node_id")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "node_id": self.node_id,
            "position": None if self.position is None else self.position.to_record(),
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(slots=True)
class LinkState:
    """Mutable runtime state for a network link."""

    open: bool = True
    speed_mps: float | None = None
    cost_multiplier: float = 1.0
    occupancy: int = 0

    def __post_init__(self) -> None:
        if self.speed_mps is not None and self.speed_mps <= 0:
            msg = "speed_mps must be positive when set"
            raise EnvironmentValidationError(msg)
        require_positive_cost_multiplier(self.cost_multiplier)
        require_non_negative(self.occupancy, "occupancy")

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "open": self.open,
            "speed_mps": self.speed_mps,
            "cost_multiplier": self.cost_multiplier,
            "occupancy": self.occupancy,
        }


def require_positive_cost_multiplier(value: float) -> None:
    if value <= 0:
        msg = "cost_multiplier must be positive"
        raise EnvironmentValidationError(msg)


@dataclass(slots=True)
class RuntimeLink:
    """Runtime network link with static supply and mutable state."""

    link_id: str
    from_node_id: str
    to_node_id: str
    length_meters: float = 0.0
    allowed_modes: tuple[str, ...] = ()
    bidirectional: bool = False
    base_speed_mps: float | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)
    state: LinkState = field(default_factory=LinkState)

    def __post_init__(self) -> None:
        require_non_empty(self.link_id, "link_id")
        require_non_empty(self.from_node_id, "from_node_id")
        require_non_empty(self.to_node_id, "to_node_id")
        require_non_negative(self.length_meters, "length_meters")
        if self.base_speed_mps is not None and self.base_speed_mps <= 0:
            msg = "base_speed_mps must be positive when set"
            raise EnvironmentValidationError(msg)
        self.allowed_modes = tuple(self.allowed_modes)
        self.attributes = copy_json_mapping(self.attributes)

    def allows_mode(self, mode: str) -> bool:
        return not self.allowed_modes or mode in self.allowed_modes

    def is_traversable(self, mode: str) -> bool:
        return self.state.open and self.allows_mode(mode)

    def travel_time_seconds(self, mode: str, default_speed_mps: float) -> int:
        if not self.is_traversable(mode):
            msg = f"link is not traversable for mode {mode}: {self.link_id}"
            raise EnvironmentValidationError(msg)
        speed_mps = self.state.speed_mps or self.base_speed_mps or default_speed_mps
        if speed_mps <= 0:
            msg = "travel speed must be positive"
            raise EnvironmentValidationError(msg)
        if self.length_meters == 0:
            return 0
        raw_seconds = self.length_meters / speed_mps
        return max(1, ceil(raw_seconds * self.state.cost_multiplier))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "link_id": self.link_id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "length_meters": self.length_meters,
            "allowed_modes": list(self.allowed_modes),
            "bidirectional": self.bidirectional,
            "base_speed_mps": self.base_speed_mps,
            "attributes": copy_json_mapping(self.attributes),
            "state": self.state.to_record(),
        }


@dataclass(frozen=True, slots=True)
class TraversalEdge:
    """Directed traversal view over a runtime link."""

    link_id: str
    from_node_id: str
    to_node_id: str
    reversed: bool = False

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "link_id": self.link_id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "reversed": self.reversed,
        }


class RuntimeNetwork:
    """Mutable runtime network state and deterministic network queries."""

    def __init__(
        self,
        nodes: Iterable[RuntimeNode] = (),
        links: Iterable[RuntimeLink] = (),
        *,
        coordinate_system: str | None = None,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> None:
        self.coordinate_system = coordinate_system
        self.metadata = copy_json_mapping(metadata or {})
        self._nodes: dict[str, RuntimeNode] = {}
        self._links: dict[str, RuntimeLink] = {}
        self._outgoing: dict[str, list[TraversalEdge]] = defaultdict(list)
        for node in nodes:
            self.add_node(node)
        for link in links:
            self.add_link(link)

    @classmethod
    def from_spec(cls, spec: NetworkSpec) -> RuntimeNetwork:
        nodes = tuple(
            RuntimeNode(
                node_id=node.node_id,
                position=(
                    Position(node.x, node.y)
                    if node.x is not None and node.y is not None
                    else None
                ),
                attributes=node.attributes,
            )
            for node in spec.nodes
        )
        links = tuple(
            RuntimeLink(
                link_id=link.link_id,
                from_node_id=link.from_node_id,
                to_node_id=link.to_node_id,
                length_meters=0.0 if link.length_meters is None else link.length_meters,
                allowed_modes=link.allowed_modes,
                bidirectional=optional_bool(
                    link.attributes,
                    "bidirectional",
                    default=False,
                ),
                base_speed_mps=optional_float(link.attributes, "base_speed_mps"),
                attributes=link.attributes,
            )
            for link in spec.links
        )
        return cls(
            nodes,
            links,
            coordinate_system=spec.coordinate_system,
            metadata=spec.metadata,
        )

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def link_count(self) -> int:
        return len(self._links)

    def add_node(self, node: RuntimeNode) -> None:
        if node.node_id in self._nodes:
            msg = f"network node already exists: {node.node_id}"
            raise EnvironmentValidationError(msg)
        self._nodes[node.node_id] = node

    def add_link(self, link: RuntimeLink) -> None:
        if link.link_id in self._links:
            msg = f"network link already exists: {link.link_id}"
            raise EnvironmentValidationError(msg)
        if link.from_node_id not in self._nodes:
            msg = f"link references unknown from_node_id: {link.from_node_id}"
            raise EnvironmentValidationError(msg)
        if link.to_node_id not in self._nodes:
            msg = f"link references unknown to_node_id: {link.to_node_id}"
            raise EnvironmentValidationError(msg)
        self._links[link.link_id] = link
        self._index_link(link)

    def contains_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def contains_link(self, link_id: str) -> bool:
        return link_id in self._links

    def get_node(self, node_id: str) -> RuntimeNode:
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            msg = f"unknown network node: {node_id}"
            raise KeyError(msg) from exc

    def get_link(self, link_id: str) -> RuntimeLink:
        try:
            return self._links[link_id]
        except KeyError as exc:
            msg = f"unknown network link: {link_id}"
            raise KeyError(msg) from exc

    def node_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._nodes))

    def link_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._links))

    def nodes(self) -> tuple[RuntimeNode, ...]:
        return tuple(self._nodes[node_id] for node_id in self.node_ids())

    def links(self) -> tuple[RuntimeLink, ...]:
        return tuple(self._links[link_id] for link_id in self.link_ids())

    def outgoing_edges(self, node_id: str, mode: str) -> tuple[TraversalEdge, ...]:
        if node_id not in self._nodes:
            msg = f"unknown network node: {node_id}"
            raise KeyError(msg)
        return tuple(
            edge
            for edge in sorted(
                self._outgoing.get(node_id, ()),
                key=lambda item: (item.to_node_id, item.link_id, item.reversed),
            )
            if self.get_link(edge.link_id).is_traversable(mode)
        )

    def set_link_open(self, link_id: str, open_: bool) -> None:
        self.get_link(link_id).state.open = open_

    def is_link_traversable(self, link_id: str, mode: str) -> bool:
        return self.get_link(link_id).is_traversable(mode)

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "coordinate_system": self.coordinate_system,
            "node_count": self.node_count,
            "link_count": self.link_count,
            "nodes": [node.to_record() for node in self.nodes()],
            "links": [link.to_record() for link in self.links()],
            "metadata": copy_json_mapping(self.metadata),
        }

    def _index_link(self, link: RuntimeLink) -> None:
        self._outgoing[link.from_node_id].append(
            TraversalEdge(
                link_id=link.link_id,
                from_node_id=link.from_node_id,
                to_node_id=link.to_node_id,
            )
        )
        if link.bidirectional:
            self._outgoing[link.to_node_id].append(
                TraversalEdge(
                    link_id=link.link_id,
                    from_node_id=link.to_node_id,
                    to_node_id=link.from_node_id,
                    reversed=True,
                )
            )
