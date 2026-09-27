# GridLock — Glossary

> For judges, contributors, and anyone reading the source documents.

---

## Domain Terms

**CEII (Critical Energy/Electric Infrastructure Information)**
A designation by the US Department of Energy for information whose release could pose a security risk to the electric grid. CEII-designated documents require access requests and cannot be used as public data sources. GridLock uses no CEII data.

**Coordination opportunity**
A situation where two transmission projects from different utilities are geographically close (within 40 km) and have overlapping construction schedules, suggesting potential to share costs, permits, or contractor mobilisation.

**Coordination tier**
A ranked classification of how urgent cross-utility coordination is:
- **Tier 1 (≤10 km):** Immediate outreach recommended. Potential for shared right-of-way or access road.
- **Tier 2 (10–25 km):** Monitor. Coordinate on permitting if schedules align.
- **Tier 3 (25–40 km):** Informational. Track for future planning.

**DESC (Dominion Energy South Carolina)**
A regulated electric utility serving central and coastal South Carolina. Files transmission planning documents with SCRTP.

**GPC / Georgia Power**
Georgia Power Company, a subsidiary of Southern Company. Serves most of Georgia. Plans transmission through the Georgia Transmission Corporation (GTC).

**Geometry status**
Indicates how well-verified a project's geographic coordinates are:
- `UNVERIFIED` — project extracted from document; no coordinate source found yet
- `INFERRED` — coordinate estimated from substation name lookup against a public source; uncertainty radius ≥ 5 km
- `CONFIRMED` — coordinate verified against two independent public sources; uncertainty radius < 1 km

**IRP (Integrated Resource Plan)**
A long-term utility planning document filed with state regulators describing how the utility plans to meet future demand. Publicly available for regulated utilities.

**PostGIS**
A spatial extension for PostgreSQL. Provides `ST_Distance` (minimum distance between full geometries, in metres on the spheroid) and `ST_DWithin` (efficient proximity filter using spatial index).

**SCRTP (South Carolina Regional Transmission Planning)**
A regional body that coordinates transmission planning across South Carolina utilities under FERC Order 1000. Publishes public meeting presentations and notes at scrtp.com.

**ST_Distance (PostGIS)**
`ST_Distance(geog_a, geog_b)` returns the minimum distance in metres between two complete geometries on the spheroid. GridLock uses this for all coordination distance calculations — never centre-to-centre approximations.

**Transmission line (230 kV / 115 kV)**
High-voltage power lines that carry electricity across long distances. 230 kV lines are bulk transmission (inter-regional); 115 kV lines are sub-transmission (regional distribution). GridLock tracks both.

---

## Technical Terms

**approved_projects.csv**
The authoritative dataset of verified transmission projects. Intentionally empty until Phase 1 approval. Only rows reviewed and approved by Abhiram enter this file.

**closest_segment**
The GeoJSON LineString connecting the two nearest points on two project geometries. Rendered as a dashed red line on the GridLock map.

**hypotheses/**
The `data/hypotheses/` folder contains speculative project-pair candidates for future research. These are NOT approved data and must never appear in engine output or the UI.

**MCP (Model Context Protocol)**
An open protocol that allows AI systems to interact with external tools and services (GitHub, filesystems, databases) through structured tool calls. Used by Perplexity to read and write this repository directly.

**Offline fallback**
When the FastAPI backend is unavailable, the GridLock frontend loads static GeoJSON files from `/static/`. An orange badge notifies the user.

**Source manifest**
`data/SOURCE_MANIFEST.md` — the authoritative record of every public document reviewed, with URL, publisher, date, CEII check result, and extracted project list.

**Verification ledger**
`data/VERIFICATION_LEDGER.md` — one row per source, recording which verification steps passed and whether the source is APPROVED, PENDING, or REJECTED.
