# GridLock — Source Manifest (Checkpoint 1 correction)

Generated: 2026-09-26  
Status: **source extraction complete; geometry review remains blocked**

## Hard rules

1. Use only open public sources; exclude CEII, confidential, and access-controlled material.
2. Never infer unpublished project dates, status, voltage, or geometry.
3. Every normalized record retains source URL, title, date, page, excerpt, review state, and last-verified date.
4. All geometries start blank and unresolved until a separate cited public coordinate/route source is verified.
5. A candidate pair based only on county or place-name proximity is a research hypothesis, not an engine result.

## SCRTP March 2025 presentation

| Field | Value |
|---|---|
| URL | https://www.scrtp.com/assets/pdfs/meeting-archives/scrtp-meeting-2025-03-05-presentation.pdf |
| Publisher | South Carolina Regional Transmission Planning (SCRTP) |
| Date | 2025-03-05 |
| Access | Public; no login |
| Status | Extracted and independently checked 2026-09-26 |
| DESC scope | Pages/slides 30–48, “Current DESC Transmission Expansion Plans” |
| Result | 19 unique DESC project records: 6 detailed records plus 13 additional unique list-only records |

The previous manifest incorrectly treated the Santee Cooper committed-facilities table on pages/slides 24/50 as DESC data. That table contains Conway, Marion–Conway, Purrysburg, Wassamassaw, Indian Field, Varnville, and other Santee Cooper projects; those records were not transcribed as `DESC-*`.

Verified DESC records now appear in `data/normalized/projects_proposed.csv`. Exact extraction notes are in `data/raw/desc/scrtp_meeting_2025-03-05_desc_extract.md`.

## Georgia Power project page

| Field | Value |
|---|---|
| URL | https://www.georgiapower.com/about/grid-reliability/grid-improvements/grid-projects/transmission-projects.html |
| Publisher | Georgia Power |
| Access | Public; no login |
| Status | Extracted and independently checked 2026-09-26 |
| Result | 9 records retained from Kiro's extraction |
| Correction | `Callaway Road – Thomson Primary` and `Effingham County` are “Area Project,” not “New Transmission Line.” |
| Known omission | The live page also lists `Tomochichi – Towaliga River 230 kV`; it was not present in the earlier raw capture and is not added until its project-page provenance is captured consistently. |

The Georgia Power listing gives no record-specific in-service dates or route coordinates in the extracted table. Dates remain unpublished and geometry remains unresolved.

## Current dataset

- `projects_proposed.csv` has 34 rows: 6 explicit hypotheses, 9 Georgia Power source-backed proposals, and 19 DESC source-backed proposals.
- No source-backed record is approved yet.
- No geometry exists, so PostGIS distance, 40 km filtering, and cross-utility ranking remain disabled.
