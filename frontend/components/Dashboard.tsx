"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import WardMap from "@/components/WardMap";
import { buildWardValues, challengeCoverage, fetchAsset, filteredChallengeMetrics, formatMonth, validateDashboardAssets, valueSource } from "@/lib/contracts";
import type { Category, ChallengeMeasure, DashboardData, Mode, WardValue } from "@/lib/contracts";

const CATEGORY_LABELS: Record<Category, string> = {
  electrical: "Electrical", solid_waste: "Solid waste", roads: "Roads", trees: "Trees",
  animals_health: "Animals & health", other: "Other",
};
const CATEGORY_ORDER: Category[] = ["electrical", "solid_waste", "roads", "trees", "animals_health", "other"];
const fmt = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 1 });
const metricFmt = (value: number | null | undefined, suffix = "") => value == null ? "Not defined" : `${fmt.format(value)}${suffix}`;

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [month, setMonth] = useState("");
  const [category, setCategory] = useState<Category>("electrical");
  const [mode, setMode] = useState<Mode>("ward");
  const [measure, setMeasure] = useState<ChallengeMeasure>("predicted");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setData(null);
    setRetry((n) => n + 1);
  };

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timer = window.setTimeout(() => controller.abort(), 10_000);
    const load = async () => {
      try {
        const manifestResponse = await fetch("/data/manifest.json", { signal: controller.signal, cache: "no-store" });
        if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
        const manifest = await manifestResponse.json();
        const files = manifest?.files;
        if (!files || typeof files !== "object") throw new Error("Manifest does not list its data assets.");
        const names = [files.predictions, files.observations, files.geometry, files.challenge, files.metrics];
        const assets = await Promise.all(names.map((name: string, index: number) => fetchAsset(name, index === 2, controller.signal)));
        const geometryResult = assets[2];
        const checked = validateDashboardAssets([manifest, assets[0].data, assets[1].data, geometryResult.data, assets[3].data, assets[4].data], geometryResult.geometryError);
        if (!checked.manifest.target_months.length) throw new Error("Manifest contains no selectable months.");
        if (controller.signal.aborted) return;
        setData(checked); setMonth((current) => checked.manifest.target_months.includes(current) ? current : checked.manifest.target_months[0]);
        setSelectedId(null);
      } catch (cause) {
        if (active) {
          if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "Dashboard data could not be read.");
          else setError("Loading took longer than 10 seconds. Check that you are serving the local export, then retry.");
        }
      } finally {
        window.clearTimeout(timer);
        if (active) setLoading(false);
      }
    };
    void load();
    return () => { active = false; window.clearTimeout(timer); controller.abort(); };
  }, [retry]);

  const values = useMemo(() => data ? buildWardValues(data, month, category, mode, measure) : [], [data, month, category, mode, measure]);
  const sortedValues = useMemo(() => values.filter((row) => `${row.ward_id} ${row.ward_name}`.toLowerCase().includes(search.trim().toLowerCase()))
    .slice().sort((a, b) => {
      const av = a.value, bv = b.value;
      if (av == null && bv == null) return a.ward_name.localeCompare(b.ward_name);
      if (av == null) return 1; if (bv == null) return -1;
      return bv - av || a.ward_name.localeCompare(b.ward_name);
    }), [values, search]);
  const selected = values.find((row) => row.ward_id === selectedId) ?? null;
  const counts = useMemo(() => {
    if (mode === "challenge" && data) {
      return challengeCoverage(values, data.challenge.challenge_wards);
    }
    let observed = 0, estimated = 0, noData = 0;
    for (const row of values) {
      if (row.ward_status === "observed" && row.value !== null) observed++;
      else if (row.ward_status === "target" && row.value !== null) estimated++;
      else noData++;
    }
    return { observed, estimated, noData };
  }, [values, mode, data]);
  const challengeFiltered = useMemo(() => data ? filteredChallengeMetrics(data, month, category) : null, [data, month, category]);
  const onSelect = useCallback((id: string) => setSelectedId(id), []);

  return <main className="app-shell">
    <header className="topbar">
      <a className="brand" href="#top" aria-label="CitySight, Ward Pulse home"><span className="brand-glyph" aria-hidden="true"><i /><i /><i /><i /></span><span>CitySight<span className="brand-sub">WARD PULSE / CIVIC DATA</span></span></a>
      <div className="top-note"><span className="live-dot" aria-hidden="true" />LOCAL DATA VIEW <span className="top-separator">/</span> COV-1</div>
    </header>

    <div className="page-content" id="top">
      <section className="intro" aria-labelledby="page-title">
        <div className="intro-copy">
          <p className="eyebrow">WARD DEMAND, MADE LEGIBLE</p>
          <h1 id="page-title">A clearer view of<br /><em>civic demand.</em></h1>
          <p className="intro-text">Recorded reports and ward-level estimates, side by side. Choose a month and service category to explore the supplied ward challenge data.</p>
        </div>
        <div className="intro-stamp" aria-label="Six civic service categories, 18 months in the supplied dataset"><span className="stamp-number">06</span><span className="stamp-rule" /><span className="stamp-caption">SERVICE<br />CATEGORIES</span><span className="stamp-years">2024 — 2025</span></div>
      </section>

      <section className="control-panel" aria-label="Map and table controls">
        <div className="control-row">
          <div className="control-field"><label htmlFor="month-filter">MONTH</label><select id="month-filter" value={month} onChange={(event) => setMonth(event.target.value)} disabled={!data}>{data?.manifest.target_months.map((value) => <option key={value} value={value}>{formatMonth(value)}</option>)}</select></div>
          <div className="control-field category-field"><label htmlFor="category-filter">SERVICE CATEGORY</label><select id="category-filter" value={category} onChange={(event) => setCategory(event.target.value as Category)}>{CATEGORY_ORDER.map((value) => <option key={value} value={value}>{CATEGORY_LABELS[value]}</option>)}</select></div>
          <div className="view-switch" role="group" aria-label="Choose data view"><button type="button" aria-pressed={mode === "ward"} className={mode === "ward" ? "active" : ""} onClick={() => setMode("ward")}>Ward view</button><button type="button" aria-pressed={mode === "challenge"} className={mode === "challenge" ? "active" : ""} onClick={() => { setMode("challenge"); setMeasure("predicted"); }}>Challenge review</button></div>
          {mode === "challenge" && <div className="measure-switch" role="group" aria-label="Challenge value"><button type="button" aria-pressed={measure === "predicted"} className={measure === "predicted" ? "active" : ""} onClick={() => setMeasure("predicted")}>Estimate</button><button type="button" aria-pressed={measure === "actual"} className={measure === "actual" ? "active" : ""} onClick={() => setMeasure("actual")}>Recorded</button></div>}
        </div>
        <div className="control-foot"><span>Values are for <strong>{data?.manifest.target_months.includes(month) ? formatMonth(month) : "selected period"}</strong> · <strong>{CATEGORY_LABELS[category]}</strong></span><span className="coverage-note"><span className="partial-mark" aria-hidden="true">◐</span> June 2025 is a partial source month</span></div>
      </section>

      {error && <section className="load-error" role="alert"><div><strong>Ward data could not be loaded.</strong><p>{error}</p><p>Serve the exported site over local HTTP and keep its <code>data/</code> directory beside the page.</p></div><button type="button" className="button-secondary" onClick={handleRetry}>Retry loading</button></section>}
      {loading && <div className="loading-state" role="status"><span className="loading-mark" aria-hidden="true" />Loading and checking the local ward files…</div>}

      {data && <>
        {data.geometryError && <div className="geometry-warning" role="status"><strong>Map unavailable.</strong> {data.geometryError} The searchable ward table is still ready below.</div>}

        <section className="summary-strip" aria-label="Data coverage counts">
          <div className="summary-title"><span className="small-label">{mode === "challenge" ? "CHALLENGE FILTER" : "THIS FILTER"}</span><strong>{CATEGORY_LABELS[category]}</strong></div>
          <div className="summary-item"><span className="summary-swatch recorded" /> <span>{mode === "challenge" ? "Challenge wards" : "Recorded wards"}</span><strong>{counts.observed}</strong></div>
          <div className="summary-item"><span className="summary-swatch estimated" /> <span>{mode === "challenge" ? "Outside holdout" : "Estimated wards"}</span><strong>{counts.estimated}</strong></div>
          <div className="summary-item"><span className="summary-swatch nodata" /> <span>{mode === "challenge" ? "No comparison" : "No data"}</span><strong>{counts.noData}</strong></div>
          <div className="method-tag"><span className="small-label">SELECTED METHOD</span><strong>{data.metrics.selected_method.replaceAll("_", " ")}</strong></div>
        </section>

        {mode === "challenge" && data.metrics.challenge_metrics && <section className="challenge-panel" aria-labelledby="challenge-title">
          <div className="challenge-heading"><div><p className="eyebrow">RESERVED WARD CHECK</p><h2 id="challenge-title">How the estimates held up</h2><p>These twelve wards were held aside during model selection. Challenge review shows a local comparison; it does not hide answers in downloaded files.</p></div><span className="challenge-count">12 <small>WARDS</small></span></div>
          <div className="challenge-metrics"><div><span>FULL REVIEW · WAPE</span><strong>{metricFmt(data.metrics.challenge_metrics.wape == null ? null : data.metrics.challenge_metrics.wape * 100, "%")}</strong></div><div><span>FULL REVIEW · MAE</span><strong>{metricFmt(data.metrics.challenge_metrics.mae)}</strong><small>reports per cell</small></div><div><span>RANK AGREEMENT</span><strong>{metricFmt(data.metrics.challenge_metrics.spearman)}</strong><small>mean Spearman</small></div><div><span>TOP QUARTER FOUND</span><strong>{metricFmt(data.metrics.challenge_metrics.top_quarter_recall * 100, "%")}</strong><small>k = {data.metrics.challenge_metrics.top_k} per category</small></div></div>
          <div className="filtered-metric"><span>FILTERED · {CATEGORY_LABELS[category]} · {month}</span><span>{challengeFiltered?.count ?? 0} ward-month records</span><strong>{challengeFiltered?.wape == null ? "WAPE undefined (zero actual total)" : `WAPE ${metricFmt(challengeFiltered.wape * 100, "%")}`}</strong><span>MAE {metricFmt(challengeFiltered?.mae)} reports per cell</span></div>
        </section>}

        <section className="workspace" aria-label="Ward demand map and data table">
          <div className="map-column">
            <div className="section-heading"><div><p className="eyebrow">SPATIAL OVERVIEW</p><h2>{mode === "challenge" ? "Reserved ward comparison" : "Demand by ward"}</h2></div><span className="section-meta">{values.filter((row) => row.value !== null).length} WITH VALUES</span></div>
            {data.geometry.features.length ? <WardMap geometry={data.geometry} values={values} selectedId={selectedId} onSelect={onSelect} /> : <div className="map-unavailable" role="status"><span aria-hidden="true">⌖</span><strong>Ward boundaries unavailable</strong><p>The map cannot be drawn from these files. Use the searchable ward register alongside it.</p></div>}
            <div className="map-legend"><span className="small-label">{mode === "challenge" ? (measure === "actual" ? "RECORDED COUNTS" : "MODEL ESTIMATES") : "REPORT COUNT / CELL"}</span><div className="legend-gradient"><span>0</span><i aria-hidden="true" /><span>Higher</span></div><span className="legend-note">Missing values are shown in grey</span></div>
            <p className="map-note">{mode === "ward" ? "Observed wards show reports in the supplied extract. New wards show model estimates. Grey means no source value was supplied." : "Only reserved challenge wards carry comparison values. Choose Estimate or Recorded above; the table follows the same selection."}</p>
          </div>

          <aside className="detail-column" aria-label="Selected ward and table">
            <div className="section-heading detail-heading"><div><p className="eyebrow">WARD DETAILS</p><h2>{selected ? selected.ward_name : "Choose a ward"}</h2></div>{selected && <span className="ward-id">#{selected.ward_id}</span>}</div>
            <div className="selected-card" aria-live="polite">
              {selected ? <><span className={`status-pill ${valueSource(selected, mode, measure) === "Estimate" ? "target" : valueSource(selected, mode, measure) === "Recorded" ? "observed" : "unassigned"}`}>{valueSource(selected, mode, measure).toUpperCase()}</span><strong className="selected-value">{selected.value == null ? "—" : fmt.format(selected.value)}</strong><span className="selected-unit">{selected.value == null ? "No value for this filter" : `${CATEGORY_LABELS[category]} reports · ${month}`}</span>{mode === "challenge" && selected.actual != null && <span className="comparison-line">Estimate {fmt.format(selected.predicted ?? 0)} <i>·</i> Recorded {fmt.format(selected.actual)}</span>}</> : <p>Select a polygon or a ward in the table to see its value and source label.</p>}
            </div>

            <div className="table-heading"><div><p className="eyebrow">WARD REGISTER</p><span>{sortedValues.length} wards in current search</span></div><label className="search-box"><span className="sr-only">Search wards by name or ID</span><span aria-hidden="true">⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find a ward" type="search" /></label></div>
            <div className="table-wrap"><table><caption className="sr-only">Ward values for {CATEGORY_LABELS[category]} in {month}; select a row for details.</caption><thead><tr><th scope="col">WARD</th><th scope="col">SOURCE</th><th scope="col" className="numeric">COUNT</th></tr></thead><tbody>
              {sortedValues.map((row) => <tr key={row.ward_id} className={row.ward_id === selectedId ? "selected-row" : ""}><td><button className="ward-select" type="button" onClick={() => setSelectedId(row.ward_id)} aria-pressed={row.ward_id === selectedId}><span>{row.ward_name}</span><small>Ward {row.ward_id}</small></button></td><td><span className={`table-source ${valueSource(row, mode, measure) === "Estimate" ? "target" : valueSource(row, mode, measure) === "Recorded" ? "observed" : "unassigned"}`}>{valueSource(row, mode, measure)}</span></td><td className="numeric count-cell">{row.value == null ? "—" : fmt.format(row.value)}</td></tr>)}
              {sortedValues.length === 0 && <tr><td colSpan={3} className="empty-row">No wards match “{search}”. Clear the search to see the full list.</td></tr>}
            </tbody></table></div>
          </aside>
        </section>

        <section className="method-note"><span className="note-mark" aria-hidden="true">i</span><p><strong>Coverage note.</strong> “Recorded” means rows present in the supplied data extract. The local COV-1 evaluation fills absent combinations with zero within the extract span; it does not confirm that source collection was complete. June 2025 is partial.</p><span className="run-id">RUN {data.manifest.run_id}</span></section>
        <footer className="footer"><span>CitySight / Ward Pulse</span><span>Local static preview · no live city feed</span><a href="#top">Back to top ↑</a></footer>
      </>}
    </div>
  </main>;
}
