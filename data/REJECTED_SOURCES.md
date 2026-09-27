# GridLock — Rejected and Unverified Sources (Phase 1D)

Generated: 2026-09-26  
Workstream: 1D — Restriction Guard output  
Status: **Checkpoint 1 — Awaiting approval**

This file records every source considered during Phase 1 that was rejected or is pending verification. No data from these sources has entered or will enter the approved dataset.

---

## Rejected Sources

| source_id | name | url_or_description | rejection_reason | rejected_by | date |
|---|---|---|---|---|---|
| REJ-001 | NERC CEII transmission line data | Internal NERC portal | CEII-designated — access-controlled, not public | Restriction Guard (automated rule) | 2026-09-26 |
| REJ-002 | Utility internal planning maps | Not publicly accessible | Not public — no URL available on open web | Restriction Guard | 2026-09-26 |
| REJ-003 | Any source requiring login/registration not yet reviewed | Multiple utility portals | Pending access review — not yet confirmed as public | Restriction Guard | 2026-09-26 |

---

## Pending Verification

| source_id | name | url | issue | required_action |
|---|---|---|---|---|
| SRC-003 | Georgia Power / GTC transmission project list | https://www.georgiapowercleanenergy.com/transmission | Unknown whether access-gated; project-level PDF not downloaded | Manual download + page review; if login required → moves to REJ-004 |

---

## Rules That Trigger Automatic Rejection

1. Source requires login, registration, or access request.
2. Source carries CEII designation or equivalent restricted notice.
3. Source URL is not reachable on the public web.
4. Source provenance is unknown (no publisher, no date).
5. Source is a secondary summary without a link to the original document.
6. Source is a news article, blog, or analyst report — acceptable for context only, never for project data extraction.

---

## Hypotheses Folder Note

`data/hypotheses/` contains speculative project-pair candidates (e.g., Jasper Port project, Okatie corridor). These are working hypotheses derived from regional development context, NOT extracted from verified documents. They are NOT approved dataset entries. They exist only to direct future source searches. They must not appear in demo output, engine results, or any user-facing UI until they graduate to SOURCE_MANIFEST with a verified public source.
