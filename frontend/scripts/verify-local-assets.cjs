"use strict";

// Checks app syntax and D3-exported JSON contracts without booting Next.js.
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const assert = require("node:assert/strict");
const ts = require(process.env.TS_COMPILER_PATH || "typescript");
const root = path.resolve(__dirname, "..");
const sources = [
  "app/layout.tsx", "app/page.tsx", "components/Dashboard.tsx",
  "components/WardMap.tsx", "lib/contracts.ts", "lib/mapStyle.ts", "next.config.ts", "eslint.config.mjs",
];
let syntaxErrors = 0;
for (const relative of sources) {
  const file = path.join(root, relative);
  const kind = relative.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const parsed = ts.createSourceFile(relative, fs.readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true, kind);
  for (const diagnostic of parsed.parseDiagnostics) {
    syntaxErrors++;
    process.stderr.write(`${relative}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, " ")}\n`);
  }
}
if (syntaxErrors) process.exitCode = 1;

const contractPath = path.join(root, "lib/contracts.ts");
const compiled = ts.transpileModule(fs.readFileSync(contractPath, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
}).outputText;
const contract = new Module(contractPath, module);
contract._compile(compiled, contractPath);
const names = ["manifest.json", "predictions.json", "observations.json", "wards.geojson", "challenge.json", "metrics.json"];
const assets = names.map((name) => JSON.parse(fs.readFileSync(path.join(root, "public/data", name), "utf8")));
const checked = contract.exports.validateDashboardAssets(assets);
assert.equal(contract.exports.formatMonth("2024-01"), "January 2024");
assert.equal(contract.exports.formatMonth("2025-06"), "June 2025");
assert.throws(() => contract.exports.formatMonth("2025-13"), /YYYY-MM/);
const month = checked.manifest.target_months[0];
const category = checked.manifest.categories[0];
const values = contract.exports.buildWardValues(checked, month, category, "ward", "predicted");
const observed = checked.observations.records.find((row) => row.month === month && row.category_group === category);
const estimate = checked.predictions.records.find((row) => row.month === month && row.category_group === category);
assert.equal(values.find((row) => row.ward_id === observed.ward_id).value, observed.observed_count);
assert.equal(values.find((row) => row.ward_id === estimate.ward_id).value, estimate.predicted_count);
assert.equal(contract.exports.filteredChallengeMetrics(checked, month, category).count, 12);
const challengeEstimates = contract.exports.buildWardValues(checked, month, category, "challenge", "predicted");
const challengeActuals = contract.exports.buildWardValues(checked, month, category, "challenge", "actual");
assert.equal(challengeEstimates.filter((row) => row.value !== null).length, 12);
assert.equal(challengeActuals.filter((row) => row.value !== null).length, 12);
const challengeRow = challengeEstimates.find((row) => row.value !== null);
assert.equal(contract.exports.valueSource(challengeRow, "challenge", "predicted"), "Estimate");
assert.equal(contract.exports.valueSource(challengeRow, "challenge", "actual"), "Recorded");
const noGeometry = contract.exports.validateDashboardAssets([assets[0], assets[1], assets[2], null, assets[4], assets[5]], "Ward geometry unavailable.");
assert.equal(noGeometry.geometry.features.length, 0);
assert.ok(noGeometry.geometryError);
assert.ok(contract.exports.buildWardValues(noGeometry, month, category, "ward", "predicted").length > 0);
const noGeometryChallenge = contract.exports.buildWardValues(noGeometry, month, category, "challenge", "predicted");
const coverage = contract.exports.challengeCoverage(noGeometryChallenge, checked.challenge.challenge_wards);
assert.equal(coverage.observed, 12);
assert.equal(coverage.estimated, noGeometryChallenge.length - 12);
assert.equal(coverage.noData, 0);
assert.throws(() => contract.exports.assetUrl("../secrets.json"), /local file names/);
assert.throws(() => contract.exports.validateDashboardAssets([assets[0], { ...assets[1], run_id: "wrong" }, ...assets.slice(2)]), /schema or run ID/);
JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
JSON.parse(fs.readFileSync(path.join(root, "tsconfig.json"), "utf8"));
const mapPath = path.join(root, "lib/mapStyle.ts");
const mapModule = new Module(mapPath, module);
mapModule._compile(ts.transpileModule(fs.readFileSync(mapPath, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
}).outputText, mapPath);
const expression = mapModule.exports.demandColor(100);
assert.equal(expression.length, 4); // case, condition, missing color, interpolation fallback
assert.equal(expression[3][0], "interpolate");
const { validateStyleMin } = require("@maplibre/maplibre-gl-style-spec");
const styleErrors = validateStyleMin({
  version: 8,
  sources: { wards: { type: "geojson", data: { type: "FeatureCollection", features: [] } } },
  layers: [{ id: "ward-fills", type: "fill", source: "wards", paint: { "fill-color": expression } }],
});
assert.deepEqual(styleErrors.map((error) => error.message), [], "MapLibre must accept the fill-color expression");

async function verifyFetchFailures() {
  const signal = new AbortController().signal;
  const unavailable = async () => { throw new TypeError("network unavailable"); };
  const geometry = await contract.exports.fetchAsset("wards.geojson", true, signal, unavailable);
  assert.equal(geometry.data, null);
  assert.match(geometry.geometryError, /network unavailable/);
  await assert.rejects(contract.exports.fetchAsset("predictions.json", false, signal, unavailable), /network unavailable/);
  const aborted = new AbortController();
  aborted.abort();
  await assert.rejects(contract.exports.fetchAsset("wards.geojson", true, aborted.signal, unavailable), /network unavailable/);
  process.stdout.write(`Syntax parse ${syntaxErrors ? "FAILED" : "PASS"}; asset contract and fallback regression checks PASS; wards=${checked.geometry.features.length}, prediction rows=${checked.predictions.records.length}, observation rows=${checked.observations.records.length}, challenge rows=${checked.challenge.records.length}\n`);
}
verifyFetchFailures().catch((error) => { console.error(error); process.exitCode = 1; });
