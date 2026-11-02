# CitySight geospatial decisions

Use MapLibre with supplied GeoJSON polygons, local fill/line styles and a searchable table. Official [GeoJSON source documentation](https://maplibre.org/maplibre-gl-js/docs/API/classes/GeoJSONSource/) supports this approach. The current data has 198 features; rendering/resource performance still needs measurement.

The main view distinguishes observed extract counts, target estimates and unassigned wards. Month/category filtering, legend, table and selected detail use the same validated artifact snapshot. Keyboard users can select through the table; hover cannot be the only access to values. Partial-period and provenance labels remain visible.

GeoJSON positions use longitude then latitude under [RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946). Haversine neighbor inputs in the Python model instead use latitude/longitude in radians; test the differing conventions. Avoid area calculations in geographic degrees.

Use a neutral map without external basemap, glyphs, sprites or fonts. Browser/WebGL failure preserves the table. No external globe code, imagery, deck.gl, Cesium or 3D dependency is needed or approved for this release. Prior upstream repository and licensing assertions are removed because they were not reverified and do not support the chosen architecture.

Detailed artifact and failure contracts live in [the contracts](../planning/02_CONTRACTS_AND_EVALUATION.md).
