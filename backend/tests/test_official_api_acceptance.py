"""Official API acceptance suite (SCAFFOLD).

Bindings: Rev 2.2 as confirmed by Agent 2B via P1, plus Revision 2.2.1
rulings relayed by P1. Every unconfirmed name is marked TODO(Rev2.2.1) and
must be locked to P2's Revision 2.2.1 SHA before this suite is trusted.
Gate semantics are marked TODO(GATE-SEMANTICS) pending Agent 1.

Structure:
- /opportunities is the APPROVED-ONLY surface. [] is the CORRECT answer
  (no geometry is human-approved; ENGINE_PHASE3 documents a positive
  control). It is ASSERTED, never skipped once the app is reachable.
- The six reference pairs live on /reference/opportunities (G-1 ruling):
  bare JSON array, section 5.3 item schema, optional ?project_id.
- Integration switch: set GRIDLOCK_API_INTEGRATED=1 once Agent 5 declares
  the API integrated. Then an app-import failure or a missing route is a
  FAIL, not a skip, so a broken import can never report green.
- The GA/SC bounding box is a NON-BLOCKING diagnostic (warns, never fails).
"""
import json
import math
import os
import warnings
from pathlib import Path

import pytest

INTEGRATED = os.environ.get("GRIDLOCK_API_INTEGRATED") == "1"

# --- Rev 2.2 confirmed (Agent 2B via P1) ---------------------------------
PAIR_DESC = "desc_project_id"
PAIR_GPC = "gpc_project_id"
KM = "closest_distance_km"
MI = "closest_distance_mi"

# --- Revision 2.2.1 rulings (G-1, via P1) ----------------------------------
REFERENCE_PAIRS_ROUTE = "/reference/opportunities"
REFERENCE_ENVELOPE = None  # bare JSON array (G-1)
PROJECT_ID_QUERY = "project_id"  # optional filter (G-1)

# --- Unconfirmed: must be locked to Revision 2.2.1 -------------------------
PROJECT_ID_KEY = None  # TODO(Rev2.2.1): project-ID key in /projects items
PROJECTS_ENVELOPE = None  # TODO(Rev2.2.1): None = bare JSON array; else wrapper key
GEOMETRY_KEY = None  # TODO(Rev2.2.1): geometry key on /projects items
APP_IMPORT = "gridlock.api:app"  # TODO(Rev2.2.1): confirm ASGI app path (unverified)
FILTER_MATCHES_EITHER_SIDE = True  # TODO(Rev2.2.1): confirm ?project_id matches either side

# --- Gate: do NOT lock until Agent 1 answers -------------------------------
RAW_METERS_KEY = None  # TODO(GATE-SEMANTICS): raw unrounded meters field, if exposed
GATE_INCLUSIVE = None  # TODO(GATE-SEMANTICS): True if comparator is <= (ST_DWithin), False if <
KM_ROUNDING_DECIMALS = None  # TODO(GATE-SEMANTICS): rounding precision of closest_distance_km

KM_PER_MI = 1.609344
GATE_M = 40000.0
ROUND_TOL = 0.0015
GOLDEN = Path(__file__).parent / "golden" / "opportunities_pairs.json"

BLOCKED_PROJECTS = "BLOCKED: /projects ID key / envelope unconfirmed (TODO Rev2.2.1)"
BLOCKED_GATE = "BLOCKED: gate comparator / raw meters unconfirmed (TODO GATE-SEMANTICS)"


def _blocked(msg):
    if INTEGRATED:
        pytest.fail(msg)
    pytest.skip(msg)


def _client():
    base = os.environ.get("GRIDLOCK_API_URL")
    if base:
        import requests

        class Live:
            def get(self, path, params=None):
                return requests.get(base.rstrip("/") + path, params=params, timeout=10)

        return Live()
    try:
        import importlib

        from fastapi.testclient import TestClient

        mod_name, attr = APP_IMPORT.split(":")
        app = getattr(importlib.import_module(mod_name), attr)
    except Exception as exc:
        _blocked(f"No GRIDLOCK_API_URL and app import {APP_IMPORT} failed: {exc!r}")
    return TestClient(app)


@pytest.fixture(scope="module")
def api():
    return _client()


def _unwrap(body, envelope):
    items = body if envelope is None else body[envelope]
    assert isinstance(items, list), "expected a JSON array of items"
    return items


# --- 1. Approved-only surface: [] is correct -------------------------------

def test_opportunities_approved_only_is_empty(api):
    r = api.get("/opportunities")
    assert r.status_code == 200
    assert r.json() == []


# --- 2. Projects ------------------------------------------------------------

@pytest.fixture(scope="module")
def projects(api):
    if PROJECT_ID_KEY is None:
        pytest.skip(BLOCKED_PROJECTS)
    r = api.get("/projects")
    assert r.status_code == 200, f"/projects -> {r.status_code}"
    return _unwrap(r.json(), PROJECTS_ENVELOPE)


