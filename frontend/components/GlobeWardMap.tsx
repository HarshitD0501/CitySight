"use client";

import { useEffect, useRef, useState } from "react";
import type { WardMapProps } from "./WardMap";
import { createGlobe, type GlobeHandle } from "@/lib/cesiumGlobe";

export default function GlobeWardMap({ geometry, values, selectedId, onSelect, onFailure }: WardMapProps & { onFailure: (message: string) => void }) {
  const frame = useRef<HTMLDivElement>(null);
  const container = useRef<HTMLDivElement>(null);
  const globe = useRef<GlobeHandle | null>(null);
  const latest = useRef({ values, selectedId });
  const [ready, setReady] = useState(false);
  const [imageryProblem, setImageryProblem] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [viewProblem, setViewProblem] = useState<string | null>(null);

  useEffect(() => {
    latest.current = { values, selectedId };
    globe.current?.update(values, selectedId);
  }, [values, selectedId]);

  useEffect(() => {
    const controller = new AbortController();
    let observer: ResizeObserver | undefined;
    let handle: GlobeHandle | null = null;
    const start = async () => {
      try {
        if (!container.current) return;
        handle = await createGlobe(container.current, geometry, {
          signal: controller.signal, onSelect,
          onError: (message) => { if (!controller.signal.aborted) onFailure(message); },
          onImageryError: () => { if (!controller.signal.aborted) setImageryProblem(true); },
        });
        if (controller.signal.aborted) { handle.destroy(); return; }
        globe.current = handle;
        handle.update(latest.current.values, latest.current.selectedId);
        observer = new ResizeObserver(() => handle?.resize());
        observer.observe(container.current);
        setReady(true);
      } catch (error) {
        if (!controller.signal.aborted) onFailure(error instanceof Error ? error.message : "3D view unavailable. Switched to the 2D map.");
      }
    };
    void start();
    return () => { controller.abort(); observer?.disconnect(); handle?.destroy(); globe.current = null; };
  }, [geometry, onSelect, onFailure]);

  useEffect(() => {
    const changed = () => setFullscreen(document.fullscreenElement === frame.current);
    document.addEventListener("fullscreenchange", changed);
    return () => document.removeEventListener("fullscreenchange", changed);
  }, []);

  const toggleFullscreen = async () => {
    setViewProblem(null);
    try {
      if (document.fullscreenElement === frame.current) await document.exitFullscreen();
      else if (frame.current?.requestFullscreen) await frame.current.requestFullscreen();
      else setViewProblem("Fullscreen unavailable. The globe controls still work.");
    } catch { setViewProblem("Fullscreen was blocked by the browser. The globe controls still work."); }
  };

  return <div ref={frame} className="map-frame globe-frame">
    <div ref={container} className="globe-canvas" role="region" aria-label="3D ward globe. Use the buttons to tilt, reset and zoom, or select wards using the table." />
    <div className="globe-tools" role="group" aria-label="3D camera controls">
      <button type="button" disabled={!ready} onClick={() => globe.current?.view("wards")}>Tilt view</button>
      <button type="button" disabled={!ready} onClick={() => globe.current?.view("top")}>Top down</button>
      <button type="button" disabled={!ready} onClick={() => globe.current?.view("globe")}>Globe</button>
      <button type="button" disabled={!ready} aria-label="Zoom in 3D" onClick={() => globe.current?.zoom(1)}>+</button>
      <button type="button" disabled={!ready} aria-label="Zoom out 3D" onClick={() => globe.current?.zoom(-1)}>−</button>
      <button type="button" disabled={!ready} aria-pressed={fullscreen} onClick={() => void toggleFullscreen()}>{fullscreen ? "Exit fullscreen" : "Fullscreen"}</button>
    </div>
    {!ready && <div className="globe-loading" role="status"><strong>Opening the 3D globe</strong><span>Downloading the map engine. The first load needs internet; 2D streets is available above.</span></div>}
    {(imageryProblem || viewProblem) && <div className="globe-notice" role="status">{viewProblem ?? "Street imagery unavailable. Local ward overlays remain visible; use 2D streets for the alternate map."}</div>}
    <div className="globe-caption">3D WARD OVERVIEW<span>Drag to orbit · Ctrl + drag to tilt · scroll to zoom</span><small>Ellipsoid + OpenStreetMap · photorealistic buildings not configured</small></div>
    <a className="globe-attribution" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">© OpenStreetMap contributors</a>
  </div>;
}
