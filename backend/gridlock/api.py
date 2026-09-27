"""GridLock FastAPI app.

/opportunities is PostGIS-backed when GRIDLOCK_DATABASE_URL is set: it ingests
the proposed rows from projects_proposed.csv and runs the deterministic
candidate query (ST_DWithin 40 km filter + ST_Distance on approved-geometry
pairs). When no database is configured, it falls back to the file-based engine.

An empty array is the correct answer when no approved pair passes the filter.
"""
import json
import pathlib

from fastapi import FastAPI

from .engine import Project, find_opportunities as find_opportunities_file
from . import db

app = FastAPI(title="GridLock")

ROOT = pathlib.Path(__file__).resolve().parents[2]
APPROVED = ROOT / "data" / "approved" / "projects_approved.geojson"


def _load_file_projects():
    if not APPROVED.exists():
        return []
    fc = json.loads(APPROVED.read_text())
    out = []
    for f in fc.get("features", []):
        p = f["properties"]
        out.append(Project(
            p["id"], p["utility"], p["name"], f["geometry"],
            p.get("geometry_confidence", "unresolved"),
            review_status=p.get("review_status", "proposed"),
        ))
    return out


@app.get("/health")
def health():
    return {"ok": True, "backend": "postgis" if db.database_url() else "file"}


@app.get("/projects")
def projects():
    if APPROVED.exists():
        return json.loads(APPROVED.read_text())
    return {"type": "FeatureCollection", "features": []}


@app.get("/opportunities")
def opportunities():
    """Ranked cross-utility coordination opportunities.

    PostGIS path when a database is configured; otherwise the file-based
    deterministic engine. Returns [] when no approved pair qualifies.
    """
    if db.database_url():
        with db.connect() as conn:
            db.ingest_csv(conn)              # proposed rows only
            return db.find_opportunities(conn)
    return find_opportunities_file(_load_file_projects())
