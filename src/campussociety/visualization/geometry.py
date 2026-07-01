from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from campussociety.core.entities import JsonValue, copy_state


@dataclass(frozen=True, slots=True)
class GeometryExport:
    """Static geometry datasets derived from a final simulation snapshot."""

    network_geojson: Mapping[str, JsonValue]
    facilities_geojson: Mapping[str, JsonValue]


def geometry_from_snapshot(snapshot: Mapping[str, JsonValue]) -> GeometryExport:
    """Extract network and facility GeoJSON from final snapshot environment state."""

    world = _environment_world(snapshot)
    network = _mapping(world.get("network"))
    facilities = _mapping(world.get("facilities"))
    return GeometryExport(
        network_geojson=network_geojson(network),
        facilities_geojson=facilities_geojson(facilities, network),
    )


def network_geojson(network: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    nodes = _records(network.get("nodes"))
    links = _records(network.get("links"))
    positions = {
        node_id: position
        for node in nodes
        if isinstance(node_id := node.get("node_id"), str)
        and (position := _position(node.get("position"))) is not None
    }

    features: list[JsonValue] = []
    for node in nodes:
        node_id = node.get("node_id")
        if not isinstance(node_id, str) or node_id not in positions:
            continue
        x, y = positions[node_id]
        features.append(
            {
                "type": "Feature",
                "id": f"node:{node_id}",
                "geometry": {
                    "type": "Point",
                    "coordinates": [x, y],
                },
                "properties": {
                    "feature_type": "network_node",
                    "node_id": node_id,
                    "attributes": copy_state(_mapping(node.get("attributes"))),
                },
            }
        )

    for link in links:
        link_id = link.get("link_id")
        from_node_id = link.get("from_node_id")
        to_node_id = link.get("to_node_id")
        if (
            not isinstance(link_id, str)
            or not isinstance(from_node_id, str)
            or not isinstance(to_node_id, str)
            or from_node_id not in positions
            or to_node_id not in positions
        ):
            continue
        from_x, from_y = positions[from_node_id]
        to_x, to_y = positions[to_node_id]
        features.append(
            {
                "type": "Feature",
                "id": f"link:{link_id}",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[from_x, from_y], [to_x, to_y]],
                },
                "properties": {
                    "feature_type": "network_link",
                    "link_id": link_id,
                    "from_node_id": from_node_id,
                    "to_node_id": to_node_id,
                    "length_meters": link.get("length_meters"),
                    "allowed_modes": link.get("allowed_modes"),
                    "bidirectional": link.get("bidirectional"),
                    "state": copy_state(_mapping(link.get("state"))),
                    "attributes": copy_state(_mapping(link.get("attributes"))),
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "schema": "campussociety.visualization.network_geojson.v1",
            "coordinate_system": network.get("coordinate_system"),
            "node_count": network.get("node_count"),
            "link_count": network.get("link_count"),
        },
    }


def facilities_geojson(
    facilities: Mapping[str, JsonValue],
    network: Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    network_positions = _network_positions(network)
    features: list[JsonValue] = []
    for facility in _records(facilities.get("facilities")):
        facility_id = facility.get("facility_id")
        if not isinstance(facility_id, str):
            continue
        position = _position(facility.get("position"))
        access_node_id = facility.get("access_node_id")
        if position is None and isinstance(access_node_id, str):
            position = network_positions.get(access_node_id)
        if position is None:
            continue
        x, y = position
        features.append(
            {
                "type": "Feature",
                "id": f"facility:{facility_id}",
                "geometry": {
                    "type": "Point",
                    "coordinates": [x, y],
                },
                "properties": {
                    "feature_type": "facility",
                    "facility_id": facility_id,
                    "facility_type": facility.get("facility_type"),
                    "access_node_id": access_node_id,
                    "capacity": facility.get("capacity"),
                    "state": copy_state(_mapping(facility.get("state"))),
                    "attributes": copy_state(_mapping(facility.get("attributes"))),
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "schema": "campussociety.visualization.facilities_geojson.v1",
            "facility_count": facilities.get("facility_count"),
        },
    }


def _environment_world(snapshot: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    entities = _mapping(snapshot.get("entities"))
    environment = _mapping(entities.get("environment"))
    world = _mapping(environment.get("world"))
    if not world:
        msg = "final snapshot does not include environment.world"
        raise ValueError(msg)
    return world


def _network_positions(
    network: Mapping[str, JsonValue],
) -> dict[str, tuple[float, float]]:
    positions: dict[str, tuple[float, float]] = {}
    for node in _records(network.get("nodes")):
        node_id = node.get("node_id")
        position = _position(node.get("position"))
        if isinstance(node_id, str) and position is not None:
            positions[node_id] = position
    return positions


def _records(value: JsonValue | None) -> tuple[Mapping[str, JsonValue], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _mapping(value: JsonValue | None) -> Mapping[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _position(value: JsonValue | None) -> tuple[float, float] | None:
    if not isinstance(value, dict):
        return None
    x = value.get("x")
    y = value.get("y")
    if not isinstance(x, int | float) or not isinstance(y, int | float):
        return None
    return (float(x), float(y))
