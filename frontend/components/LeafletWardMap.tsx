"use client";

import { useEffect, useRef, useState } from "react";
import type { GeoJSON, Map as LeafletMap, Path, TileLayer } from "leaflet";
import type { GeoJsonObject } from "geojson";
import type { FeatureCollection, WardValue } from "@/lib/contracts";
import { wardStyle } from "@/lib/mapStyle";

type Props = { geometry: FeatureCollection; values: WardValue[]; selectedId: string | null; onSelect: (id: string) => void };

export default function LeafletWardMap({ geometry, values, selectedId, onSelect }: Props) {
  const frame = useRef<HTMLDivElement>(null);
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<LeafletMap | null>(null);
  const wards = useRef<GeoJSON | null>(null);
  const tiles = useRef<TileLayer | null>(null);
  const latest = useRef({ values, selectedId, streets: true });
  const [streets, setStreets] = useState(true);
  const [ready, setReady] = useState(false);
  const [tileProblem, setTileProblem] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [viewProblem, setViewProblem] = useState<string | null>(null);

  useEffect(() => {
    latest.current = { values, selectedId, streets };
    const byId = new Map(values.map((row) => [row.ward_id, row]));
    const maximum = Math.max(1, ...values.map((row) => row.value ?? 0));
    let selectedLayer: Path | null = null;
    wards.current?.eachLayer((layer) => {
      const polygon = layer as Path & { feature?: { properties?: { ward_id?: string } } };
      const id = polygon.feature?.properties?.ward_id ?? "";
      const row = byId.get(id);
      polygon.setStyle(wardStyle(row?.value ?? null, maximum, id === selectedId, streets));
      const label = document.createElement("span");
      label.textContent = `${row?.ward_name ?? `Ward ${id}`} · ${row?.value == null ? "No data" : new Intl.NumberFormat("en-IN", { maximumFractionDigits: 1 }).format(row.value)}`;
      polygon.bindTooltip(label, { sticky: true });
      if (id === selectedId) selectedLayer = polygon;
    });
    (selectedLayer as Path | null)?.bringToFront();
    if (map.current && tiles.current) {
      if (streets && !map.current.hasLayer(tiles.current)) tiles.current.addTo(map.current);
      else if (!streets && map.current.hasLayer(tiles.current)) map.current.removeLayer(tiles.current);
    }
  }, [values, selectedId, streets, ready]);

  useEffect(() => {
    let disposed = false;
    let instance: LeafletMap | null = null;
    let observer: ResizeObserver | undefined;
    const start = async () => {
      try {
        const L = await import("leaflet");
        if (disposed || !container.current) return;
        instance = L.map(container.current, { minZoom: 9, maxZoom: 19, scrollWheelZoom: false, zoomAnimation: false, fadeAnimation: false });
        map.current = instance;
        const overlay = L.geoJSON(geometry as GeoJsonObject, {
          onEachFeature: (feature, layer) => {
            layer.on("click", () => onSelect(String(feature.properties.ward_id)));
          },
        }).addTo(instance);
        wards.current = overlay;
        const bounds = overlay.getBounds();
        if (!bounds.isValid()) throw new Error("Ward boundaries have no usable coordinates.");
        instance.fitBounds(bounds, { padding: [20, 20], maxZoom: 12, animate: false });
        instance.setMaxBounds(bounds.pad(0.6));
        L.control.scale({ imperial: false, position: "bottomleft" }).addTo(instance);
        const streetLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
          maxZoom: 19, updateWhenIdle: true, keepBuffer: 1, referrerPolicy: "strict-origin-when-cross-origin",
        });
        tiles.current = streetLayer;
        streetLayer.on("tileerror", () => {
          if (disposed || !instance?.hasLayer(streetLayer)) return;
          instance.removeLayer(streetLayer);
          setTileProblem(true);
          setStreets(false);
        });
        if (latest.current.streets) streetLayer.addTo(instance);
        observer = new ResizeObserver(() => instance?.invalidateSize({ animate: false }));
        observer.observe(container.current);
        setReady(true);
      } catch (error) {
        if (!disposed) setProblem(error instanceof Error ? `Map unavailable: ${error.message}` : "Map unavailable. Use the searchable ward table below.");
      }
    };
    void start();
    return () => { disposed = true; observer?.disconnect(); instance?.remove(); map.current = null; wards.current = null; tiles.current = null; };
  }, [geometry, onSelect]);

  useEffect(() => {
    const changed = () => setFullscreen(document.fullscreenElement === frame.current);
    document.addEventListener("fullscreenchange", changed);
    return () => document.removeEventListener("fullscreenchange", changed);
  }, []);

  const resetView = () => {
    const bounds = wards.current?.getBounds();
    if (bounds?.isValid()) map.current?.fitBounds(bounds, { padding: [20, 20], maxZoom: 12, animate: false });
  };
  const toggleFullscreen = async () => {
    setViewProblem(null);
    try {
      if (document.fullscreenElement === frame.current) await document.exitFullscreen();
      else if (frame.current?.requestFullscreen) await frame.current.requestFullscreen();
      else setViewProblem("Fullscreen is unavailable in this browser. You can still zoom and pan the map.");
    } catch { setViewProblem("Fullscreen was blocked by the browser. You can still zoom and pan the map."); }
  };

  return <div ref={frame} className="map-frame leaflet-frame">
    <div ref={container} className="map-canvas" role="region" aria-label="Ward map with OpenStreetMap streets. Use arrow keys to pan and plus or minus to zoom. Ward values are also available in the table." />
    <div className="map-tools" role="group" aria-label="Map display controls">
      <button type="button" disabled={!ready} aria-pressed={streets} onClick={() => { setTileProblem(false); setStreets((current) => !current); }}>{streets ? "Streets on" : "Streets off"}</button>
      <button type="button" disabled={!ready} onClick={resetView}>All wards</button>
      <button type="button" disabled={!ready} aria-pressed={fullscreen} onClick={() => void toggleFullscreen()}>{fullscreen ? "Exit fullscreen" : "Bird’s-eye view"}</button>
    </div>
    <div className="map-orientation" aria-hidden="true"><span>↑</span>N</div>
    {!ready && !problem && <div className="map-loading" role="status">Loading ward map…</div>}
    {(problem || tileProblem || viewProblem) && <div className="map-fallback" role="status"><p>{problem ?? viewProblem ?? "Street tiles unavailable. Ward boundaries and values remain available; turn Streets on to retry."}</p></div>}
    <div className="map-credit">Original dataset boundaries · {streets ? "Street background needs internet" : "Local ward view"}</div>
  </div>;
}
