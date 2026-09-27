"""GridLock FastAPI app (P2 Revision 2.2.1).

Two opportunity surfaces, kept strictly separate (API_CONTRACT §5, §5.7):

- `GET /opportunities` is APPROVED-ONLY. While no geometry is human-approved it
  returns `200` with the §5.2 envelope and `data: []`. It never serves the
  coordinate-derived reference pairs.
- `GET /reference/opportunities` serves the proximity-screened REFERENCE
  CANDIDATES computed by gridlock.contract over the official dataset
  (data/official/projects_official.json), in the same §5.2 envelope. These are
  candidates for the utilities to confirm, never approved results.

Distance model: closest points are found in EPSG:32617 (UTM 17N) via shapely,
and the reported distance is the WGS 84 geodesic distance between them
(GEOMETRY_MATH 2.2.1 Blocker 3 option (a)). See gridlock.contract.

Errors use the §6.1 envelope {"error": {code, message, http_status, details}}.
"""
import json
import pathlib
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
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


def _err(status: int, code: str, message: str, **details) -> JSONResponse:
    """§6.1 error envelope response."""
    body = {"error": {"code": code, "message": message,
                      "http_status": status, "details": details or {}}}
    headers = {"Allow": "GET"} if status == 405 else None
    return JSONResponse(status_code=status, content=body, headers=headers)


def _load_official_projects() -> list[dict]:
    """Load the official challenge dataset (the reference dataset)."""
    if not OFFICIAL_JSON.exists():
        # Missing dataset -> count mismatch (found 0) -> documented 503.
        return []
    return json.loads(OFFICIAL_JSON.read_text())


def _dataset_version() -> str:
    """`projects_official.json@<40-char git blob SHA>` of the served file."""
    try:
        sha = subprocess.check_output(
            ["git", "hash-object", str(OFFICIAL_JSON)],
            cwd=str(ROOT), stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        sha = "0" * 40
    return f"projects_official.json@{sha}"


def _reject_unknown_query(request: Request, allowed: set[str]) -> JSONResponse | None:
    """400 invalid_query_parameter for any query param not in `allowed`."""
    for key in request.query_params.keys():
        if key not in allowed:
            return _err(400, "invalid_query_parameter",
                       f"Unknown query parameter: {key}", parameter=key)
    return None


@app.get("/health")
def health():
    return {"ok": True, "backend": "postgis" if db.database_url() else "file"}


@app.get("/projects")
def projects(request: Request):
    # §6.2: any query parameter on /projects is invalid.
    bad = _reject_unknown_query(request, allowed=set())
    if bad is not None:
        return bad
    import datetime
    rows = _load_official_projects()
    if len(rows) == 0 and not OFFICIAL_JSON.exists():
        return _err(503, "data_unavailable", "Official dataset not found.")
    # endpoint_only count: rows where geometry_confidence != "two_endpoints"
    ep_only = sum(1 for p in rows if p.get("geometry_confidence") != "two_endpoints")
    return {
        "data": rows,
        "meta": {
            "count": len(rows),
            "endpoint_only_count": ep_only,
            "dataset_version": _dataset_version(),
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        },
    }


@app.get("/opportunities")
def opportunities(request: Request):
    """APPROVED-ONLY coordination opportunities (Revision 2.2.1).

    Returns the §5.2 envelope. While no geometry is human-approved, `data` is
    empty. Reference candidates are served only by /reference/opportunities.
    `project_id` is accepted and validated for contract parity, but the
    approved set is empty so the filtered result is also empty.
    """
    bad = _reject_unknown_query(request, allowed={"project_id"})
    if bad is not None:
        return bad
    project_id = request.query_params.get("project_id")
    try:
        if project_id is not None:
            contract.validate_project_id(project_id)
    except contract.ContractError as exc:
        return JSONResponse(status_code=exc.status, content=exc.body())
    # Approved-only: no human-approved geometry exists, so data is empty.
    meta = contract._build_meta(
        0, 0,
        filter_project_id=project_id,
        dataset_version=_dataset_version(),
    )
    return {"data": [], "meta": meta}


@app.get("/reference/opportunities")
def reference_opportunities(request: Request):
    """Reference candidates (§5.7): the six proximity-screened cross-utility
    pairs from the official dataset, in the §5.2 envelope. Optional `project_id`
    filters to either pair member, preserving unfiltered ranks."""
    bad = _reject_unknown_query(request, allowed={"project_id"})
    if bad is not None:
        return bad
    project_id = request.query_params.get("project_id")
    try:
        if project_id is not None:
            contract.validate_project_id(project_id)
        payload = contract.build_opportunities(
            _load_official_projects(), dataset_version=_dataset_version(),
        )
        if project_id is not None:
            payload = contract.filter_by_project(payload, project_id)
        return payload
    except contract.ContractError as exc:
        return JSONResponse(status_code=exc.status, content=exc.body())


# --- §6 error envelope for framework-generated 404 / 405 ---------------------

@app.exception_handler(404)
async def _not_found(request: Request, exc):
    return _err(404, "not_found", "Unknown route.")


@app.exception_handler(405)
async def _method_not_allowed(request: Request, exc):
    return _err(405, "method_not_allowed",
               "Only GET is allowed on this route.")
