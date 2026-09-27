"""GridLock FastAPI app.

`GET /opportunities` serves the P2 Revision 2.2 coordination contract
(docs/specs/EDGE_CASES.md) computed by gridlock.contract over the official
challenge dataset (data/official/projects_official.json). The engine runs
offline and deterministically: no runtime network calls, no invented
coordinates, no tuning.

Distance model: closest points are found in EPSG:32617 (UTM 17N) via shapely,
and the reported distance is the WGS 84 geodesic distance (pyproj.Geod) between
those closest points. See gridlock.contract.

An empty `data: []` array with HTTP 200 is the correct answer when no pair
qualifies. The three documented 503 reasons and the 400 invalid_project_id case
are returned as structured error bodies.
"""
import json
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from . import contract, db, migrate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load proposed rows into PostGIS once at boot. No-op in file-only mode.
    migrate.run()
    yield


app = FastAPI(title="GridLock", lifespan=lifespan)

ROOT = pathlib.Path(__file__).resolve().parents[2]
APPROVED = ROOT / "data" / "approved" / "projects_approved.geojson"
OFFICIAL_JSON = ROOT / "data" / "official" / "projects_official.json"


def _load_official_projects() -> list[dict]:
    """Load the official challenge dataset (the contract's approved dataset)."""
    if not OFFICIAL_JSON.exists():
        # Missing dataset is treated as a count mismatch (found 0), which maps
        # to the documented 503 rather than a crash.
        return []
    return json.loads(OFFICIAL_JSON.read_text())


@app.get("/health")
def health():
    return {"ok": True, "backend": "postgis" if db.database_url() else "file"}


@app.get("/projects")
def projects():
    if APPROVED.exists():
        return json.loads(APPROVED.read_text())
    return {"type": "FeatureCollection", "features": []}


@app.get("/opportunities")
def opportunities(project_id: str | None = Query(default=None)):
    """Ranked cross-utility coordination opportunities (Revision 2.2 contract).

    Optional `project_id` filters to opportunities touching that project,
    preserving each opportunity's original rank. IDs are case-sensitive; an
    unknown or wrong-case id returns 400 invalid_project_id.
    """
    try:
        if project_id is not None:
            contract.validate_project_id(project_id)

        payload = contract.build_opportunities(
            _load_official_projects(), result_source="official_reference"
        )

        if project_id is not None:
            payload = contract.filter_by_project(payload, project_id)
        return payload
    except contract.ContractError as exc:
        return JSONResponse(status_code=exc.status, content=exc.body())
