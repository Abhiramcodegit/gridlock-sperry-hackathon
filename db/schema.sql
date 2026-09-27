CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS projects (
  id text PRIMARY KEY, utility text NOT NULL, name text NOT NULL, project_type text, project_status text,
  voltage_kv numeric, description text, geom geography, geometry_type text,
  geometry_source text, geometry_method text,
  geometry_confidence text CHECK (geometry_confidence IN
    ('confirmed','confirmed_route','confirmed_point','inferred','inferred_endpoints','approximate','approximate_corridor','unresolved')),
  construction_start date, construction_end date, in_service_date date, date_basis text,
  source_url text, source_title text, source_date date, source_page text, source_excerpt text,
  review_status text NOT NULL DEFAULT 'proposed' CHECK (review_status IN ('proposed','approved','rejected')),
  ceii_checked boolean NOT NULL DEFAULT false, last_verified date);
CREATE INDEX IF NOT EXISTS projects_geom_idx ON projects USING gist (geom);

-- Cross-utility candidate pairs. Distance is only computed for pairs where BOTH
-- projects are APPROVED and have geometry. ST_DWithin provides the 40 km
-- candidate filter (geography => meters, geodesic). Temporal overlap on the
-- construction window is reported separately from geographic proximity.
CREATE OR REPLACE VIEW candidate_pairs AS
SELECT
  a.id AS a_id, b.id AS b_id,
  a.utility AS a_utility, b.utility AS b_utility,
  ST_Distance(a.geom, b.geom) AS distance_m,
  ST_Intersects(a.geom, b.geom) AS intersects,
  ST_ShortestLine(a.geom::geometry, b.geom::geometry) AS closest_segment,
  -- temporal overlap: number of overlapping days on the construction window
  -- (NULL when either window is unknown; never silently treated as overlapping)
  CASE
    WHEN a.construction_start IS NULL OR a.construction_end IS NULL
      OR b.construction_start IS NULL OR b.construction_end IS NULL THEN NULL
    ELSE GREATEST(0, (LEAST(a.construction_end, b.construction_end)
                      - GREATEST(a.construction_start, b.construction_start)) + 1)
  END AS overlap_days
FROM projects a
JOIN projects b
  ON a.utility < b.utility
 AND ST_DWithin(a.geom, b.geom, 40000)
WHERE a.review_status = 'approved' AND b.review_status = 'approved'
  AND a.geom IS NOT NULL AND b.geom IS NOT NULL;
