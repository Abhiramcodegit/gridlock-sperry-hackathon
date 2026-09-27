# GridLock — Data Limitations

Last updated: 2026-09-26 (Checkpoint 1 source correction)

## What the proposed dataset contains

- 19 unique DESC projects from the **Current DESC Transmission Expansion Plans** section of the SCRTP March 5, 2025 presentation.
- 9 Georgia Power projects from the public Transmission Expansion & Upgrades page.
- Record-level source URL, source title/date, source page or web marker, excerpt, review state, CEII check flag, and last-verification date.
- 6 explicitly labeled hypothesis rows retained separately from source-backed proposals.

## What it does not contain

- Approved production records: every source-backed row remains `review_status=proposed` pending human approval.
- Project geometries, routes, or coordinates: all geometry fields are blank and `geometry_confidence=unresolved`.
- Construction windows: the reviewed sources do not provide both construction start and end dates.
- Per-project Georgia Power in-service dates: the listing provides project names, counties/regions, and types, but not record-specific dates.
- Verified distance results: without geometry, `ST_DWithin` and `ST_Distance` cannot establish a cross-utility pair.

## Source correction

The earlier source manifest mixed Santee Cooper committed facilities from PDF pages/slides 24/50 with the DESC project section on pages/slides 30–48. The normalized `DESC-*` records now use only the DESC section. The Santee Cooper records may be added later under a separate utility code after a dedicated extraction and review.

The DESC section yields 19 unique records, not 18: six detailed project pages and fourteen list entries, with Long Savannah appearing in both places and deduplicated once.

## Candidate-pair caution

`GPC-004 Effingham County 500 kV` and DESC projects containing Bluffton, Okatie, or Long Savannah are geographic research leads only. County/name proximity does not prove that two project geometries are within 40 km. The product must not display such a pair as verified until source-backed geometries are approved and the deterministic engine computes the minimum geometry distance.

## Remaining gate

1. Human review of all 28 source-backed proposed records.
2. Decide whether to add the live-page `Tomochichi – Towaliga River 230 kV` record after a matching raw source capture is stored.
3. Locate and verify public geometry sources.
4. Resolve the schema mismatch: proposed records intentionally permit blank geometry, while `db/schema.sql` currently defines production `geom geography NOT NULL`.
5. Promote only approved records into `data/approved_projects.csv` and the production database.
