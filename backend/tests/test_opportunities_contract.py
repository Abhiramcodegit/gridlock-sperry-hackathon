"""Contract tests for GET /opportunities (P2 Revision 2.2, docs/specs/EDGE_CASES.md).

Covers the fixture-backed acceptance checks that live at the contract/API layer:
expected pair set, exclusions, shared-endpoint reference case (§3.4), tier
boundaries and labels, ranking/tiebreak, date-gap semantics, the three 503
reasons, 400 invalid_project_id, project_id filtering, and meta fields.

The golden pair set is used as a regression oracle only; the contract runs on
data/official/projects_official.json.
"""
import copy
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from gridlock import contract
from gridlock.api import app

ROOT = pathlib.Path(__file__).resolve().parents[2]
OFFICIAL = ROOT / "data" / "official" / "projects_official.json"

EXPECTED_IDS = {
    "DESC_1__GPC_1", "DESC_2__GPC_1", "DESC_3__GPC_2",
    "DESC_3__GPC_3", "DESC_5__GPC_2", "DESC_5__GPC_3",
}
EXCLUDED = {"DESC_4", "GPC_4", "GPC_5"}

client = TestClient(app)


@pytest.fixture(scope="module")
def projects():
    return json.loads(OFFICIAL.read_text())


@pytest.fixture(scope="module")
def payload(projects):
    return contract.build_opportunities(projects)


# --- fixture-backed contract behavior ---------------------------------------

def test_pair_universe_meta(payload):
    assert payload["meta"]["pair_count"] == 25
    assert payload["meta"]["opportunity_count"] == 6
    assert payload["meta"]["endpoint_only_count"] == 4
    assert payload["meta"]["gate_km"] == 40.0
    assert payload["meta"]["result_source"] == "official_reference"


def test_expected_pair_set(payload):
    got = {o["opportunity_id"] for o in payload["data"]}
    assert got == EXPECTED_IDS


def test_excluded_projects_absent(payload):
    for o in payload["data"]:
        assert o["desc_project_id"] not in EXCLUDED
        assert o["gpc_project_id"] not in EXCLUDED


def test_opportunity_id_format_and_no_self_pairs(payload):
    for o in payload["data"]:
        assert o["opportunity_id"] == f"{o['desc_project_id']}__{o['gpc_project_id']}"
        assert o["desc_project_id"] != o["gpc_project_id"]


def test_ranks_are_1_based_and_dense(payload):
    ranks = [o["rank"] for o in payload["data"]]
    assert ranks == list(range(1, len(ranks) + 1))


def test_ranking_order_distance_then_gap_then_id(payload):
    keys = [
        (o["closest_distance_km"],
         float("inf") if o["date_gap_days"] is None else o["date_gap_days"],
         o["opportunity_id"])
        for o in payload["data"]
    ]
    assert keys == sorted(keys)


def test_all_under_strict_gate(payload):
    for o in payload["data"]:
        assert o["closest_distance_km"] < 40.0


def test_required_fields_present(payload):
    required = {
        "opportunity_id", "rank", "desc_project_id", "gpc_project_id",
        "closest_distance_km", "closest_distance_mi",
        "center_distance_km", "center_distance_mi",
        "coordination_tier", "coordination_tier_label", "tier_confidence",
        "date_gap_days", "date_gap_days_signed", "distance_basis",
        "pair_geometry_confidence", "is_endpoint_only_estimate",
        "shared_endpoint_detected", "shared_endpoint_name",
        "closest_point_desc", "closest_point_gpc", "closest_connector",
        "data_warnings", "result_source",
    }
    for o in payload["data"]:
        assert required <= set(o.keys())
        assert "_full_km" not in o  # internal key must be stripped


def test_shared_endpoint_reference_case_desc2_gpc1(payload):
    o = next(o for o in payload["data"] if o["opportunity_id"] == "DESC_2__GPC_1")
    assert o["closest_distance_km"] <= 0.001
    assert o["coordination_tier"] == "touching_crossing"
    assert o["coordination_tier_label"] == "Shared endpoint facility"
    assert o["shared_endpoint_detected"] is True
    assert o["shared_endpoint_name"] == "Thurmond Sub / THURMOND DAM #5"
    assert o["tier_confidence"] == "reduced"
    assert o["distance_basis"] == "point_to_segment"
    assert o["pair_geometry_confidence"] == "mixed"
    assert o["is_endpoint_only_estimate"] is True
    assert o["date_gap_days"] == 3074


