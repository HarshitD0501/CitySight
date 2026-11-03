"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { FeatureCollection, WardValue } from "@/lib/contracts";
import { demandColor } from "@/lib/mapStyle";

type Props = { geometry: FeatureCollection; values: WardValue[]; selectedId: string | null; onSelect: (id: string) => void };
const STYLE: import("maplibre-gl").StyleSpecification = { version: 8, sources: {}, layers: [{ id: "paper", type: "background", paint: { "background-color": "#f1f3ef" } }] };
function coordinateBounds(collection: FeatureCollection): [[number, number], [number, number]] | null {
  let west = 180, south = 90, east = -180, north = -90, seen = false;
  const visit = (value: unknown): void => {
    if (!Array.isArray(value)) return;
    if (value.length >= 2 && typeof value[0] === "number" && typeof value[1] === "number") {
      const [lon, lat] = value;
      if (Number.isFinite(lon) && Number.isFinite(lat) && Math.abs(lon) <= 180 && Math.abs(lat) <= 90) {
        west = Math.min(west, lon); east = Math.max(east, lon); south = Math.min(south, lat); north = Math.max(north, lat); seen = true;
      }
      return;
    }
    value.forEach(visit);
  };
  collection.features.forEach((feature) => visit(feature.geometry.coordinates));
  return seen ? [[west, south], [east, north]] : null;
}

export default function WardMap({ geometry, values, selectedId, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<import("maplibre-gl").Map | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const maximum = useMemo(() => Math.max(1, ...values.map((row) => row.value ?? 0)), [values]);
  const selected = selectedId ?? "";
  const geoData = useMemo(() => {
    const valueMap = new Map(values.map((row) => [row.ward_id, row.value]));
    return {
      type: "FeatureCollection" as const,
      features: geometry.features.map((feature) => ({
        ...feature,
        properties: { ...feature.properties, pulse_value: valueMap.get(feature.properties.ward_id) ?? null },
      })),
    };
  }, [geometry, values]);
  const latest = useRef({ geoData, maximum, selected });

  useEffect(() => {
    latest.current = { geoData, maximum, selected };
    const instance = map.current;
    if (!instance) return;
    let source: import("maplibre-gl").GeoJSONSource | undefined;
    try { source = instance.getSource("wards") as import("maplibre-gl").GeoJSONSource | undefined; }
    catch { return; } // The initial load callback will use the latest snapshot.
    if (source) void source.setData(geoData as import("maplibre-gl").GeoJSONSourceSpecification["data"]);
    if (instance?.getLayer("ward-fills")) {
      instance.setPaintProperty("ward-fills", "fill-color", demandColor(maximum) as import("maplibre-gl").ExpressionSpecification);
      instance.setPaintProperty("ward-fills", "fill-opacity", ["case", ["==", ["get", "ward_id"], selected], 0.96, 0.82]);
    }
    if (instance?.getLayer("ward-lines")) {
      instance.setPaintProperty("ward-lines", "line-color", ["case", ["==", ["get", "ward_id"], selected], "#bf522d", "#526660"]);
      instance.setPaintProperty("ward-lines", "line-width", ["case", ["==", ["get", "ward_id"], selected], 2.5, 0.7]);
    }
  }, [geoData, selected, maximum]);

  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | undefined;
    let instance: import("maplibre-gl").Map | null = null;
    const start = async () => {
      try {
        const maplibre = await import("maplibre-gl");
        if (disposed || !container.current) return;
        // MapLibre v6's worker must be emitted explicitly by the Next.js bundler.
        maplibre.setWorkerUrl(new URL("maplibre-gl/dist/maplibre-gl-worker.mjs", import.meta.url).toString());
        const initialBounds = coordinateBounds(geometry);
        const center: [number, number] = initialBounds
          ? [(initialBounds[0][0] + initialBounds[1][0]) / 2, (initialBounds[0][1] + initialBounds[1][1]) / 2]
          : [0, 0];
        instance = new maplibre.Map({
          container: container.current, style: STYLE, center, zoom: 9,
          attributionControl: false, maxPitch: 0, dragRotate: false, pitchWithRotate: false,
        });
        map.current = instance;
        instance.on("error", () => setProblem("The ward map could not render. Use the searchable ward table below."));
        instance.on("load", () => {
          if (disposed || !instance) return;
          const snapshot = latest.current;
          instance.addSource("wards", { type: "geojson", data: snapshot.geoData as import("maplibre-gl").GeoJSONSourceSpecification["data"] });
          instance.addLayer({ id: "ward-fills", type: "fill", source: "wards", paint: {
            "fill-color": demandColor(snapshot.maximum) as import("maplibre-gl").ExpressionSpecification,
            "fill-opacity": ["case", ["==", ["get", "ward_id"], snapshot.selected], 0.96, 0.82],
          } });
          instance.addLayer({ id: "ward-lines", type: "line", source: "wards", paint: {
            "line-color": ["case", ["==", ["get", "ward_id"], snapshot.selected], "#bf522d", "#526660"],
            "line-width": ["case", ["==", ["get", "ward_id"], snapshot.selected], 2.5, 0.7],
          } });
          const bounds = coordinateBounds(geometry);
          if (bounds) instance.fitBounds(bounds, { padding: 30, duration: 0, maxZoom: 11 });
          instance.on("click", "ward-fills", (event) => {
            const id = event.features?.[0]?.properties?.ward_id;
            if (typeof id === "string") onSelect(id);
          });
          instance.on("mouseenter", "ward-fills", () => { if (container.current) container.current.style.cursor = "pointer"; });
          instance.on("mouseleave", "ward-fills", () => { if (container.current) container.current.style.cursor = ""; });
          setProblem(null);
        });
        observer = new ResizeObserver(() => instance?.resize());
        observer.observe(container.current);
      } catch (error) {
        setProblem(error instanceof Error ? `Map unavailable: ${error.message}` : "Map unavailable. The ward table remains available below.");
      }
    };
    void start();
    return () => { disposed = true; observer?.disconnect(); instance?.remove(); map.current = null; };
    // GeoJSON is updated by the second effect to keep map lifecycle stable.
  }, [geometry, onSelect]);

  return <div className="map-frame">
    <div ref={container} className="map-canvas" role="img" aria-label="Interactive map of challenge wards. Each polygon is selectable; the table provides the same values without a map." />
    {problem && <div className="map-fallback" role="status"><span className="fallback-mark" aria-hidden="true">↗</span><p>{problem}</p></div>}
    <div className="map-credit">Ward boundaries · supplied challenge geometry</div>
  </div>;
}
