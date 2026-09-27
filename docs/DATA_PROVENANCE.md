# GridLock — Data Provenance

> **Agent 4 — documentation & evidence.** This document traces every dataset
> GridLock uses back to a public source, states how each geometry was derived,
> and records the limits of what the data can support. No CEII, no
> access-controlled material, and no private grid data is used anywhere.

Last updated: 2026-09-27

---

## Two data tracks, kept separate on purpose

GridLock has two clearly separated datasets. Confusing them is the most common
way to overstate a result, so they are documented apart here.

| Track | File | Role | State |
|---|---|---|---|
| **A. Official challenge dataset** | `Sperry-Tech-Challenge/Projects_Overlaps.xlsx` | Canonical starter dataset + answer key supplied with the challenge | 10 projects, 6 precomputed overlaps |
| **B. GridLock ingestion pipeline** | `data/normalized/projects_proposed.csv` → `data/approved/projects_approved.geojson` | Our own provenance-gated ingestion of live public filings | 34 proposed rows, **0 approved** |

Everything the demo, methodology, and cost docs describe is grounded in
**Track A**, the official dataset, and is computed by the **offline reference
engine** (`official_engine.py`), not the live API. Track B is our stricter,
still-in-review research pipeline; its approved set is intentionally empty and
its engine correctly returns `[]`. See [`DATA_LIMITATIONS.md`](DATA_LIMITATIONS.md)
for the full Track B posture.

### The five result surfaces (do not conflate)

To avoid overstating any result, GridLock's outputs are reported on five
distinct surfaces:

1. **Spreadsheet center-to-center** — `Projects_Overlaps.xlsx` Sheet 2 answer
   key (miles, midpoint-to-midpoint).
2. **Offline reference engine closest-point** — `official_engine.py` over Track
   A; the source of the six flagged pairs and their closest-point distances.
3. **Conservative production API** — `GET /opportunities` returns `[]` today
   because nothing in Track B is human-approved.
4. **Frontend candidate/proxy display** — the map can render inferred candidate
   geometry for display only; of the 34 proposed Track B records, **32 carry no
   geometry** and the 2 that do are proxy points, never approved opportunities.
5. **Official reference results** — the six overlaps from surface 2, presented as
   the demo's headline. Distinct from the live API (surface 3).

---

## Track A — the official XLSX as the canonical starter dataset

`Projects_Overlaps.xlsx` ships inside the official challenge package
(`Sperry-Tech-Challenge/`). It is the canonical starter dataset and the answer
key the challenge grades against. It has two sheets:

- **Sheet 1 — 10 projects** (5 DESC + 5 GPC). Each row carries a project id,
  utility, project name, two named endpoints with latitude/longitude (some
  projects locate only one endpoint), a computed center point, and a planned
  in-service date.
- **Sheet 2 — 6 overlaps** (the answer key). Each row is a cross-utility pair
  with a center-to-center distance in miles and an in-service-date gap in days.

### Per-project source fields (Sheet 1)

Every project row provides:

| Field | Meaning |
|---|---|
| `id` | Stable identifier (DESC_1..DESC_5, GPC_1..GPC_5) |
| `utility` | DESC or GPC |
| `project name` | Full project name as published |
| endpoint A (lat, lon) | First named terminal (substation) |
| endpoint B (lat, lon) | Second named terminal, or `none` if only one located |
| center point | Midpoint of the two endpoints; if one endpoint, the center equals it |
| in-service date | Planned in-service date |

The 10 projects and their endpoints:

| id | utility | project name | in-service |
|---|---|---|---|
| DESC_1 | DESC | Stevens Creek – Hooks 115 kV / LR Plumb Branch 46 kV Rebuilds | 12/31/2024 |
| DESC_2 | DESC | Hooks – Thurmond 115 kV Tie: Rebuild | 12/31/2024 |
| DESC_3 | DESC | Jasper – Okatie 230 kV #2: Construct | 12/31/2025 |
| DESC_4 | DESC | Queensboro – Ft Johnson 115 kV & Queensboro–Bayfront 115 kV | 12/31/2023 |
| DESC_5 | DESC | Okatie – Bluffton 115 kV: Rebuild | 12/31/2025 |
| GPC_1 | GPC | Evans Primary – Thurmond Dam (USA) #5 115 kV Rebuild | 6/1/2033 |
| GPC_2 | GPC | SAV: McIntosh – Purrysburg 230 kV Reactors | 6/1/2026 |
| GPC_3 | GPC | SAV: Goshen (SAV) – McIntosh 115 kV Line Rebuild | 6/1/2027 |
| GPC_4 | GPC | Mitchell – North Tifton 230 kV Reconductor | 6/1/2026 |
| GPC_5 | GPC | Jesup – Ludowici Primary 115 kV Rebuild | 6/1/2025 |