def test_endpoint_only_sides_are_reduced(payload):
    for o in payload["data"]:
        if o["pair_geometry_confidence"] == "mixed" or o["pair_geometry_confidence"] == "both_endpoint_only":
            assert o["tier_confidence"] == "reduced"
            assert o["is_endpoint_only_estimate"] is True


def test_signed_gap_direction(payload):
    # DESC_2 (2024-12-31) vs GPC_1 (2033-06-01): GPC later -> positive signed
    o = next(o for o in payload["data"] if o["opportunity_id"] == "DESC_2__GPC_1")
    assert o["date_gap_days_signed"] == 3074
    assert o["date_gap_days"] == 3074


def test_center_distance_reported_but_not_gate(payload):
    # center distance may exceed closest distance; it must never gate.
    for o in payload["data"]:
        assert o["center_distance_km"] is None or o["center_distance_km"] >= o["closest_distance_km"] - 1e-9


# --- tier boundary logic (unit level) ---------------------------------------

@pytest.mark.parametrize("km,expected", [
    (0.0, "touching_crossing"),
    (0.001, "touching_crossing"),
    (0.0011, "under_1_6_km"),
    (1.5999, "under_1_6_km"),
    (1.6, "under_8_km"),      # boundary -> next-larger tier
    (7.9999, "under_8_km"),
    (8.0, "under_40_km"),     # boundary -> next-larger tier
    (39.999, "under_40_km"),
])
def test_tier_boundaries(km, expected):
    tier, _ = contract._tier_for(km, shared_endpoint=False, touching=False)
    assert tier == expected


def test_decimal_round_half_up():
    # 0.0005 -> 0.001 (half up), not banker's rounding
    assert contract._round(0.0005, 3) == 0.001
    assert contract._round(2.9925, 3) == 2.993


# --- error conditions --------------------------------------------------------

def test_503_dataset_count_mismatch(projects):
    short = projects[:9]
    with pytest.raises(contract.ContractError) as ei:
        contract.build_opportunities(short)
    assert ei.value.status == 503
    assert ei.value.details["reason"] == "dataset_project_count_mismatch"
    assert ei.value.details["expected"] == 10
    assert ei.value.details["found"] == 9


def test_503_duplicate_id_is_count_mismatch(projects):
    dup = copy.deepcopy(projects)
    dup[1] = copy.deepcopy(dup[0])  # duplicate DESC_1, drop a distinct id
    with pytest.raises(contract.ContractError) as ei:
        contract.build_opportunities(dup)
    assert ei.value.details["reason"] == "dataset_project_count_mismatch"


def test_503_unparseable_date(projects):
    bad = copy.deepcopy(projects)
    for p in bad:
        if p["id"] == "GPC_2":
            p["in_service_date"] = "2027-6-1"  # not zero-padded -> unparseable
    with pytest.raises(contract.ContractError) as ei:
        contract.build_opportunities(bad)
    assert ei.value.status == 503
    assert ei.value.details["reason"] == "unparseable_in_service_date"
    assert ei.value.details["project_id"] == "GPC_2"
    assert ei.value.details["value"] == "2027-6-1"


def test_503_no_known_endpoint(projects):
    bad = copy.deepcopy(projects)
    for p in bad:
        if p["id"] == "DESC_4":
            p["endpoint_a_coords"] = None
            p["endpoint_b_coords"] = None
    with pytest.raises(contract.ContractError) as ei:
        contract.build_opportunities(bad)
    assert ei.value.status == 503
    assert ei.value.details["reason"] == "no_known_endpoint"
    assert ei.value.details["project_id"] == "DESC_4"


def test_400_invalid_project_id():
    with pytest.raises(contract.ContractError) as ei:
        contract.validate_project_id("desc_1")  # wrong case
    assert ei.value.status == 400
    assert ei.value.details["reason"] == "invalid_project_id"


def test_null_date_gap(projects):
    bad = copy.deepcopy(projects)
    for p in bad:
        if p["id"] == "GPC_1":
            p["in_service_date"] = None
    payload = contract.build_opportunities(bad)
    for o in payload["data"]:
        if o["gpc_project_id"] == "GPC_1":
            assert o["date_gap_days"] is None
            assert o["date_gap_days_signed"] is None
    # pair still qualifies on distance
    assert "DESC_2__GPC_1" in {o["opportunity_id"] for o in payload["data"]}


# --- HTTP layer --------------------------------------------------------------

