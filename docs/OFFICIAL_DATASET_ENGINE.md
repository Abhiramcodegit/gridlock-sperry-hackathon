# Official Challenge Dataset & Overlap Engine

Canonical, offline pipeline for the 10 official challenge projects (5 DESC, 5 GPC)
and the cross-utility overlap engine that ranks coordination opportunities.

## Source of truth

`Sperry-Tech-Challenge/Projects_Overlaps.xlsx` (sheet `projects`). Every coordinate
in the normalized dataset is copied verbatim from that sheet. No coordinate is
invented, and no Overpass/Nominatim call is made at build or run time.

The sheet's `overlaps` sheet is used **only** as a regression oracle in tests
(`backend/tests/test_official_engine.py`), never as an engine input.

## Data build

`scripts/build_official_dataset.py` reads the spreadsheet and writes:

- `data/official/projects_official.json` — normalized records
- `data/official/projects_official.geojson` — FeatureCollection (analysis geometry)

### Normalized schema (per project)

| field | meaning |
|---|---|
| `id` | `DESC_n` / `GPC_n` |
| `utility` | utility name |
| `project_name` | official project name |
| `endpoint_a_name` / `endpoint_a_coords` | endpoint A name and `[lon, lat]` |
| `endpoint_b_name` / `endpoint_b_coords` | endpoint B name and `[lon, lat]` (may be `null`) |
| `center_geometry` | sheet-provided center `[lon, lat]` |
| `in_service_date` | ISO `YYYY-MM-DD` |
| `geometry_confidence` | `two_endpoints` or `endpoint_only` |
| `source_reference` | `Sperry-Tech-Challenge/Projects_Overlaps.xlsx#projects` |
| `geometry` | analysis geometry: `LineString` (two endpoints) or `Point` (endpoint_only) |

### Geometry rule

- Two known endpoints → `LineString(A, B)`, `geometry_confidence = "two_endpoints"`.
- One endpoint is "none" (blank in sheet) → `Point(known endpoint)`,
  `geometry_confidence = "endpoint_only"`.

`endpoint_only` projects: `DESC_1` (Hooks blank), `DESC_2` (Hooks blank),
`DESC_4` (Ft Johnson blank), `GPC_2` (Purrysburg blank).

## Overlap engine

`backend/gridlock/official_engine.py`

- Compares every DESC project to every GPC project — 5 × 5 = 25 pairs.
- **Primary metric:** closest-point distance between full geometries
  (projected to UTM 17N / EPSG:32617), never center-to-center.
- **Inclusion gate:** distance < 40 km (25 mi).
- **Secondary field:** absolute in-service date gap in days.
- **Coordination tier** (by closest-point distance):
  - touching/crossing → outage timing + crossing-structure coordination
  - < 1.6 km → shared right-of-way / access / permits
  - < 8 km → shared laydown yards / deliveries
  - < 40 km → shared crews / equipment
- **Output:** opportunities ranked by distance ascending. Each carries
  `distance_m/km/mi`, `day_gap`, `tier`, `coordination_action`, and per-project
  `confidence`.

Run it directly:

```
python -m gridlock.official_engine
```

## Computed opportunities (closest-point)

| rank | DESC | GPC | dist (km) | dist (mi) | day gap | tier | confidence (desc/gpc) |
|---|---|---|---|---|---|---|---|
| 1 | DESC_2 | GPC_1 | 0.000 | 0.000 | 3074 | crossing | endpoint_only / two_endpoints |
| 2 | DESC_3 | GPC_2 | 4.816 | 2.992 | 152 | shared_logistics | two_endpoints / endpoint_only |
| 3 | DESC_3 | GPC_3 | 5.466 | 3.396 | 517 | shared_logistics | two_endpoints / two_endpoints |
| 4 | DESC_1 | GPC_1 | 11.083 | 6.886 | 3074 | shared_crews | endpoint_only / two_endpoints |
| 5 | DESC_5 | GPC_2 | 13.574 | 8.434 | 365 | shared_crews | two_endpoints / endpoint_only |
| 6 | DESC_5 | GPC_3 | 14.225 | 8.839 | 730 | shared_crews | two_endpoints / two_endpoints |

`DESC_4`, `GPC_4`, and `GPC_5` do not appear in any opportunity.

## Divergence from the reference sheet

The sheet's `distance_mi` is **center-to-center**; the engine uses **closest-point**
distance. Per the task rules, the engine is not tuned to match the sheet. The
qualifying pair set and day gaps match the sheet exactly; only distances differ.

| pair | sheet dist (mi, center) | engine dist (mi, closest-point) | Δ (mi) |
|---|---|---|---|
| DESC_2 + GPC_1 | 4.09 | 0.000 | −4.09 |
| DESC_3 + GPC_2 | 5.65 | 2.992 | −2.66 |
| DESC_3 + GPC_3 | 7.55 | 3.396 | −4.15 |
| DESC_1 + GPC_1 | 8.01 | 6.886 | −1.12 |
| DESC_5 + GPC_2 | 14.34 | 8.434 | −5.91 |
| DESC_5 + GPC_3 | 14.81 | 8.839 | −5.97 |

Closest-point distances are consistently smaller, as expected: the closest points
of two line segments are at or nearer than their midpoints. The largest single
divergence is the **DESC_2 + GPC_1** pair, which computes to 0 m because
`DESC_2`'s only known endpoint (Thurmond Sub, 33.660127, −82.195931) is the exact
same coordinate as `GPC_1`'s endpoint B (THURMOND DAM #5, 33.660127, −82.195931).
The two projects share a physical endpoint — a genuine touch, not an artifact.

## Known limitations

- **Endpoint-only geometries.** Four projects have one blank endpoint and are
  modeled as a single point. Their true extent is a line, so real closest-point
  distances for pairs involving them are upper bounds (the actual line could be
  closer). This affects DESC_1, DESC_2, DESC_4, and GPC_2.
- **No route geometry.** Endpoints are substation points; the actual transmission
  routes between them are not published in the sheet, so the straight-line
  segment is an approximation of the corridor.
- **Distance vs the sheet.** Closest-point and center-to-center are different
  measures; they are not expected to match and were not reconciled.
- **In-service dates only.** The sheet provides in-service dates but not
  construction windows, so the engine reports an in-service date gap rather than a
  construction-overlap window.
- **Projection.** Distances use UTM 17N (EPSG:32617), accurate for the SC/GA
  border region; pairs far outside that zone would carry more projection error
  (not a concern for the qualifying set).
