/** A MapLibre case expression: missing values are grey, otherwise use the scale. */
export function demandColor(maximum: number) {
  const max = Math.max(maximum, 1);
  return ["case", ["==", ["get", "pulse_value"], null], "#d9dfdc",
    ["interpolate", ["linear"], ["get", "pulse_value"], 0, "#d5e6df", max * 0.25, "#6ea894", max * 0.6, "#14745e", max, "#064638"]];
}