### Upstream sources behind the official dataset

The XLSX draws its project lists and details from two public filings shipped in
the same challenge package:

- **DESC projects and cost tables:** `Project Listings/Dominion Energy/
  2024-2028-2million-and-above-project-descriptions.pdf` — a 44-page Dominion
  filing, one project per page, each with name, project ID, description, need,
  status, planned in-service date, and a year-by-year cost breakdown with a
  Total. This is the source of truth for DESC project details and the cost
  anchors used in [`COST_ESTIMATE.md`](COST_ESTIMATE.md).
- **GPC projects:** `Project Listings/Georgia Power/
  2025 IRP Volume 3 PUBLIC DISCLOSURE.pdf` — the 668-page public Georgia Power
  transmission plan appendix.

Both are public regulatory filings. Neither is CEII.

---

## Geometry derivation method

### Track A (official dataset)

The XLSX supplies endpoint coordinates directly. Per the challenge's
`Finding_Real_Locations_Guide.docx`, those coordinates originate from
**OpenStreetMap** (`power=substation` / `power=line` features filtered by
operator name within a bounding box, exported as GeoJSON and matched to the
project list), then confirmed against the PDF descriptions, zones, and counties.
Where a same-named substation sits in the wrong county, the guide flags it as a
lower-confidence match rather than accepting it.

### Track B (GridLock pipeline)

Two proposed rows carry geometry, both derived as **substation proxy points**
from public OpenStreetMap ways:

- **GPC-004** (Effingham County 500 kV): `centroid_of_osm_way` of West McIntosh
  Substation (OSM way 121624371), corroborated against a public HIFLD-derived
  record (~180 m agreement). Confidence: `inferred`.
- **DESC-003** (Long Savannah 115 kV Tap): `centroid_of_osm_way` of Church Creek
  Substation (OSM way 185330726). Confidence: `inferred`.

**DESC-002** (Okatie–McIntosh 115 kV) is deliberately left `unresolved` — the
coordinate research (`data/raw/desc/desc002_okatie_coordinate_research_2026-09-27.md`)
found no defensible source-published coordinate, so **no placeholder was
committed**. A blank is more honest than a fabricated point.

---

## The `endpoint_only` limitation

Both tracks locate projects by their **endpoints (terminal substations)**, not
by the actual routed path of the transmission line between them. This is an
`endpoint_only` representation, and it has real consequences:

- A transmission line is a corridor, not a pair of points. A 60 km line can pass
  within a few km of another utility's facility even though its two endpoints
  are far from that facility.
- Center-to-center distance (used by the official Sheet 2) compresses each
  project to a single midpoint, which can overstate or understate how close two
  projects actually come to each other.
- Where only one endpoint is located (`none` in Sheet 1), the "center" collapses
  to that single point, further reducing spatial fidelity.

GridLock's engine mitigates this by computing **closest-point distance between
full geometries** rather than center-to-center (see
[`METHODOLOGY.md`](METHODOLOGY.md)). But the underlying geometry is still
endpoint-derived: until a published route polyline exists for a project, the
"line" is an approximation anchored on its terminals. Every distance figure
should be read as *endpoint/proxy proximity*, not surveyed route proximity.

---

## No CEII — public filings only

GridLock uses **only publicly available information**:

- Official challenge package filings (Dominion 2M+ project descriptions PDF,
  Georgia Power 2025 IRP Volume 3 **Public Disclosure** PDF, `Projects_Overlaps.xlsx`).
- Publicly published SCRTP / DESC / Georgia Power planning material.
- OpenStreetMap for public substation geometry.

No **CEII (Critical Energy Infrastructure Information)**, no access-controlled
data, and no otherwise non-public grid data is ingested, stored, or displayed
anywhere in GridLock. Every non-hypothesis row in the pipeline cites a public
source URL, title, date, and page, and carries a CEII-checked flag. This is a
hard, non-negotiable rule.

---

Related: [`METHODOLOGY.md`](METHODOLOGY.md) · [`COST_ESTIMATE.md`](COST_ESTIMATE.md)
· [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) · [`DATA_LIMITATIONS.md`](DATA_LIMITATIONS.md)
· [`../README.md`](../README.md)
