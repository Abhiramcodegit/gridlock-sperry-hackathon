# DESC-002 Okatie–McIntosh 115 kV — coordinate research (Phase 2)

Date: 2026-09-27
Researcher: Kiro
Outcome: **UNRESOLVED — no defensible source-backed coordinate found. No placeholder committed.**

DESC-002 remains `geometry_confidence=unresolved`, geometry empty, `review_status=proposed`.

---

## Constraints applied (per authorization)
- No community centroid.
- No Georgia Power / GA McIntosh facility coordinate.
- Only a defensible, source-backed coordinate is acceptable.

## Sources checked

### 1. OpenStreetMap (Overpass API) — NO RESULT
Query for any `power` feature named Okatie / Riverport / Sherwood in the
Beaufort/Jasper SC bbox (31.9,-81.2,32.6,-80.6) returned zero elements.
OSM has no Okatie substation node/way.

### 2. EIA / HIFLD public substation layer — NOT AVAILABLE
EIA FAQ (https://www.eia.gov/tools/faqs/faq.php?id=567&t=3) states directly
that EIA and HIFLD do not publish the location of electric substations. The
former HIFLD open substation layer is withdrawn. This route is closed —
confirms the earlier finding relayed by the research engine.

### 3. SC PSC docket 2023-115-E (Jasper–Okatie–Riverport) — REAL PROJECT, NO MACHINE-READABLE COORDINATE
- Docket detail: https://dms.psc.sc.gov/Web/Dockets/Detail/118543
- Dominion project page: https://www.dominionenergy.com/projects-and-facilities/electric-projects/power-line-projects/jasper-okatie-riverport
- Confirms the Okatie Substation is a real, named DESC facility: "The first
  230 kV line begins at the Jasper Generating Plant and ends at the Okatie
  Substation. The second 230 kV line begins at the Okatie Substation and ends
  at the new Riverport Substation." (public, published 2024)
- NOTE: this docket concerns 230 kV lines. DESC-002 is the Okatie–McIntosh
  **115 kV** tie (SCRTP p37). The Okatie Substation is likely the shared
  facility, but this must be confirmed, not assumed.

### 4. Dominion Jasper–Okatie–Riverport route map PDF — IMAGE ONLY, NO COORDINATE
- https://cdn-dominionenergy-prd-001.azureedge.net/-/media/content/about/power-line-projects/jasper-okatie-riverport/pdfs/jor-route-options-street-map.pdf
- Single-page rendered street map (2.6 MB). Labels "Okatie", "Riverport",
  "Substation", "Jasper" but the PDF text layer contains NO decimal-degree or
  DMS coordinates. Extracting a point would require hand-georeferencing the
  image, which yields an approximation I would be generating myself — not a
  source-published coordinate. Not committed.

## Recommendation

Two acceptable paths — human/orchestrator to decide:

**A. Leave DESC-002 unresolved (current state, safest).** Fully rule-compliant.
   The GPC-004 ↔ DESC-003 proxy pair already satisfied the ≥1 GPC + ≥1 DESC
   geometry gate; DESC-002 is not required for the engine to run.

**B. Hand-georeference the Okatie Substation from the Dominion route map**, label
   it `approximate`, and cite the route map PDF + the visual method. This is a
   self-derived approximation, not a published coordinate; acceptable only if
   the team explicitly allows `approximate` confidence for a visually estimated
   point. If chosen, it should be clearly flagged as visually estimated.

Kiro did NOT take path B unilaterally, because the authorization emphasized a
defensible source-backed coordinate and forbade centroids/proxies of the wrong
facility. Path B needs an explicit decision.
