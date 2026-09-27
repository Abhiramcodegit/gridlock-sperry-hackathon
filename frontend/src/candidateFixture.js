// candidateFixture.js
// ---------------------------------------------------------------------------
// ISOLATED, NON-AUTHORITATIVE FIXTURE — FOR REVIEW ONLY.
//
// This file is a hand-derived snapshot of the two PROPOSED records that carry
// inferred proxy geometry in data/normalized/projects_proposed.csv. It exists
// only because no backend endpoint currently serves proposed geometry:
//   - /api/projects       -> approved projects only (currently an empty FC)
//   - /api/opportunities  -> approved-only coordination opportunities ([] today)
// See the "API gaps" note in AGENT_STATUS.md.
//
// DO NOT treat anything here as approved project geometry. Both points are
// INFERRED substation proxies (centroid of an OSM substation way), NOT the
// actual proposed facility footprints. They must never be assigned a
// coordination tier, and the ~116.993 km between them is NOT a verified
// project-to-project distance — it is the distance between two proxy points.
//
// Source of truth: data/normalized/projects_proposed.csv
//   GPC-004  Effingham County 500 kV   geometry_source: OSM way 121624371
//                                       (West McIntosh Substation) — inferred
//   DESC-003 Long Savannah 115 kV Tap   geometry_source: OSM way 185330726
//                                       (Church Creek Substation) — inferred
//
// Counts (from the same CSV): 34 proposed records total; 2 with geometry
// (below); 32 with NO geometry (surfaced as a sidebar count, not markers).
// ---------------------------------------------------------------------------

// Total proposed records in projects_proposed.csv.
export const PROPOSED_TOTAL = 34

// The two proposed records that carry inferred proxy geometry.
// Kept as plain records so the UI can build both markers and labels from them.
export const CANDIDATE_RECORDS = [
  {
    id: 'GPC-004',
    utility: 'GPC',
    name: 'Effingham County 500 kV',
    label: 'Proposed — inferred substation proxy',
    review_status: 'proposed',
    geometry_confidence: 'inferred',
    geometry_method: 'centroid_of_osm_way',
    geometry_source: 'OSM way 121624371 (West McIntosh Substation)',
    // [lon, lat]
    coordinates: [-81.1824528, 32.3543695],
  },
  {
    id: 'DESC-003',
    utility: 'DESC',
    name: 'Long Savannah 115 kV Tap',
    label: 'Proposed — inferred substation proxy',
    review_status: 'proposed',
    geometry_confidence: 'inferred',
    geometry_method: 'centroid_of_osm_way',
    geometry_source: 'OSM way 185330726 (Church Creek Substation)',
    // [lon, lat]
    coordinates: [-80.0702792, 32.8303196],
  },
]

// Number of proposed records that have NO geometry (34 total - 2 with geometry).
// Surfaced as a count in the sidebar; these are intentionally NOT drawn.
export const PROPOSED_WITHOUT_GEOMETRY = PROPOSED_TOTAL - CANDIDATE_RECORDS.length

// GeoJSON FeatureCollection for the candidate-review map layer.
// Properties are limited to what the layer needs to style and label points.
export const candidateFeatureCollection = {
  type: 'FeatureCollection',
  features: CANDIDATE_RECORDS.map((r) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: r.coordinates },
    properties: {
      id: r.id,
      utility: r.utility,
      name: r.name,
      label: r.label,
      review_status: r.review_status,
      geometry_confidence: r.geometry_confidence,
    },
  })),
}
