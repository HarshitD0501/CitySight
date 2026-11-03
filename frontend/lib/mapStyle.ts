/** Shared demand scale; translucent fills keep street labels visible. */
export function demandColor(value: number | null, maximum: number): string {
  if (value === null || !Number.isFinite(value)) return "#d9dfdc";
  const ratio = Math.max(0, Math.min(1, value / Math.max(1, maximum)));
  const stops = [0, 0.25, 0.6, 1];
  const colors = [[213, 230, 223], [110, 168, 148], [20, 116, 94], [6, 70, 56]];
  const end = Math.max(1, stops.findIndex((stop) => ratio <= stop));
  const fraction = (ratio - stops[end - 1]) / (stops[end] - stops[end - 1]);
  return `#${colors[end].map((channel, index) => Math.round(colors[end - 1][index] + fraction * (channel - colors[end - 1][index])).toString(16).padStart(2, "0")).join("")}`;
}

export function wardStyle(value: number | null, maximum: number, selected: boolean, streets: boolean) {
  return { fillColor: demandColor(value, maximum), fillOpacity: value === null ? 0.2 : selected ? 0.7 : streets ? 0.38 : 0.82,
    color: selected ? "#bf522d" : "#315b4e", weight: selected ? 3 : 1, opacity: selected ? 1 : 0.7 };
}