def test_projects_exactly_ten_unique(projects):
    ids = [p[PROJECT_ID_KEY] for p in projects]
    assert len(ids) == 10
    assert len(set(ids)) == 10, "duplicate project IDs"


# --- 3. Reference pairs: /reference/opportunities ---------------------------

def _get_reference(api, params=None):
    r = api.get(REFERENCE_PAIRS_ROUTE, params=params)
    if r.status_code == 404:
        _blocked(f"BLOCKED: {REFERENCE_PAIRS_ROUTE} returned 404 (route not live yet)")
    assert r.status_code == 200, f"{REFERENCE_PAIRS_ROUTE} -> {r.status_code}"
    return _unwrap(r.json(), REFERENCE_ENVELOPE)


@pytest.fixture(scope="module")
def reference_pairs(api):
    return _get_reference(api)


@pytest.fixture(scope="module")
def golden():
    return json.loads(GOLDEN.read_text())


def _pair(o):
    a, b = o[PAIR_DESC], o[PAIR_GPC]
    assert a != b, f"self-pair {a}"
    return frozenset((a, b))


def test_reference_exactly_six(reference_pairs):
    assert len(reference_pairs) == 6


def test_reference_pairs_unique_regardless_of_order(reference_pairs):
    pairs = [_pair(o) for o in reference_pairs]
    assert len(set(pairs)) == len(pairs), "duplicate pair (A,B)/(B,A)"


def test_reference_pairs_match_golden(reference_pairs, golden):
    got = {_pair(o) for o in reference_pairs}
    want = {frozenset(p) for p in golden["pairs_unordered"]}
    assert got == want, f"missing={want - got} unexpected={got - want}"


def test_reference_km_mi_consistent(reference_pairs):
    for o in reference_pairs:
        km, mi = o[KM], o[MI]
        assert math.isfinite(km) and math.isfinite(mi)
        assert abs(mi - km / KM_PER_MI) <= ROUND_TOL, f"{_pair(o)}: {km} km vs {mi} mi"


def test_reference_distance_inside_gate(reference_pairs):
    """TODO(GATE-SEMANTICS): never infer strictness from rounded closest_distance_km."""
    if RAW_METERS_KEY is None or GATE_INCLUSIVE is None:
        pytest.skip(BLOCKED_GATE)
    for o in reference_pairs:
        m = o[RAW_METERS_KEY]
        assert math.isfinite(m) and m >= 0.0, f"{_pair(o)}: bad raw meters {m}"
        ok = m <= GATE_M if GATE_INCLUSIVE else m < GATE_M
        assert ok, f"{_pair(o)}: {m} m outside gate ({'<=' if GATE_INCLUSIVE else '<'} {GATE_M})"


def test_reference_project_id_filter(api, reference_pairs):
    target = reference_pairs[0][PAIR_DESC]
    subset = _get_reference(api, params={PROJECT_ID_QUERY: target})
    assert subset, f"?{PROJECT_ID_QUERY}={target} returned no items"
    full = {_pair(o) for o in reference_pairs}
    for o in subset:
        assert _pair(o) in full, f"filtered item {_pair(o)} not in unfiltered set"
        if FILTER_MATCHES_EITHER_SIDE:
            assert target in _pair(o), f"{_pair(o)} does not involve {target}"


def test_reference_ids_exist_in_projects(reference_pairs, projects):
    ids = {p[PROJECT_ID_KEY] for p in projects}
    for o in reference_pairs:
        assert _pair(o) <= ids, f"{_pair(o)} references unknown project"


# --- 4. Coordinates -----------------------------------------------------------

def _coords(geom):
    c = geom["coordinates"]
    return [c] if geom["type"] == "Point" else c


def _project_geoms(projects):
    if GEOMETRY_KEY is None:
        pytest.skip("BLOCKED: geometry key unconfirmed (TODO Rev2.2.1)")
    for p in projects:
        geom = p.get(GEOMETRY_KEY)
        assert geom and geom.get("type") in {"Point", "LineString"}, f"{p.get(PROJECT_ID_KEY)}: bad geometry"
        yield p, geom


def test_coords_finite_and_valid(projects):
    for p, geom in _project_geoms(projects):
        for lon, lat, *_ in _coords(geom):
            assert math.isfinite(lon) and math.isfinite(lat)
            assert -180 <= lon <= 180 and -90 <= lat <= 90


def test_diagnostic_gasc_bbox_nonblocking(projects):
    """NON-BLOCKING diagnostic. Improvised GA/SC box; warns only, never fails."""
    for p, geom in _project_geoms(projects):
        for lon, lat, *_ in _coords(geom):
            if not (-86.0 <= lon <= -78.0 and 30.0 <= lat <= 36.0):
                warnings.warn(f"DIAGNOSTIC: {p.get(PROJECT_ID_KEY)} outside improvised GA/SC box ({lon}, {lat})")
