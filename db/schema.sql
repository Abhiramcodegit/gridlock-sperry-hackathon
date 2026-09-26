CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE projects (
  id text PRIMARY KEY, utility text NOT NULL, name text NOT NULL, project_type text, project_status text,
  voltage_kv numeric, description text, geom geography NOT NULL, geometry_type text,
  geometry_source text, geometry_method text,
  geometry_confidence text CHECK (geometry_confidence IN ('confirmed_route','confirmed_point','inferred_endpoints','approximate_corridor','unresolved')),
  construction_start date, construction_end date, in_service_date date, date_basis text,
  source_url text NOT NULL, source_title text, source_date date, source_page text, source_excerpt text,
  review_status text NOT NULL DEFAULT 'proposed' CHECK (review_status IN ('proposed','approved','rejected')),
  ceii_checked boolean NOT NULL DEFAULT false, last_verified date);
CREATE INDEX projects_geom_idx ON projects USING gist (geom);
CREATE VIEW candidate_pairs AS
SELECT a.id a_id, b.id b_id, ST_Distance(a.geom,b.geom) distance_m,
       ST_Intersects(a.geom,b.geom) intersects,
       ST_ShortestLine(a.geom::geometry,b.geom::geometry) closest_segment
FROM projects a JOIN projects b ON a.utility < b.utility AND ST_DWithin(a.geom,b.geom,40000)
WHERE a.review_status='approved' AND b.review_status='approved';
