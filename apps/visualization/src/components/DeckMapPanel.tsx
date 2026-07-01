import { COORDINATE_SYSTEM, OrthographicView } from "@deck.gl/core";
import DeckGL from "@deck.gl/react";
import { GeoJsonLayer } from "@deck.gl/layers";
import { useMemo } from "react";
import type { GeoJSON } from "geojson";

import type { FeatureCollection, GeoJsonFeature, ReplayFrame } from "../types";

interface DeckMapPanelProps {
  network: FeatureCollection;
  facilities: FeatureCollection;
  currentFrame: ReplayFrame | null;
}

export default function DeckMapPanel({
  network,
  facilities,
  currentFrame,
}: DeckMapPanelProps) {
  const bounds = useMemo(() => computeBounds([network, facilities]), [
    network,
    facilities,
  ]);
  const initialViewState = useMemo(
    () => ({
      target: [bounds.centerX, bounds.centerY, 0] as [number, number, number],
      zoom: bounds.zoom,
    }),
    [bounds],
  );
  const layers = useMemo(
    () => [
      new GeoJsonLayer<Record<string, unknown>>({
        id: "network",
        data: network as GeoJSON,
        coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
        pickable: true,
        stroked: true,
        filled: false,
        getLineColor: (feature) =>
          feature.properties.feature_type === "network_link"
            ? [76, 86, 100, 220]
            : [98, 113, 128, 180],
        getLineWidth: (feature) =>
          feature.properties.feature_type === "network_link" ? 2 : 0,
        lineWidthUnits: "pixels",
        pointRadiusUnits: "pixels",
        getPointRadius: 3,
        getFillColor: [76, 86, 100, 180],
      }),
      new GeoJsonLayer<Record<string, unknown>>({
        id: "facilities",
        data: facilities as GeoJSON,
        coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
        pickable: true,
        stroked: true,
        filled: true,
        getFillColor: [44, 125, 109, 230],
        getLineColor: [255, 255, 255, 230],
        getLineWidth: 1,
        lineWidthUnits: "pixels",
        pointRadiusUnits: "pixels",
        getPointRadius: 6,
      }),
    ],
    [network, facilities],
  );

  return (
    <section className="map-panel">
      <div className="map-toolbar">
        <div>
          <h2>Network Replay</h2>
          <p>{currentFrame ? `t=${currentFrame.time}s` : "No replay frame"}</p>
        </div>
        <div className="map-legend">
          <span>
            <i className="legend-line" /> Links
          </span>
          <span>
            <i className="legend-point" /> Facilities
          </span>
        </div>
      </div>
      <div className="deck-frame">
        <DeckGL
          views={new OrthographicView({ id: "main", controller: true })}
          initialViewState={initialViewState}
          controller
          layers={layers}
          getTooltip={({ object }) => tooltip(object as GeoJsonFeature | null)}
        />
      </div>
    </section>
  );
}

function tooltip(feature: GeoJsonFeature | null): string | null {
  if (!feature) {
    return null;
  }
  const properties = feature.properties;
  const featureType = stringValue(properties.feature_type);
  if (featureType === "facility") {
    return [
      stringValue(properties.facility_id),
      stringValue(properties.facility_type),
    ]
      .filter(Boolean)
      .join(" · ");
  }
  if (featureType === "network_link") {
    return [
      stringValue(properties.link_id),
      stringValue(properties.length_meters),
    ]
      .filter(Boolean)
      .join(" · ");
  }
  return stringValue(properties.node_id);
}

function computeBounds(collections: FeatureCollection[]) {
  const coordinates = collections.flatMap((collection) =>
    collection.features.flatMap(featureCoordinates),
  );
  if (coordinates.length === 0) {
    return { centerX: 0, centerY: 0, zoom: 4 };
  }
  const xs = coordinates.map(([x]) => x);
  const ys = coordinates.map(([, y]) => y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const extent = Math.max(maxX - minX, maxY - minY, 1);
  return {
    centerX: (minX + maxX) / 2,
    centerY: (minY + maxY) / 2,
    zoom: Math.max(1, Math.min(14, Math.log2(520 / extent))),
  };
}

function featureCoordinates(feature: GeoJsonFeature): [number, number][] {
  const coordinates = feature.geometry.coordinates;
  if (feature.geometry.type === "Point" && isPoint(coordinates)) {
    return [coordinates];
  }
  if (feature.geometry.type === "LineString" && isLineString(coordinates)) {
    return coordinates;
  }
  return [];
}

function isPoint(value: number[] | number[][]): value is [number, number] {
  return (
    Array.isArray(value) &&
    value.length >= 2 &&
    typeof value[0] === "number" &&
    typeof value[1] === "number"
  );
}

function isLineString(value: number[] | number[][]): value is [number, number][] {
  return (
    Array.isArray(value) &&
    value.every(
      (point) =>
        Array.isArray(point) &&
        point.length >= 2 &&
        typeof point[0] === "number" &&
        typeof point[1] === "number",
    )
  );
}

function stringValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}
