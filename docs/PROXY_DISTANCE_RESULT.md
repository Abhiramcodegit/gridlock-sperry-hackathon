# GridLock — Proxy Distance Result: GPC-004 ↔ DESC-003

Date: 2026-09-27
Branch: `research/source-validation`
Authorization: Human-approved geometry run on two inferred proxy points.

---

## Summary

| Field | Value |
|---|---|
| **Project A** | GPC-004 — Effingham County 500 kV |
| **Project B** | DESC-003 — Long Savannah 115 kV Tap |
| **Point A** | West McIntosh substation centroid (32.3543695, -81.1824528) |
| **Point B** | Church Creek substation centroid (32.8303196, -80.0702792) |
| **Geometry confidence (both)** | `inferred` — substation proxy, not confirmed project geometry |
| **proxy_distance_m** | **116,993.3 m** |
| **proxy_distance_km** | **116.993 km** |
| **Candidate threshold** | 40,000 m (40 km) |
| **Within threshold?** | **NO** |
| **Tier** | None — beyond 40 km |

---

## What this result IS

- The geodesic distance between the West McIntosh substation centroid (Georgia Power, Effingham County GA) and the Church Creek substation centroid (Charleston County SC).
- Both points are **inferred proxies**, not confirmed project geometries. West McIntosh is a proxy for the GPC-004 Effingham County 500 kV area project. Church Creek is a proxy for the DESC-003 Long Savannah 115 kV Tap.
- An honest negative result that validates the deterministic engine. The pair does not qualify as a coordination candidate at the proxy-point level.

## What this result IS NOT

- A verified project-to-project proximity measurement.
- Evidence that these projects cannot coordinate (the real geometries, when known, may be closer or farther).
- A basis for removing either project from the dataset.

---

## Computation details

### Method 1 — geodesic on WGS84 spheroid (authoritative, equivalent to PostGIS `ST_Distance` on `geography`)

```
pyproj.Geod(ellps='WGS84').inv(
    lon1=-81.1824528, lat1=32.3543695,
    lon2=-80.0702792, lat2=32.8303196
) → distance = 116,993.250 m
```

This is mathematically identical to the PostgreSQL query:

```sql
SELECT ST_Distance(
    ST_GeogFromText('POINT(-81.1824528 32.3543695)'),
    ST_GeogFromText('POINT(-80.0702792 32.8303196)')
);
-- Expected result: 116993.250 (meters, geodesic on WGS84 spheroid)
```

### Method 2 — UTM 17N planar cross-check (engine's `min_distance` method)

```
SRID: EPSG:32617 (UTM zone 17N)
shapely Point.distance() after reprojection from EPSG:4326
Result: 116,949.517 m
```

### Cross-check

| Method | Distance (m) | Distance (km) |
|---|---|---|
| Geodesic WGS84 | 116,993.250 | 116.993 |
| UTM 17N planar | 116,949.517 | 116.950 |
| **Delta** | **43.733 m** | **0.044 km** |

The 44 m delta is expected — the geodesic accounts for Earth curvature; the UTM projection introduces minor distortion at this distance. Both agree the pair is ~117 km apart, far beyond the 40 km threshold.

### Candidate filter (PostGIS equivalent)

```sql
SELECT ST_DWithin(
    ST_GeogFromText('POINT(-81.1824528 32.3543695)'),
    ST_GeogFromText('POINT(-80.0702792 32.8303196)'),
    40000  -- 40 km candidate radius
);
-- Expected result: FALSE
```

---

## Limitations

1. Both geometries are `inferred` substation proxy points, not confirmed project routes or endpoints. The actual planned facilities may have geometries that are closer or farther.
2. No PostGIS instance was available locally. The geodesic calculation used `pyproj.Geod(ellps='WGS84')`, which implements the same Karney geodesic algorithm that PostGIS uses for `ST_Distance` on `geography` type. Result will match PostGIS to sub-meter precision.
3. Neither record has been promoted. `review_status` remains `proposed` on both rows. The approved FeatureCollection is unchanged.
4. This result does not preclude other DESC ↔ GPC pairs from qualifying. DESC-002 (Okatie–McIntosh) remains unresolved and could be closer to GPC-004 if an SC-side coordinate is found.

---

## Records NOT modified

- `projects_proposed.csv`: untouched
- `projects_approved.geojson`: untouched (still empty)
- `review_status`: remains `proposed` on all 34 rows
