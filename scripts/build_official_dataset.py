#!/usr/bin/env python3
"""Build the canonical official-challenge dataset from the source-of-truth
spreadsheet (Sperry-Tech-Challenge/Projects_Overlaps.xlsx).

Deterministic, offline. Never calls Overpass/Nominatim. Never invents
coordinates: every coordinate written here comes verbatim from the spreadsheet.

Output schema (per project):
  id, utility, project_name,
  endpoint_a_name, endpoint_a_coords,
  endpoint_b_name, endpoint_b_coords,
  center_geometry, in_service_date,
  geometry_confidence, source_reference

Geometry rule:
  - Two known endpoints -> LineString(endpoint_a, endpoint_b), confidence "two_endpoints".
  - One endpoint "none"  -> Point(single known endpoint), confidence "endpoint_only".

Writes:
  data/official/projects_official.json   (list of normalized records)
  data/official/projects_official.geojson (FeatureCollection, geometry = full line/point)
"""
import json
import pathlib
from datetime import date, datetime

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Committed source of truth (tracked in git so the dataset rebuilds from a clean
# checkout). Falls back to the original challenge drop location only if the
# committed copy is absent; the committed copy is authoritative.
_XLSX_COMMITTED = ROOT / "data" / "official" / "source" / "Projects_Overlaps.xlsx"
_XLSX_LEGACY = ROOT / "Sperry-Tech-Challenge" / "Projects_Overlaps.xlsx"
XLSX = _XLSX_COMMITTED if _XLSX_COMMITTED.exists() else _XLSX_LEGACY
OUT_DIR = ROOT / "data" / "official"
SOURCE_REFERENCE = "data/official/source/Projects_Overlaps.xlsx#projects"


def _num(v):
    """Return a float coord if present, else None. Blank strings -> None."""
    if v is None or v == "":
        return None
    return float(v)


def _iso_date(v):
    """Normalize the spreadsheet in_service_date to ISO YYYY-MM-DD."""
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    # string like "12/31/2024" or "6/1/2033"
    s = str(v).strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {v!r}")


def _coords(lat, lon):
    """GeoJSON coordinate order is [lon, lat]. None if either missing."""
    if lat is None or lon is None:
        return None
    return [lon, lat]


def build():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb["projects"]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(h).strip() if h is not None else "" for h in rows[0]]
    idx = {name: i for i, name in enumerate(header)}

    records = []
    for row in rows[1:]:
        if row[idx["project_id"]] in (None, ""):
            continue
        lat_a, lon_a = _num(row[idx["lat_a"]]), _num(row[idx["lon_a"]])
        lat_b, lon_b = _num(row[idx["lat_b"]]), _num(row[idx["lon_b"]])
        a_coords = _coords(lat_a, lon_a)
        b_coords = _coords(lat_b, lon_b)

        known = [c for c in (a_coords, b_coords) if c is not None]
        if len(known) == 2:
            confidence = "two_endpoints"
            geometry = {"type": "LineString", "coordinates": [a_coords, b_coords]}
        elif len(known) == 1:
            confidence = "endpoint_only"
            geometry = {"type": "Point", "coordinates": known[0]}
        else:
            raise ValueError(f"{row[idx['project_id']]} has no known endpoint")

        rec = {
            "id": row[idx["project_id"]],
            "utility": row[idx["utility"]],
            "project_name": row[idx["project_name"]],
            "endpoint_a_name": row[idx["name_a"]] or None,
            "endpoint_a_coords": a_coords,
            "endpoint_b_name": row[idx["name_b"]] or None,
            "endpoint_b_coords": b_coords,
            "center_geometry": _coords(_num(row[idx["lat_center"]]), _num(row[idx["lon_center"]])),
            "in_service_date": _iso_date(row[idx["in_service_date"]]),
            "geometry_confidence": confidence,
            "source_reference": SOURCE_REFERENCE,
            # geometry is the analysis geometry used by the engine (full line/point)
            "geometry": geometry,
        }
        records.append(rec)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "projects_official.json").write_text(
        json.dumps(records, indent=2) + "\n"
    )

    features = []
    for r in records:
        props = {k: v for k, v in r.items() if k != "geometry"}
        features.append({"type": "Feature", "properties": props, "geometry": r["geometry"]})
    fc = {"type": "FeatureCollection", "features": features}
    (OUT_DIR / "projects_official.geojson").write_text(json.dumps(fc, indent=2) + "\n")

    return records


if __name__ == "__main__":
    recs = build()
    print(f"Wrote {len(recs)} official projects to {OUT_DIR}")
    for r in recs:
        print(f"  {r['id']:7} {r['geometry_confidence']:14} {r['geometry']['type']:11} isd={r['in_service_date']}")
