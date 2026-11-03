export type Category = "electrical" | "solid_waste" | "roads" | "trees" | "animals_health" | "other";
export type Mode = "ward" | "challenge";
export type ChallengeMeasure = "predicted" | "actual";
export type WardStatus = "observed" | "target" | "unassigned";
export type DemandRow = { ward_id: string; month: string; category_group: Category; predicted_count?: number; observed_count?: number; actual_count?: number };
export type WardProperties = { ward_id: string; ward_name: string; ward_status: WardStatus; [key: string]: unknown };
export type GeoFeature = { type: "Feature"; properties: WardProperties; geometry: { type: "Polygon" | "MultiPolygon"; coordinates: unknown } };
export type FeatureCollection = { type: "FeatureCollection"; features: GeoFeature[] };
export type Envelope<T> = { schema_version: 1; run_id: string; records: T[]; fit_id?: string };
export type Manifest = {
  schema_version: 1; run_id: string; created_at: string; coverage_policy: "COV-1";
  source_hashes: Record<string, string>; categories: Category[]; target_months: string[];
  selected_model: string; full_fit_id: string; challenge_fit_id: string;
  files: { predictions: string; observations: string; geometry: string; challenge: string; metrics: string };
};
export type Metrics = {
  schema_version: 1; run_id: string; selected_method: string; full_fit_id: string; challenge_fit_id: string;
  challenge_metrics: { wape: number | null; wape_undefined_reason: string | null; mae: number; spearman: number | null; top_quarter_recall: number; top_k: number };
  category_metrics: Record<Category, { wape: number | null; mae: number }>;
  limitations: string[];
};
export type DashboardData = {
  manifest: Manifest; predictions: Envelope<DemandRow>; observations: Envelope<DemandRow>;
  geometry: FeatureCollection; challenge: Envelope<DemandRow & { actual_count: number }> & { challenge_wards: string[] };
  metrics: Metrics; geometryError: string | null;
};
export type WardValue = { ward_id: string; ward_name: string; ward_status: WardStatus; value: number | null; actual: number | null; predicted: number | null };

const CATEGORIES: Category[] = ["electrical", "solid_waste", "roads", "trees", "animals_health", "other"];
const FILE_KEYS = ["predictions", "observations", "geometry", "challenge", "metrics"] as const;

