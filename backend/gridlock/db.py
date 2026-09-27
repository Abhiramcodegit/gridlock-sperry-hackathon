"""PostGIS-backed ingestion and opportunity query for GridLock.

Deterministic. No LLM decides anything here. All geographic math is done by
PostGIS (ST_DWithin candidate filter + ST_Distance on geography). Tier and
score reuse the same deterministic thresholds as the pure-Python engine.

Connection: set GRIDLOCK_DATABASE_URL, e.g.
  postgresql://postgres:PASSWORD@localhost:5432/gridlock
When unset, callers should fall back to the file-based path (see api.py).
"""
import csv
import json
import os
import pathlib
from typing import Optional

import psycopg

from . import config as C

DATA_CSV = pathlib.Path(__file__).resolve().parents[2] / "data" / "normalized" / "projects_proposed.csv"

# The CSV's confidence vocabulary -> the schema's CHECK vocabulary.
_CONFIDENCE_MAP = {
    "confirmed": "confirmed_point",
    "inferred": "inferred_endpoints",
    "approximate": "approximate_corridor",
    "unresolved": "unresolved",
    "": "unresolved",
}


def database_url() -> Optional[str]:
    return os.environ.get("GRIDLOCK_DATABASE_URL")


def connect(url: Optional[str] = None):
    url = url or database_url()
    if not url:
        raise RuntimeError("GRIDLOCK_DATABASE_URL is not set; no database to connect to.")
    return psycopg.connect(url)


def _clean_date(v: str) -> Optional[str]:
    v = (v or "").strip()
    return v or None


def _clean_num(v: str) -> Optional[str]:
    v = (v or "").strip()
    # voltages like "230/115" are not numeric; store NULL rather than fabricate one.
    if not v or not v.replace(".", "", 1).isdigit():
        return None
    return v


def ingest_csv(conn, csv_path: pathlib.Path = DATA_CSV, proposed_only: bool = True) -> int:
    """Load rows from projects_proposed.csv into the projects table.

    Only rows the source marks proposed are loaded by default. A row's geometry
    is stored only when the CSV provides GeoJSON; otherwise geom stays NULL.
    Returns the number of rows ingested.
    """
    rows = list(csv.DictReader(open(csv_path, newline="")))
    n = 0
    with conn.cursor() as cur:
        for r in rows:
            if proposed_only and r.get("review_status", "").strip() != "proposed":
                continue
            geojson = (r.get("geometry") or "").strip()
            conf = _CONFIDENCE_MAP.get((r.get("geometry_confidence") or "").strip(), "unresolved")
            cur.execute(
                """
                INSERT INTO projects (
                    id, utility, name, project_type, project_status, voltage_kv, description,
                    geom, geometry_type, geometry_source, geometry_method, geometry_confidence,
                    construction_start, construction_end, in_service_date, date_basis,
                    source_url, source_title, source_date, source_page, source_excerpt,
                    review_status, ceii_checked, last_verified)
                VALUES (%s,%s,%s,%s,%s,%s,%s,
                        CASE WHEN %s = '' THEN NULL ELSE ST_GeogFromGeoJSON(%s) END,
                        %s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s,%s,%s,
                        %s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                    geom = EXCLUDED.geom,
                    geometry_confidence = EXCLUDED.geometry_confidence,
                    review_status = EXCLUDED.review_status,
                    last_verified = EXCLUDED.last_verified
                """,
                (
                    r["id"], r["utility"], r["name"], r.get("project_type") or None,
                    r.get("project_status") or None, _clean_num(r.get("voltage_kv")), r.get("description") or None,
                    geojson, geojson,
                    r.get("geometry_type") or None, r.get("geometry_source") or None,
                    r.get("geometry_method") or None, conf,
                    _clean_date(r.get("construction_start")), _clean_date(r.get("construction_end")),
                    _clean_date(r.get("in_service_date")), r.get("date_basis") or None,
                    r.get("source_url") or None, r.get("source_title") or None,
                    _clean_date(r.get("source_date")), r.get("source_page") or None, r.get("source_excerpt") or None,
                    r.get("review_status") or "proposed",
                    (r.get("ceii_checked") or "false").strip().lower() == "true",
                    _clean_date(r.get("last_verified")),
                ),
            )
            n += 1
    conn.commit()
    return n


def find_opportunities(conn) -> list:
    """Return ranked cross-utility coordination opportunities from PostGIS.

    Distance and the 40 km candidate filter are computed by PostGIS on
    approved-geometry pairs only (via the candidate_pairs view). Returns an
    EMPTY LIST when no approved pair passes the filter — that is the correct
    answer, not an error.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT a_id, b_id, distance_m, intersects, "
            "ST_AsGeoJSON(closest_segment), overlap_days "
            "FROM candidate_pairs"
        )
        rows = cur.fetchall()

    out = []
    for a_id, b_id, distance_m, intersects, seg_json, overlap_days in rows:
        t = _tier(distance_m, intersects)
        if t is None:
            continue
        seg = json.loads(seg_json)["coordinates"] if seg_json else None
        timeline_status = "unknown" if overlap_days is None else (
            "no_overlap" if overlap_days == 0 else "overlap")
        out.append({
            "project_a": a_id,
            "project_b": b_id,
            "distance_m": round(float(distance_m), 1),
            "intersects": bool(intersects),
            "tier": t[0],
            "coordination_action": t[3],
            "timeline_status": timeline_status,
            "overlap_days": None if overlap_days is None else int(overlap_days),
            "closest_segment": seg,
        })
    return sorted(out, key=lambda o: o["distance_m"])


def _tier(distance_m: float, intersects: bool):
    if intersects or distance_m == 0:
        return C.TIERS[0]
    for name, mx, inc, action in C.TIERS[1:]:
        if distance_m < mx or (inc and distance_m == mx):
            return (name, mx, inc, action)
    return None
