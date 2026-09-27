# OpenStreetMap substation coordinate capture (Phase 2 geometry research)

- Source: OpenStreetMap via Overpass API (https://overpass-api.de/api/interpreter)
- Data license: ODbL — © OpenStreetMap contributors
- Captured: 2026-09-26 (osm3s timestamp_osm_base 2026-09-27T00:03:04Z)
- Captured by: Kiro (direct Overpass query)
- Confidence: `inferred` — substation point used as a proxy for a line/tap/area
  project endpoint. NOT a published route for the specific project.

## Results

### Church Creek Substation (proxy for DESC-003 Long Savannah 115 kV Tap / DESC-004 Church Creek–Dawson)
- OSM way id: 185330726
- Coordinate (center): lat 32.8303196, lon -80.0702792
- Tags: power=substation; substation=transmission; voltage=230000;115000; name="Church Creek Substation"
- OSM link: https://www.openstreetmap.org/way/185330726
- Note: 230/115 kV transmission substation, Charleston County SC area. Matches the
  Church Creek–Dawson 230 kV context on SCRTP page 41. Proxy point, not a route.

### West McIntosh Substation (corroborates GPC-004 Effingham County 500 kV)
- OSM way id: 121624371
- Coordinate (center): lat 32.3543695, lon -81.1824528
- Tags: power=substation; substation=transmission; voltage=500000; operator="Georgia Power"; start_date=1986; name="West McIntosh Substation"
- OSM link: https://www.openstreetmap.org/way/121624371
- Note: 500 kV Georgia Power substation, Effingham County GA. Independently
  corroborates the GridCensus coordinate for GPC-004 (32.3537, -81.1807);
  the two points are ~180 m apart — effectively the same facility.

### Related McIntosh-area substations (context only)
- McIntosh Substation — way 121624352 — 32.3521162, -81.1751124 — 230 kV, Georgia Power
- McIntosh Combined Cycle Facility Substation — way 863571829 — 32.3487187, -81.1815513 — 230 kV generation

### Okatie (DESC-002) — NOT FOUND
- Overpass query for power=substation with name~"Okatie" in Beaufort County SC
  bbox returned zero elements. No OSM substation node exists for Okatie.
- DESC-002 remains geometry unresolved. No placeholder committed.

## IMPORTANT naming caution for DESC-002
DESC-002 is the "Okatie–McIntosh 115 kV tie." The "McIntosh" substations found
above are Georgia Power 500/230 kV facilities in Effingham County GA. These are
almost certainly NOT the SC endpoint of the DESC Okatie–McIntosh 115 kV tie.
Do not assign the GA West/McIntosh coordinate to DESC-002. Keep DESC-002
unresolved until a defensible SC-side Okatie/McIntosh 115 kV point is sourced.
