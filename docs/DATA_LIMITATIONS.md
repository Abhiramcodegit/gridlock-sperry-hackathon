# GridLock — Data Limitations

Last updated: 2026-09-26 (Phase 1 update)  
This document is a living record of what the dataset does and does not contain.

---

## What the Dataset Contains (After Phase 1A)

- 18 DESC transmission projects extracted from SCRTP March 2025 public presentation.
- Project names, voltages, in-service dates, and text descriptions only.
- No geometries. All `geometry_status` values are `UNVERIFIED`.
- No coordinates, no route maps, no GIS data.
- Source: one verified public document (SRC-001). IRP (SRC-002) used for corroboration only.

---

## What the Dataset Does NOT Contain

- **Georgia Power projects:** Pending source verification. Zero Georgia Power rows in the approved dataset until SRC-003 verification completes and receives human approval.
- **Geometries / coordinates:** No project has a confirmed geometry. The engine will not compute distances until at least two projects have CONFIRMED or INFERRED geometries with cited sources.
- **Cost estimates:** Not present in source documents reviewed so far.
- **Private or CEII data:** None included. Sources reviewed contain no CEII designation.
- **Substation GPS coordinates:** Not derived from the planning documents. Would require separate public source (e.g., EIA-860, OpenStreetMap, utility GIS portals).

---

## Geometry Uncertainty Levels (Defined)

| Status | Meaning |
|---|---|
| `UNVERIFIED` | Project name and description extracted; no coordinate source found yet |
| `INFERRED` | Coordinate estimated from substation name lookup against a public source (EIA-860, OSM); uncertainty radius ≥ 5 km |
| `CONFIRMED` | Coordinate verified against two independent public sources; uncertainty radius < 1 km |

---

## Known Gaps

1. SCRTP document lists projects by name and in-service date but does not include route maps or GPS endpoints.
2. Several projects list in-service date as TBD — schedule overlap cannot be computed for these until dates are confirmed in a later public filing.
3. The `hypotheses/` folder contains unverified project pairs (Jasper, Okatie, etc.) that are working hypotheses only — they are not in the approved dataset and must not be used in demo output.
4. Georgia Power source verification is incomplete as of Checkpoint 1.

---

## Approved Dataset Location

`data/approved_projects.csv` — intentionally empty until Phase 1 verification receives human approval and Georgia Power source is resolved.
