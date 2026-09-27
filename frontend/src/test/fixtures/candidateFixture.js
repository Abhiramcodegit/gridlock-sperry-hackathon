// test/fixtures/candidateFixture.js
// ---------------------------------------------------------------------------
// TEST-ONLY fixture. NOT imported by any runtime/application module.
//
// Per F18, runtime code must not hardcode coordinates, distances, tiers, or
// pair lists. The application (App.jsx) therefore fetches candidate geometry
// at runtime from the static data asset:
//     frontend/public/static/candidates_proposed.geojson
// This file exists only so tests have a stable in-memory copy of that same
// derived data without a network fetch.
//
// Both points are INFERRED substation proxies (centroid of an OSM substation
// way), derived from data/normalized/projects_proposed.csv. They are NOT
// approved geometry, must never be assigned a coordination tier, and the
// distance between them is NOT a verified project-to-project distance.
//
// Counts (from the same CSV): 34 proposed records total; 2 with geometry
// (below); 32 with NO geometry.
// ---------------------------------------------------------------------------

export const PROPOSED_TOTAL = 34

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
    coordinates: [-80.0702792, 32.8303196],
  },
]

export const PROPOSED_WITHOUT_GEOMETRY = PROPOSED_TOTAL - CANDIDATE_RECORDS.length

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