def test_http_opportunities_ok():
    r = client.get("/opportunities")
    assert r.status_code == 200
    body = r.json()
    assert {o["opportunity_id"] for o in body["data"]} == EXPECTED_IDS
    assert body["meta"]["opportunity_count"] == 6


def test_http_filter_by_project_keeps_rank():
    full = client.get("/opportunities").json()
    r = client.get("/opportunities", params={"project_id": "DESC_3"})
    assert r.status_code == 200
    sub = r.json()
    ids = {o["opportunity_id"] for o in sub["data"]}
    assert ids == {"DESC_3__GPC_2", "DESC_3__GPC_3"}
    # ranks preserved from the full ranking
    full_ranks = {o["opportunity_id"]: o["rank"] for o in full["data"]}
    for o in sub["data"]:
        assert o["rank"] == full_ranks[o["opportunity_id"]]
    assert sub["meta"]["filtered_project_id"] == "DESC_3"


def test_http_filter_zero_project_returns_empty():
    r = client.get("/opportunities", params={"project_id": "GPC_5"})
    assert r.status_code == 200
    assert r.json()["data"] == []


def test_http_invalid_project_id_400():
    r = client.get("/opportunities", params={"project_id": "desc_1"})
    assert r.status_code == 400
    assert r.json()["error"]["details"]["reason"] == "invalid_project_id"


# --- 40 km gate boundary at the contract layer (strict; 40.0 km EXCLUDED) ---
from pyproj import Geod as _Geod

_GEOD = _Geod(ellps="WGS84")


def _mk_project(pid, lon, lat):
    """Minimal endpoint_only project at a single known point (synthetic)."""
    return {
        "id": pid,
        "utility": "DESC" if pid.startswith("DESC_") else "GPC",
        "project_name": f"synthetic {pid}",
        "endpoint_a_name": "A", "endpoint_a_coords": [lon, lat],
        "endpoint_b_name": None, "endpoint_b_coords": None,
        "center_geometry": [lon, lat],
        "in_service_date": "2027-06-01",
        "geometry_confidence": "endpoint_only",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def _pair_at_geodesic_m(meters):
    """Return (desc, gpc) endpoint_only projects exactly `meters` apart (WGS84)."""
    lon0, lat0 = -81.0, 32.5
    lon1, lat1, _ = _GEOD.fwd(lon0, lat0, 90.0, meters)  # due east
    return _mk_project("DESC_9", lon0, lat0), _mk_project("GPC_9", lon1, lat1)


class _VD:
    """Stand-in ValidatedDataset for _evaluate_pair unit tests."""
    def __init__(self, ids):
        self.parsed_dates = {i: __import__("datetime").date(2027, 6, 1) for i in ids}


def test_contract_gate_comparator_is_strict_at_40km():
    # The gate is `closest_km_full < GATE_KM` (contract.py). Prove exactly
    # 40.0 km is EXCLUDED and any value below is INCLUDED, independent of
    # geodesic round-trip precision.
    assert contract.GATE_KM == 40.0
    assert not (40.0 < contract.GATE_KM)          # exactly 40.0 -> excluded
    assert (39.999999 < contract.GATE_KM)         # just under -> included


def test_contract_gate_includes_just_under_40000_m():
    # A synthetic pair ~39.6 km apart qualifies with tier under_40_km.
    d, g = _pair_at_geodesic_m(39600.0)
    row = contract._evaluate_pair(d, g, _VD([d["id"], g["id"]]))
    assert row is not None
    assert row["closest_distance_km"] < 40.0
    assert row["coordination_tier"] == "under_40_km"


def test_contract_gate_excludes_over_40km_pair():
    # A synthetic pair ~40.5 km apart is excluded (None).
    d, g = _pair_at_geodesic_m(40500.0)
    row = contract._evaluate_pair(d, g, _VD([d["id"], g["id"]]))
    assert row is None


def test_contract_rounding_km_3dp_half_up():
    # 39.9995 km rounds half-up to 40.000 for display, but the gate uses the
    # full-precision value (< 40.0) so the pair still qualifies (E13).
    assert contract._round(39.9995, 3) == 40.0
    assert contract._round(2.9925, 3) == 2.993       # half-up, not banker's
    assert contract._round(0.0005, 3) == 0.001


def test_contract_latlon_rounding_6dp():
    assert contract._round(-81.12345649, 6) == -81.123456
    assert contract._round(32.50000050, 6) == 32.500001  # half-up
