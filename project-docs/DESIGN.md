# GridLock — Design Document

> Living document. Updated every phase. Last updated: 2026-09-26 (Phase 1)

---

## Design Principles

1. **Evidence first.** Every number shown to the user traces to a source document. No numbers without provenance.
2. **Determinism is trust.** The engine calculates distance and score the same way every time. No AI makes scoring decisions.
3. **Honest uncertainty.** Geometry confidence levels (UNVERIFIED / INFERRED / CONFIRMED) are always visible.
4. **Offline-first fallback.** The map works with static GeoJSON if the API is unavailable.
5. **Hackathon pragmatism.** Beauty matters for judges. Every component must work in a live demo.

---

## UI Layout

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│  SIDEBAR (320px fixed)           │  MAP (flex 1)                       │
│                                  │                                      │
│  GridLock                        │  [WebGL map — MapLibre GL JS]        │
│  ─────────────────────────     │  ──────────────────────────  │
│  [offline badge if needed]       │  DESC lines: blue (#1f6feb)          │
│                                  │  GPC lines:  amber (#d97706)         │
│  Ranked opportunities list       │  Closest-pt: red dashed (#dc2626)    │
│  1. ProjectA ↔ ProjectB          │                                      │
│     12.4 km · Tier 1 · score 87  │                                      │
│  2. ...                          │                                      │
│                                  │                                      │
│  [Evidence drawer — on select]   │                                      │
│  Minimum distance: X.XXX km      │                                      │
│  Tier: 1 — [action]              │                                      │
│  Timeline: overlapping (0.73)    │                                      │
│  Confidence: 0.9                 │                                      │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Color System

| Element | Color | Hex | Meaning |
|---|---|---|---|
| DESC transmission lines | Blue | `#1f6feb` | Dominion Energy SC |
| Georgia Power lines | Amber | `#d97706` | Georgia Power |
| Closest-point segment | Red dashed | `#dc2626` | Minimum distance vector |
| Tier 1 badge | Green | TBD | Immediate coordination |
| Tier 2 badge | Yellow | TBD | Monitor / plan |
| Tier 3 badge | Gray | TBD | Informational |

---

## Map Layers (MapLibre)

| Layer ID | Type | Source | Filter | Notes |
|---|---|---|---|---|
| `lines` | line | `p` (GeoJSON) | LineString | 4px width, utility color |
| `pts` | circle | `p` (GeoJSON) | Point | 7px radius, utility color |
| `seg` | line | `seg` (GeoJSON) | — | 3px dashed red, closest-point segment |

---

## Evidence Drawer

Opens when user clicks an opportunity in the ranked list. Shows:

- Minimum distance (full geometry, metres → km, 3dp)
- Coordination tier + action description
- Timeline status + overlap fraction
- Confidence multiplier
- (Phase 3+) Source document link, extraction date, geometry confidence level
- (Phase 4) Cost/impact estimate

---

## Offline Fallback

If the FastAPI backend is unreachable, the frontend falls back to:
- `GET /static/projects_approved.geojson` (served by Vite dev server from `public/`)
- `GET /static/opportunities.json`

An orange warning badge appears in the sidebar. The map still renders.

---

## Phase 4 Design Additions (Planned)

- Cost/impact estimate panel in evidence drawer
- Geometry confidence indicator on each map feature
- Source citation tooltip on hover
- "Import New Utility" workflow (agent-assisted ingestion demo)
- Animated fitBounds transition on opportunity select
