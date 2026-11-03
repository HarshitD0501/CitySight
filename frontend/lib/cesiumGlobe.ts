import type { FeatureCollection, WardValue } from "./contracts";
import { demandColor } from "./mapStyle";
import { wardView } from "./globeView";

// A narrow adapter for the version-pinned browser SDK, not a replacement SDK declaration.
type Property = { getValue: () => unknown };
type Entity = { properties?: Record<string, Property>; polygon?: { material: unknown; outline: unknown; outlineColor: unknown; height: unknown } };
type Source = { entities: { values: Entity[] } };
type Color = { withAlpha: (alpha: number) => Color };
type Provider = { errorEvent: { addEventListener: (listener: () => void) => () => void } };
type Scene = {
  requestRender: () => void;
  pick: (position: unknown) => { id?: Entity } | undefined;
  globe: { baseColor: Color; enableLighting: boolean };
  renderError: { addEventListener: (listener: () => void) => () => void };
};
type Viewer = {
  canvas: HTMLCanvasElement; scene: Scene; clock: { shouldAnimate: boolean };
  dataSources: { add: (source: Source) => Promise<Source> };
  imageryLayers: { addImageryProvider: (provider: Provider) => unknown; removeAll: () => void };
  camera: {
    lookAt: (target: unknown, offset: unknown) => void; lookAtTransform: (matrix: unknown) => void;
    flyTo: (options: Record<string, unknown>) => void;
    positionCartographic: { height: number }; zoomIn: (amount: number) => void; zoomOut: (amount: number) => void;
  };
  isDestroyed: () => boolean; destroy: () => void; resize: () => void;
};
type SDK = {
  VERSION: string; Ion: { defaultAccessToken: string };
  Viewer: new (element: HTMLElement, options: Record<string, unknown>) => Viewer;
  Color: { fromCssColorString: (css: string) => Color };
  ConstantProperty: new (value: unknown) => unknown;
  ColorMaterialProperty: new (value: Color) => unknown;
  GeoJsonDataSource: { load: (data: FeatureCollection, options: Record<string, unknown>) => Promise<Source> };
  Cartesian3: { fromDegrees: (longitude: number, latitude: number, height?: number) => unknown };
  HeadingPitchRange: new (heading: number, pitch: number, range: number) => unknown;
  Matrix4: { IDENTITY: unknown };
  ScreenSpaceEventHandler: new (element: HTMLElement) => { setInputAction: (fn: (event: { position: unknown }) => void, type: unknown) => void; destroy: () => void };
  ScreenSpaceEventType: { LEFT_CLICK: unknown };
  OpenStreetMapImageryProvider: new (options: Record<string, unknown>) => Provider;
};
type GlobeWindow = Window & { Cesium?: SDK; CESIUM_BASE_URL?: string };
export const CESIUM_VERSION = "1.146.0";
const BASE = "https://cesium.com/downloads/cesiumjs/releases/1.146/Build/Cesium/";
const INTEGRITY = {
  script: "sha384-1lWK5deN/B+lLaUw4lk6xKp/L19ii/98SZLk6K8YthDskgvc+GbdixLzbCnSS2Wn",
  css: "sha384-ghEeMdcWWzRv/BPeUcX835vcKDGrxvROXisl/Btpv3GeekBUXTSPVcFJpI1Tcrgp",
};
let sdkPromise: Promise<SDK> | null = null;

function loadSDK(): Promise<SDK> {
  const host = window as GlobeWindow;
  if (sdkPromise) return sdkPromise;
  host.CESIUM_BASE_URL = BASE;
  sdkPromise = new Promise<SDK>((resolve, reject) => {
    const script = document.createElement("script");
    const css = document.createElement("link");
    let scriptReady = false, cssReady = false, finished = false;
    const end = (error?: Error) => {
      if (finished) return;
      if (!error && (!scriptReady || !cssReady)) return;
      finished = true; window.clearTimeout(timer);
      script.onload = script.onerror = css.onload = css.onerror = null;
      if (error || host.Cesium?.VERSION !== CESIUM_VERSION) {
        script.remove(); css.remove(); reject(error ?? new Error("Unexpected 3D engine version."));
      } else resolve(host.Cesium);
    };
    const timer = window.setTimeout(() => end(new Error("3D engine download timed out. The 2D map remains available.")), 20_000);
    script.src = `${BASE}Cesium.js`; script.integrity = INTEGRITY.script; script.crossOrigin = "anonymous"; script.async = true;
    css.rel = "stylesheet"; css.href = `${BASE}Widgets/widgets.css`; css.integrity = INTEGRITY.css; css.crossOrigin = "anonymous";
    script.onload = () => { scriptReady = true; end(); };
    css.onload = () => { cssReady = true; end(); };
    script.onerror = css.onerror = () => end(new Error("3D engine could not load. Check your connection or use the 2D map."));
    document.head.append(css, script);
  }).catch((error) => { sdkPromise = null; throw error; });
  return sdkPromise;
}

export type GlobeHandle = {
  update: (values: WardValue[], selected: string | null) => void;
  view: (kind: "wards" | "top" | "globe") => void;
  zoom: (direction: 1 | -1) => void;
  resize: () => void;
  destroy: () => void;
};

