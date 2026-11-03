import type { FeatureCollection } from "./contracts";

/** WGS84 coordinates stay in longitude/latitude order until handed to Cesium. */
export function wardView(geometry: FeatureCollection) {
  let west = Infinity, east = -Infinity, south = Infinity, north = -Infinity;
  function visit(value: unknown) {
    if (!Array.isArray(value)) return;
    if (typeof value[0] === "number" && typeof value[1] === "number") {
      const [lon, lat] = value;
      if (!Number.isFinite(lon) || !Number.isFinite(lat) || Math.abs(lon) > 180 || Math.abs(lat) > 90) throw new Error("Invalid globe coordinate.");
      west = Math.min(west, lon); east = Math.max(east, lon);
      south = Math.min(south, lat); north = Math.max(north, lat);
    } else value.forEach(visit);
  }
  geometry.features.forEach((feature) => visit(feature.geometry.coordinates));
  if (!Number.isFinite(west)) throw new Error("No ward coordinates for the globe.");
  const latitude = (south + north) / 2;
  const span = Math.max((east - west) * Math.cos(latitude * Math.PI / 180), north - south) * 111_320;
  return { longitude: (west + east) / 2, latitude, range: Math.max(25_000, span * 2.1) };
}
