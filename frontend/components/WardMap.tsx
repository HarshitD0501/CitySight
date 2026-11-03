"use client";

import { useCallback, useState } from "react";
import dynamic from "next/dynamic";
import type { FeatureCollection, WardValue } from "@/lib/contracts";

const GlobeWardMap = dynamic(() => import("./GlobeWardMap"), { ssr: false, loading: () => <div className="map-unavailable" role="status">Preparing 3D view…</div> });
const LeafletWardMap = dynamic(() => import("./LeafletWardMap"), { ssr: false, loading: () => <div className="map-unavailable" role="status">Preparing 2D map…</div> });
export type WardMapProps = { geometry: FeatureCollection; values: WardValue[]; selectedId: string | null; onSelect: (id: string) => void };

export default function WardMap(props: WardMapProps) {
  const [mode, setMode] = useState<"3d" | "2d">("3d");
  const [problem, setProblem] = useState<string | null>(null);
  const fallback = useCallback((message: string) => { setProblem(message); setMode("2d"); }, []);
  return <div className="ward-map-views">
    <div className="map-view-bar">
      <div className="map-view-switch" role="group" aria-label="Map renderer">
        <button type="button" aria-pressed={mode === "3d"} onClick={() => { setProblem(null); setMode("3d"); }}>3D globe</button>
        <button type="button" aria-pressed={mode === "2d"} onClick={() => setMode("2d")}>2D streets</button>
      </div>
      <span>Original ward boundaries · shared filters</span>
    </div>
    {problem && <p className="globe-recovery" role="status">{problem} You can retry with 3D globe.</p>}
    {mode === "3d" ? <GlobeWardMap {...props} onFailure={fallback} /> : <LeafletWardMap {...props} />}
  </div>;
}
