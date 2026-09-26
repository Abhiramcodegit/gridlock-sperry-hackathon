# GridLock — Source Manifest (Phase 1A)

Generated: 2026-09-26  
Workstream: 1A — Source Scout  
Status: **Checkpoint 1 — Awaiting approval before any geometry/DB work**

---

## Hard Rules Applied

1. No CEII, confidential, or access-controlled material.
2. Every source must be a publicly accessible URL, verifiable on the open web.
3. No inferred, hallucinated, or assumed project data — extraction only from confirmed documents.
4. Every project row in the approved dataset requires: utility, project name, voltage_kv, description, source_url, source_date, geometry_status=UNVERIFIED.
5. Geometries start as NULL. No coordinate is entered without a cited public source.

---

## Source 1 — SCRTP March 2025 Meeting Presentation (DESC planned facilities)

| Field | Value |
|---|---|
| **URL** | https://www.scrtp.com/assets/pdfs/meeting-archives/scrtp-meeting-2025-03-05-presentation.pdf |
| **Publisher** | South Carolina Regional Transmission Planning (SCRTP) |
| **Document type** | Public stakeholder meeting presentation (PDF) |
| **Date** | 2025-03-05 |
| **Access** | Open public web — no login, no registration |
| **CEII risk** | None — published by SCRTP as a public planning document per FERC Order 1000 |
| **Retention** | Archived at scrtp.com; also archived at scrtp.stge.dominionenergyse.com |
| **Scope** | DESC 2025–2029 Planned Transmission Facilities |
| **Usable?** | YES |

### Projects Extracted (DESC, Source 1)

| project_id | project_name | utility | voltage_kv | in_service_date | description_excerpt | geometry_status |
|---|---|---|---|---|---|---|
| DESC-001 | Conway 230 kV Switching Station | DESC | 230 | 2025-12-01 | New switching station | UNVERIFIED |
| DESC-002 | Marion–Conway 230 kV Line | DESC | 230 | 2025-12-01 | New 230 kV line segment | UNVERIFIED |
| DESC-003 | Upgrade Purrysburg 230-115 kV Transformer | DESC | 230/115 | 2025-12-01 | Transformer upgrade | UNVERIFIED |
| DESC-004 | Carolina Forest 230-115 kV Substation: Add Transformer | DESC | 230/115 | 2025-12-01 | Add transformer to existing sub | UNVERIFIED |
| DESC-005 | Conway – Perry Road 230 kV Line | DESC | 230 | 2025-12-01 | New 230 kV line | UNVERIFIED |
| DESC-006 | Install 2nd Wassamassaw Transformer | DESC | 230/115 | 2026-09-01 | Second transformer at Wassamassaw | UNVERIFIED |
| DESC-007 | Replace Bluffton–Purrysburg 230 kV Limiting Elements | DESC | 230 | 2026-11-01 | Line upgrade | UNVERIFIED |
| DESC-008 | Indian Field–Wassamassaw 230 kV Line | DESC | 230 | 2026-11-01 | New 230 kV line | UNVERIFIED |
| DESC-009 | Indian Field 230-115 kV Substation | DESC | 230/115 | 2026-12-01 | New substation | UNVERIFIED |
| DESC-010 | Upgrade Batesburg 230-115 kV Transformer | DESC | 230/115 | 2026-12-01 | Transformer upgrade | UNVERIFIED |
| DESC-011 | Varnville to Nixville Tap 69 kV Rebuild to 115 kV | DESC | 115 | TBD | Line rebuild | UNVERIFIED |
| DESC-012 | Saluda Hydro – Bush River 115 kV #1 and #2 Tie Lines Rebuild | DESC | 115 | 2026-12-01 | Rebuild to SPDC 1272 standard | UNVERIFIED |
| DESC-013 | Okatie–McIntosh 115 kV Tie: Add Series Reactor (Deerfield SS) | DESC | 115 | TBD | Construct Deerfield Switching Station; install 9% series reactor | UNVERIFIED |
| DESC-014 | Scout 230 kV Substation and Fold-in | DESC | 230 | TBD | New 230 kV substation | UNVERIFIED |
| DESC-015 | Dawson 230 kV Substation and Fold-in / Rebuild | DESC | 230 | TBD | New substation + line rebuild | UNVERIFIED |
| DESC-016 | Long Savannah 115 kV Tap: Construct | DESC | 115 | TBD | New tap | UNVERIFIED |
| DESC-017 | Millrace 115 kV Tap: Construct | DESC | 115 | TBD | New tap | UNVERIFIED |
| DESC-018 | Catalina Solar 115 kV Switching Station: Construct | DESC | 115 | TBD | Solar interconnect switching station | UNVERIFIED |

---

## Source 2 — DESC 2026 Integrated Resource Plan (PDF)

| Field | Value |
|---|---|
| **URL** | https://cdn-dominionenergy-prd-001.azureedge.net/-/media/content/about/our-company/irp/pdfs/integrated-resource-plan-desc.pdf |
| **Publisher** | Dominion Energy South Carolina (DESC) |
| **Document type** | Public IRP filing (regulatory requirement) |
| **Date** | 2026-03-30 |
| **Access** | Open public web |
| **CEII risk** | None — publicly filed IRP |
| **Usable?** | YES — confirms transmission upgrade planning context; does not add geometry |
| **Note** | Confirms DESC transmission group is identifying upgrades and cost allocations. Corroborates Source 1 project list. Does not provide additional project-level geometry. |

---

## Source 3 — Georgia Power Transmission Planning

| Field | Value |
|---|---|
| **URL** | https://www.georgiatransmission.com (GTC) and https://www.georgiapowercleanenergy.com/transmission |
| **Publisher** | Georgia Transmission Corporation / Georgia Power |
| **Status** | **PENDING — URLs found but full project-level PDF not yet downloaded and verified** |
| **Usable?** | CONDITIONAL — requires Phase 1B document-level verification before any projects extracted |
| **Action required** | Manual download + page-level review before any Georgia Power rows enter SOURCE_MANIFEST |

---

## Extraction Rules

- Only rows with a confirmed `source_url` and confirmed `source_date` enter the approved dataset.
- `geometry_status` starts as `UNVERIFIED` for every row. It advances to `INFERRED` only after a cited public coordinate source is found, and to `CONFIRMED` only after Workstream 1C verification.
- `in_service_date` of TBD means the document listed the project without a confirmed date — it is NOT inferred.
- No DESC project names that appear only in `data/hypotheses/` are moved to the approved dataset without this manifest entry.
