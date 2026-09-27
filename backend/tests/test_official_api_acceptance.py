"""Official API acceptance suite (SCAFFOLD).

Bindings: Rev 2.2 as confirmed by Agent 2B via P1. Every unconfirmed name is
marked TODO(Rev2.3) and must be locked to P2's Rev 2.3 SHA before this suite
is trusted.

Structure:
- /opportunities is the APPROVED-ONLY surface. [] is the CORRECT answer
  (no geometry is human-approved; ENGINE_PHASE3 documents a positive
  control). It is ASSERTED, never skipped.
- The six reference pairs live on a SEPARATE route. Until Rev 2.3 defines
  that route, those tests report BLOCKED (skip). No route is invented and
  /opportunities is never repurposed.
- The GA/SC bounding box is a NON-BLOCKING diagnostic (warns, never fails).
"""
import json
import math
import os
import warnings
from pathlib import Path

import pytest

# --- Rev 2.2 confirmed (Agent 2B via P1) ---------------------------------
PAIR_DESC = "desc_project_id"
PAIR_GPC = "gpc_project_id"
KM = "closest_distance_km"
MI = "closest_distance_mi"

# --- Unconfirmed: must be locked to Rev 2.3 --------------------------------
PROJECT_ID_KEY = None  # TODO(Rev2.3): project-ID key in /projects items
PROJECTS_ENVELOPE = None  # TODO(Rev2.3): None = bare JSON array; else wrapper key
REFERENCE_ENVELOPE = None  # TODO(Rev2.3): None = bare JSON array; else wrapper key
REFERENCE_PAIRS_ROUTE = None  # TODO(Rev2.3): separate reference-pairs route; do NOT invent
GEOMETRY_KEY = None  # TODO(Rev2.3): geometry key on /projects items
APP_IMPORT = "gridlock.api:app"  # TODO(Rev2.3): confirm ASGI app path (unverified)

KM_PER_MI = 1.609344
GATE_M = 40000.0
ROUND_TOL = 0.0015
GOLDEN = Path(__file__).parent / "golden" / "opportunities_pairs.json"

BLOCKED_ROUTE = "BLOCKED: reference-pairs route not defined (TODO Rev2.3)"
BLOCKED_PROJECTS = "BLOCKED: /projects ID key / envelope unconfirmed (TODO Rev2.3)"


def _client():
    base = os.environ.get("GRIDLOCK_API_URL")
    if base:
        import requests

        class Live:
            def get(self, path):
                return requests.get(base.rstrip("/") + path, timeout=10)

        return Live()
    try:
        import importlib

        from fastapi.testclient import TestClient

        mod_name, attr = APP_IMPORT.split(":")
        app = getattr(importlib.import_module(mod_name), attr)
    except Exception as exc:
        pytest.skip(f"No GRIDLOCK_API_URL and app import {APP_IMPORT} failed: {exc}")
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
    assert r.json() == []  # TODO(Rev2.3): if Rev 2.3 adds an envelope, update this literal


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


# --- 3. Reference pairs (separate route) ------------------------------------

@pytest.fixture(scope="module")
def reference_pairs(api):
    if REFERENCE_PAIRS_ROUTE is None:
        pytest.skip(BLOCKED_ROUTE)
    r = api.get(REFERENCE_PAIRS_ROUTE)
    assert r.status_code == 200, f"{REFERENCE_PAIRS_ROUTE} -> {r.status_code}"
    return _unwrap(r.json(), REFERENCE_ENVELOPE)


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


def test_reference_distance_inside_exclusive_gate(reference_pairs):
    for o in reference_pairs:
        m = o[KM] * 1000.0
        assert 0.0 <= m < GATE_M, f"{_pair(o)}: {m} m not in [0, {GATE_M})"


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
        pytest.skip("BLOCKED: geometry key unconfirmed (TODO Rev2.3)")
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