export async function createGlobe(container: HTMLElement, geometry: FeatureCollection, options: {
  signal: AbortSignal; onSelect: (wardId: string) => void; onError: (message: string) => void; onImageryError: () => void;
}): Promise<GlobeHandle> {
  const C = await loadSDK();
  options.signal.throwIfAborted();
  // No implicit ion services or embedded example token; keyless OSM + ellipsoid only.
  C.Ion.defaultAccessToken = "";
  const viewer = new C.Viewer(container, {
    baseLayer: false, baseLayerPicker: false, geocoder: false, timeline: false, animation: false,
    homeButton: false, sceneModePicker: false, navigationHelpButton: false, infoBox: false,
    selectionIndicator: false, fullscreenButton: false, requestRenderMode: true,
    maximumRenderTimeChange: Infinity, targetFrameRate: 30, shouldAnimate: false,
    showRenderLoopErrors: false,
  });
  const cleanup: Array<() => void> = [];
  const destroy = () => {
    if (viewer.isDestroyed()) return;
    cleanup.forEach((remove) => remove()); viewer.destroy();
  };
  options.signal.addEventListener("abort", destroy, { once: true });
  cleanup.push(() => options.signal.removeEventListener("abort", destroy));
  try {
    viewer.clock.shouldAnimate = false;
    viewer.scene.globe.baseColor = C.Color.fromCssColorString("#132c38");
    viewer.scene.globe.enableLighting = false;
    const imagery = new C.OpenStreetMapImageryProvider({ url: "https://tile.openstreetmap.org/", maximumLevel: 19 });
    let imageryFailed = false;
    cleanup.push(imagery.errorEvent.addEventListener(() => {
      if (imageryFailed || viewer.isDestroyed()) return;
      imageryFailed = true; viewer.imageryLayers.removeAll(); viewer.scene.requestRender(); options.onImageryError();
    }));
    viewer.imageryLayers.addImageryProvider(imagery);
    cleanup.push(viewer.scene.renderError.addEventListener(() => options.onError("The 3D scene could not render. Switched to the 2D map.")));
    const lost = (event: Event) => { event.preventDefault(); options.onError("The graphics context was lost. Switched to the 2D map."); };
    viewer.canvas.addEventListener("webglcontextlost", lost);
    cleanup.push(() => viewer.canvas.removeEventListener("webglcontextlost", lost));
    const source = await C.GeoJsonDataSource.load(geometry, { clampToGround: false, stroke: C.Color.fromCssColorString("#173f39"), fill: C.Color.fromCssColorString("#6ea894").withAlpha(0.55), strokeWidth: 1 });
    options.signal.throwIfAborted();
    await viewer.dataSources.add(source);
    const view = wardView(geometry);
    const setView: GlobeHandle["view"] = (kind) => {
      if (viewer.isDestroyed()) return;
      if (kind === "globe") {
        viewer.camera.flyTo({ destination: C.Cartesian3.fromDegrees(view.longitude, view.latitude, 20_000_000), orientation: { heading: 0, pitch: -Math.PI / 2, roll: 0 }, duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 1.2 });
      } else {
        viewer.camera.lookAt(C.Cartesian3.fromDegrees(view.longitude, view.latitude), new C.HeadingPitchRange(0, kind === "top" ? -Math.PI / 2 : -Math.PI / 3.6, view.range));
        viewer.camera.lookAtTransform(C.Matrix4.IDENTITY);
      }
      viewer.scene.requestRender();
    };
    setView("wards");
    const handler = new C.ScreenSpaceEventHandler(viewer.canvas);
    cleanup.push(() => handler.destroy());
    handler.setInputAction((event) => {
      const entity = viewer.scene.pick(event.position)?.id;
      const id = entity?.properties?.ward_id?.getValue();
      if (typeof id === "string") options.onSelect(id);
    }, C.ScreenSpaceEventType.LEFT_CLICK);
    return {
      update(values, selected) {
        if (viewer.isDestroyed()) return;
        const byId = new Map(values.map((row) => [row.ward_id, row]));
        const max = Math.max(1, ...values.map((row) => row.value ?? 0));
        for (const entity of source.entities.values) {
          if (!entity.polygon) continue;
          const id = String(entity.properties?.ward_id?.getValue() ?? "");
          const value = byId.get(id)?.value ?? null;
          const color = C.Color.fromCssColorString(id === selected ? "#ef8a46" : demandColor(value, max));
          // This keyless scene uses an ellipsoid, not terrain or building heights.
          entity.polygon.height = new C.ConstantProperty(0);
          entity.polygon.material = new C.ColorMaterialProperty(color.withAlpha(value === null ? 0.18 : id === selected ? 0.9 : 0.58));
          entity.polygon.outline = new C.ConstantProperty(true);
          entity.polygon.outlineColor = new C.ConstantProperty(C.Color.fromCssColorString(id === selected ? "#fff0b5" : "#244c42"));
        }
        viewer.scene.requestRender();
      },
      view: setView,
      zoom(direction) { const amount = Math.max(150, viewer.camera.positionCartographic.height * 0.3); if (direction === 1) viewer.camera.zoomIn(amount); else viewer.camera.zoomOut(amount); viewer.scene.requestRender(); },
      resize() { if (!viewer.isDestroyed()) { viewer.resize(); viewer.scene.requestRender(); } },
      destroy,
    };
  } catch (error) { destroy(); throw error; }
}