function object(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`${label} must be a JSON object.`);
  return value as Record<string, unknown>;
}
function text(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${label} must be a non-empty string.`);
  return value;
}
function finiteNonnegative(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) throw new Error(`${label} must be finite and non-negative.`);
  return value;
}
function validateRing(ring: unknown): boolean {
  if (!Array.isArray(ring) || ring.length < 4) return false;
  const positions = ring.map((position) => Array.isArray(position) && (position.length === 2 || position.length === 3)
    && position.every((coordinate) => typeof coordinate === "number" && Number.isFinite(coordinate))
    && Math.abs(position[0]) <= 180 && Math.abs(position[1]) <= 90);
  return positions.every(Boolean) && JSON.stringify(ring[0]) === JSON.stringify(ring[ring.length - 1]);
}
function validatePolygonCoordinates(type: string, coordinates: unknown): boolean {
  if (!Array.isArray(coordinates) || !coordinates.length) return false;
  const polygons = type === "Polygon" ? [coordinates] : coordinates;
  return polygons.every((polygon) => Array.isArray(polygon) && polygon.length > 0 && polygon.every(validateRing));
}
function rows<T>(value: unknown, label: string, runId: string): Envelope<T> {
  const data = object(value, label);
  if (data.schema_version !== 1 || data.run_id !== runId || !Array.isArray(data.records)) throw new Error(`${label} has an unsupported schema or run ID.`);
  return data as unknown as Envelope<T>;
}
function checkRows<T extends DemandRow>(envelope: Envelope<T>, label: string, field: "predicted_count" | "observed_count" | "actual_count"): Set<string> {
  const seen = new Set<string>();
  for (const row of envelope.records) {
    text(row.ward_id, `${label}.ward_id`); text(row.month, `${label}.month`);
    if (!CATEGORIES.includes(row.category_group)) throw new Error(`${label} contains an unknown category.`);
    const key = `${row.ward_id}\u0000${row.month}\u0000${row.category_group}`;
    if (seen.has(key)) throw new Error(`${label} contains duplicate ward/month/category rows.`);
    seen.add(key); finiteNonnegative(row[field], `${label}.${field}`);
  }
  return seen;
}

export function validateDashboardAssets(raw: unknown[], geometryError: string | null = null): DashboardData {
  if (raw.length !== 6) throw new Error("The dashboard requires one manifest and five data files.");
  const [manifestRaw, predictionsRaw, observationsRaw, geometryRaw, challengeRaw, metricsRaw] = raw;
  const m = object(manifestRaw, "manifest") as unknown as Manifest;
  if (m.schema_version !== 1 || m.coverage_policy !== "COV-1") throw new Error("Unsupported manifest schema or coverage policy.");
  text(m.run_id, "manifest.run_id"); text(m.full_fit_id, "manifest.full_fit_id"); text(m.challenge_fit_id, "manifest.challenge_fit_id");
  const created = Date.parse(text(m.created_at, "manifest.created_at"));
  if (!Number.isFinite(created)) throw new Error("Manifest creation time is invalid.");
  const hashes = object(m.source_hashes, "manifest.source_hashes");
  if (!Object.keys(hashes).length || Object.values(hashes).some((hash) => typeof hash !== "string" || !/^[a-f0-9]{64}$/.test(hash))) throw new Error("Manifest source hashes are invalid.");
  if (!Array.isArray(m.categories) || m.categories.length !== CATEGORIES.length || CATEGORIES.some((c) => !m.categories.includes(c))) throw new Error("Manifest categories do not match the supported set.");
  if (!Array.isArray(m.target_months) || !m.target_months.length || new Set(m.target_months).size !== m.target_months.length || m.target_months.some((month) => typeof month !== "string" || !/^\d{4}-(0[1-9]|1[0-2])$/.test(month))) throw new Error("Manifest target months are invalid.");
  const files = object(m.files, "manifest.files");
  const requiredFiles: Record<(typeof FILE_KEYS)[number], string> = { predictions: "predictions.json", observations: "observations.json", geometry: "wards.geojson", challenge: "challenge.json", metrics: "metrics.json" };
  for (const key of FILE_KEYS) {
    const file = text(files[key], `manifest.files.${key}`);
    if (file !== requiredFiles[key]) throw new Error(`Manifest has an unexpected ${key} asset path.`);
  }
  const predictions = rows<DemandRow>(predictionsRaw, "predictions", m.run_id);
  const observations = rows<DemandRow>(observationsRaw, "observations", m.run_id);
  const challenge = rows<DemandRow & { actual_count: number }>(challengeRaw, "challenge", m.run_id) as DashboardData["challenge"];
  checkRows(predictions, "predictions", "predicted_count");
  checkRows(observations, "observations", "observed_count"); checkRows(challenge, "challenge", "actual_count");
  for (const envelope of [predictions, observations, challenge]) {
    if (envelope.records.some((row) => !m.target_months.includes(row.month) || !m.categories.includes(row.category_group))) throw new Error("An artifact row is outside the manifest month/category set.");
  }
  if ((observationsRaw as { coverage_policy?: unknown }).coverage_policy !== m.coverage_policy) throw new Error("Observation coverage policy does not match the manifest.");
  if ((predictionsRaw as { prediction_type?: unknown }).prediction_type !== "model_estimate") throw new Error("Prediction artifact is not labeled as a model estimate.");
  for (const row of challenge.records) finiteNonnegative(row.predicted_count, "challenge.predicted_count");
  if (predictions.fit_id !== m.full_fit_id || challenge.fit_id !== m.challenge_fit_id) throw new Error("Artifact fit provenance does not match the manifest.");
  const challengeWards = (challengeRaw as { challenge_wards?: unknown }).challenge_wards;
  if (!Array.isArray(challengeWards) || challengeWards.length !== 12 || challengeWards.some((ward) => typeof ward !== "string") || new Set(challengeWards).size !== 12) throw new Error("Challenge ward list must contain twelve unique IDs.");
  if (challenge.records.some((row) => !challengeWards.includes(row.ward_id))) throw new Error("Challenge rows include a ward outside the reserved set.");
  let geometry: FeatureCollection = { type: "FeatureCollection", features: [] };
  if (!geometryError) {
    try {
      const candidate = object(geometryRaw, "wards.geojson") as unknown as FeatureCollection;
      if (candidate.type !== "FeatureCollection" || !Array.isArray(candidate.features) || !candidate.features.length) throw new Error("Ward geometry is not a valid FeatureCollection.");
      const wardIds = new Set<string>();
      for (const feature of candidate.features) {
        const props = object(feature?.properties, "geometry.properties");
        const id = text(props.ward_id, "geometry.ward_id");
        if (feature.type !== "Feature" || wardIds.has(id)) throw new Error("Ward geometry has an invalid or duplicate feature.");
        wardIds.add(id);
        if (!("observed target unassigned".split(" ").includes(String(props.ward_status)))) throw new Error("Ward geometry contains an unknown status.");
        if (feature.geometry?.type !== "Polygon" && feature.geometry?.type !== "MultiPolygon") throw new Error("Ward geometry contains an unsupported shape.");
        if (!validatePolygonCoordinates(feature.geometry.type, feature.geometry.coordinates)) throw new Error("Ward geometry contains an invalid ring or coordinate.");
      }
      for (const row of predictions.records) if (!wardIds.has(row.ward_id)) throw new Error("Prediction ward IDs do not match the geometry.");
      geometry = candidate;
    } catch (cause) {
      geometryError = cause instanceof Error ? cause.message : "Ward geometry is invalid.";
    }
  }
  const metrics = object(metricsRaw, "metrics") as unknown as Metrics;
  if (metrics.schema_version !== 1 || metrics.run_id !== m.run_id || metrics.full_fit_id !== m.full_fit_id || metrics.challenge_fit_id !== m.challenge_fit_id) throw new Error("Metrics provenance does not match the manifest.");
  if (metrics.challenge_metrics.wape !== null) finiteNonnegative(metrics.challenge_metrics.wape, "metrics.wape");
  finiteNonnegative(metrics.challenge_metrics.mae, "metrics.mae");
  if (metrics.challenge_metrics.spearman !== null && (typeof metrics.challenge_metrics.spearman !== "number" || !Number.isFinite(metrics.challenge_metrics.spearman) || Math.abs(metrics.challenge_metrics.spearman) > 1)) throw new Error("Metrics Spearman value is invalid.");
  if (typeof metrics.challenge_metrics.top_quarter_recall !== "number" || metrics.challenge_metrics.top_quarter_recall < 0 || metrics.challenge_metrics.top_quarter_recall > 1) throw new Error("Metrics top-quarter recall is invalid.");
  return { manifest: m, predictions, observations, geometry, challenge, metrics, geometryError };
}

export function buildWardValues(data: DashboardData, month: string, category: Category, mode: Mode, measure: ChallengeMeasure): WardValue[] {
  const pred = new Map<string, number>();
  const obs = new Map<string, number>();
  const challenge = new Map<string, { actual: number; predicted: number }>();
  if (mode === "ward") {
    for (const row of data.predictions.records) if (row.month === month && row.category_group === category) pred.set(row.ward_id, row.predicted_count!);
    for (const row of data.observations.records) if (row.month === month && row.category_group === category) obs.set(row.ward_id, row.observed_count!);
  } else {
    for (const row of data.challenge.records) if (row.month === month && row.category_group === category) challenge.set(row.ward_id, { actual: row.actual_count!, predicted: row.predicted_count! });
  }
  const wards = new Map<string, { ward_name: string; ward_status: WardStatus }>();
  for (const feature of data.geometry.features) wards.set(feature.properties.ward_id, {
    ward_name: feature.properties.ward_name || `Ward ${feature.properties.ward_id}`, ward_status: feature.properties.ward_status,
  });
  for (const row of data.observations.records) if (!wards.has(row.ward_id)) wards.set(row.ward_id, { ward_name: `Ward ${row.ward_id}`, ward_status: "observed" });
  for (const row of data.predictions.records) if (!wards.has(row.ward_id)) wards.set(row.ward_id, { ward_name: `Ward ${row.ward_id}`, ward_status: "target" });
  for (const row of data.challenge.records) if (!wards.has(row.ward_id)) wards.set(row.ward_id, { ward_name: `Ward ${row.ward_id}`, ward_status: "observed" });
  return [...wards.entries()].map(([id, properties]) => {
    const measured = challenge.get(id);
    const estimate = mode === "challenge" ? measured?.predicted ?? null : pred.get(id) ?? null;
    const actual = mode === "challenge" ? measured?.actual ?? null : obs.get(id) ?? null;
    return { ward_id: id, ward_name: properties.ward_name || `Ward ${id}`, ward_status: properties.ward_status,
      value: mode === "challenge" ? (measure === "actual" ? actual : estimate) : properties.ward_status === "observed" ? actual : estimate,
      actual, predicted: estimate };
  });
}

export function filteredChallengeMetrics(data: DashboardData, month: string, category: Category) {
  const subset = data.challenge.records.filter((row) => row.month === month && row.category_group === category);
  const actualTotal = subset.reduce((sum, row) => sum + row.actual_count!, 0);
  const error = subset.reduce((sum, row) => sum + Math.abs(row.actual_count! - row.predicted_count!), 0);
  return { count: subset.length, wape: actualTotal === 0 ? null : error / actualTotal,
    mae: subset.length ? error / subset.length : null, wapeUndefined: actualTotal === 0 };
}

export function assetUrl(path: string): string {
  if (path.includes("/") || path.includes("\\") || path === "." || path === "..") throw new Error("Manifest asset paths must be local file names.");
  return `/data/${encodeURIComponent(path)}`;
}

export function formatMonth(month: string): string {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) throw new Error("Month must use YYYY-MM.");
  return new Date(`${month}-01T00:00:00Z`).toLocaleDateString("en", {
    month: "long", year: "numeric", timeZone: "UTC",
  });
}

export async function fetchAsset(name: string, geometry: boolean, signal: AbortSignal, fetchImpl: typeof fetch = fetch): Promise<{ data: unknown; geometryError: string | null }> {
  const url = assetUrl(name);
  try {
    const response = await fetchImpl(url, { signal, cache: "no-store" });
    if (!response.ok) throw new Error(`Data file ${name} failed to load (${response.status}).`);
    return { data: await response.json(), geometryError: null };
  } catch (cause) {
    if (!geometry || signal.aborted) throw cause;
    return { data: null, geometryError: cause instanceof Error ? cause.message : "Ward geometry could not be loaded." };
  }
}

export function valueSource(row: WardValue, mode: Mode, measure: ChallengeMeasure): "No data" | "Estimate" | "Recorded" {
  if (row.value === null) return "No data";
  if (mode === "challenge") return measure === "actual" ? "Recorded" : "Estimate";
  return row.ward_status === "target" ? "Estimate" : "Recorded";
}

export function challengeCoverage(values: WardValue[], challengeWards: string[]) {
  const heldOut = new Set(challengeWards);
  const available = values.filter((row) => heldOut.has(row.ward_id) && row.value !== null).length;
  const included = values.filter((row) => heldOut.has(row.ward_id)).length;
  return { observed: available, estimated: values.length - included, noData: heldOut.size - available };
}
