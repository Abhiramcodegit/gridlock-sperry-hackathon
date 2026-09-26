# SCRTP March 5, 2025 — DESC project extract

Source: https://www.scrtp.com/assets/pdfs/meeting-archives/scrtp-meeting-2025-03-05-presentation.pdf  
Publisher: South Carolina Regional Transmission Planning (SCRTP)  
Meeting date: 2025-03-05  
Captured and independently checked: 2026-09-26  
Access: public, no login; no CEII marking observed in the published presentation.

## Extraction scope

The normalized DESC dataset uses the **Current DESC Transmission Expansion Plans** section (PDF pages/slides 30–48), not the **Santee Cooper committed facilities** table on pages/slides 24 and 50.

### Detailed DESC projects

| ID | Project | Status | Planned in-service | Source page |
|---|---|---|---|---|
| DESC-001 | Saluda Hydro – Bush River 115 kV #1 and #2 Tie Lines Rebuild | In Progress | December 2026 | 35 |
| DESC-002 | Okatie – McIntosh 115 kV Tie: Add Series Reactor | Planned | December 2028 | 37 |
| DESC-003 | Long Savannah 115 kV Tap: Construct | Planned | December 2028 | 39 |
| DESC-004 | Church Creek – Dawson 230 kV: Rebuild from Long Savannah to Dawson | Planned | December 2028 | 41 |
| DESC-005 | Winnsboro West 230-115 kV Sub and Fold-in: Construct | Planned | January 2028 | 43 |
| DESC-006 | Canadys-Ritter 115 kV: Rebuild SPDC 230/115 kV 1272 | In Progress | June 2028 | 45 |

### Listed DESC load-growth and solar projects

Page/slide 47 lists the following projects without individual status or in-service dates. Those fields remain unfilled in the normalized dataset.

- DESC-007 Scout 230 kV Sub and Fold-in: Construct
- DESC-008 Dawson 230 kV Sub and Fold-in: Construct and Rebuild
- DESC-009 Union Pier 115-13.8 kV Sub: Tap
- DESC-010 Harleyville 115 kV Transmission Tap: Construct (1.4 miles)
- DESC-011 Sherwood Tap: Construct Tap (voltage not stated)
- DESC-012 Wagener 115 kV Tap: Construct Tap
- DESC-013 Coit – Gills Creek 115 kV: Construct
- DESC-014 Cainhoy 115 kV Tap: Construct
- DESC-015 Jack Primus 115 kV Tap: Construct
- DESC-016 Coast Guard 115 kV Tap: Construct
- DESC-003 Long Savannah 115 kV Tap: Construct (already represented by its detailed page)
- DESC-017 Millrace 115 kV Tap: Construct
- DESC-018 Catalina Solar 115 kV Switching Station: Construct
- DESC-019 DESCSQ-1151 115 kV Switching Station: Construct; upgrade the 336 ACSR portion of the DESCSQ-1151 – Yemassee 115 kV line to 1272 ACSR

## Important correction

The prior `SOURCE_MANIFEST.md` mixed 11 Santee Cooper committed-facility records from pages/slides 24/50 with seven DESC records from pages/slides 35–47. The two lists belong to different utility sections. The normalized `DESC-*` rows now contain only records from the DESC section.

## Geometry restriction

The source contains schematic diagrams, not machine-readable routes or coordinates. All normalized geometry fields therefore remain blank and `geometry_confidence=unresolved`.
