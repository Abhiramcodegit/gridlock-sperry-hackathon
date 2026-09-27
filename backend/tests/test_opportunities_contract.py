"""Contract tests for the P2 Revision 2.2.1 opportunity surfaces.

Two surfaces (API_CONTRACT §5, §5.7):
- GET /opportunities is APPROVED-ONLY -> 200 {"data": [], "meta": {...}}.
- GET /reference/opportunities serves the six proximity-screened reference
  candidates in the same §5.2 envelope.

Covers: expected pair set, exclusions, shared-endpoint reference case (§7),
tier boundaries and labels, ranking/tiebreak, date-gap semantics, the three
503 reasons, 400 invalid_project_id / invalid_query_parameter, 405 + Allow: GET,
project_id filtering with preserved ranks, and the §5.4 nine-field meta.

The golden pair set is a regression oracle only; the contract runs on
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
DATASET_VERSION = "projects_official.json@" + "0" * 40  # test stub

EXPECTED_IDS = {
    "DESC_1__GPC_1", "DESC_2__GPC_1", "DESC_3__GPC_2",
    "DESC_3__GPC_3", "DESC_5__GPC_2", "DESC_5__GPC_3",
}
EXCLUDED = {"DESC_4", "GPC_4", "GPC_5"}

META_FIELDS = {
    "count", "total_count", "inclusion_threshold_km",
    "inclusion_threshold_mi_display", "inclusion_rule", "ranking_rule",
    "filter_project_id", "dataset_version", "generated_at",
}

client = TestClient(app)


@pytest.fixture(scope="module")
def projects():
    return json.loads(OFFICIAL.read_text())


@pytest.fixture(scope="module")
def payload(projects):
    return contract.build_opportunities(projects, dataset_version=DATASET_VERSION)


# --- fixture-backed contract behavior ---------------------------------------

def test_meta_is_exactly_the_nine_fields(payload):
    assert set(payload["meta"].keys()) == META_FIELDS
    m = payload["meta"]
    assert m["count"] == 6
    assert m["total_count"] == 6
    assert m["inclusion_threshold_km"] == 40.0
    assert m["inclusion_threshold_mi_display"] == 25
    assert m["inclusion_rule"] == "closest_distance_km < 40.0 and utilities differ"
    assert m["ranking_rule"] == "closest_distance_km asc, date_gap_days asc nulls last, opportunity_id asc"
    assert m["filter_project_id"] is None


def test_no_forbidden_meta_keys(payload):
    forbidden = {"result_source", "gate_km", "gate_m", "pair_count",
                 "opportunity_count", "endpoint_only_count", "filtered_project_id"}
    assert forbidden.isdisjoint(payload["meta"].keys())


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
        "shared_endpoint_detected", "shared_endpoint_name",
        "distance_basis", "pair_geometry_confidence",
        "desc_geometry_confidence", "gpc_geometry_confidence",
        "closest_point_desc", "closest_point_gpc", "closest_connector",
        "desc_in_service_date", "gpc_in_service_date",
        "date_gap_days", "date_gap_days_signed", "is_endpoint_only_estimate",
    }
    for o in payload["data"]:
        assert required <= set(o.keys())
        assert "_full_km" not in o          # internal key stripped
        assert "data_warnings" not in o     # §4.3 Project field, not item-level
        assert "result_source" not in o     # removed in 2.2.1


def test_closest_point_objects_are_lat_lon(payload):
    for o in payload["data"]:
        for key in ("closest_point_desc", "closest_point_gpc"):
            pt = o[key]
            assert set(pt.keys()) == {"lat", "lon"}
        # connector is [lon, lat] order, matching the point objects
        coords = o["closest_connector"]["coordinates"]
        assert coords[0] == [o["closest_point_desc"]["lon"], o["closest_point_desc"]["lat"]]
        assert coords[1] == [o["closest_point_gpc"]["lon"], o["closest_point_gpc"]["lat"]]


def test_shared_endpoint_reference_case_desc2_gpc1(payload):
    o = next(o for o in payload["data"] if o["opportunity_id"] == "DESC_2__GPC_1")
    assert o["closest_distance_km"] <= 0.001
    assert o["coordination_tier"] == "touching_crossing"
    assert o["coordination_tier_label"] == "Endpoints published at the same coordinates"
    assert o["shared_endpoint_detected"] is True
    assert o["shared_endpoint_name"] == "Thurmond Sub / THURMOND DAM #5"
    assert o["tier_confidence"] == "reduced"
    assert o["distance_basis"] == "point_to_segment"
    assert o["pair_geometry_confidence"] == "mixed"
    assert o["is_endpoint_only_estimate"] is True
    assert o["date_gap_days"] == 3074


def test_endpoint_only_sides_are_reduced(payload):
    for o in payload["data"]:
        if o["pair_geometry_confidence"] in ("mixed", "both_endpoint_only"):
            assert o["tier_confidence"] == "reduced"
            assert o["is_endpoint_only_estimate"] is True


def test_signed_gap_direction(payload):
    # DESC_2 (2024-12-31) vs GPC_1 (2033-06-01): GPC later -> positive signed
    o = next(o for o in payload["data"] if o["opportunity_id"] == "DESC_2__GPC_1")
    assert o["date_gap_days_signed"] == 3074
    assert o["date_gap_days"] == 3074


def test_center_distance_reported_but_not_gate(payload):
    for o in payload["data"]:
        assert o["center_distance_km"] is None or o["center_distance_km"] >= o["closest_distance_km"] - 1e-9


# --- tier boundary logic (unit level) ---------------------------------------

@pytest.mark.parametrize("km,expected,label", [
    (0.0, "touching_crossing", "Touching / crossing"),
    (0.001, "touching_crossing", "Touching / crossing"),
    (0.0011, "under_1_6_km", "Under 1.6 km (1 mi)"),
    (1.5999, "under_1_6_km", "Under 1.6 km (1 mi)"),
    (1.6, "under_8_km", "Under 8 km (5 mi)"),      # boundary -> next-larger tier
    (7.9999, "under_8_km", "Under 8 km (5 mi)"),
    (8.0, "under_40_km", "Under 40 km (25 mi)"),   # boundary -> next-larger tier
    (39.999, "under_40_km", "Under 40 km (25 mi)"),
])
def test_tier_boundaries_and_labels(km, expected, label):
    tier, lbl = contract._tier_for(km, shared_endpoint=False, touching=False)
    assert tier == expected
    assert lbl == label


def test_shared_endpoint_label_string():
    tier, lbl = contract._tier_for(0.0, shared_endpoint=True, touching=True)
    assert tier == "touching_crossing"
    assert lbl == "Endpoints published at the same coordinates"


def test_decimal_round_half_up():
    assert contract._round(0.0005, 3) == 0.001
    assert contract._round(2.9925, 3) == 2.993


# --- shared-endpoint detection order + trim rules (§7) ----------------------

def test_shared_endpoint_equal_labels_emit_desc_alone():
    desc = {"endpoint_a_name": "  Alpha ", "endpoint_a_coords": [-81.0, 32.5],
            "endpoint_b_name": None, "endpoint_b_coords": None}
    gpc = {"endpoint_a_name": "alpha", "endpoint_a_coords": [-81.0, 32.5],
           "endpoint_b_name": None, "endpoint_b_coords": None}
    detected, name = contract._detect_shared_endpoint(desc, gpc)
    assert detected is True
    assert name == "Alpha"   # trimmed DESC label alone (equal after trim+casefold)


def test_shared_endpoint_differing_labels_concatenate_trimmed():
    desc = {"endpoint_a_name": "Thurmond Sub", "endpoint_a_coords": [-82.195931, 33.660127],
            "endpoint_b_name": None, "endpoint_b_coords": None}
    gpc = {"endpoint_a_name": "EVANS", "endpoint_a_coords": [-82.168648, 33.543994],
           "endpoint_b_name": "THURMOND DAM #5", "endpoint_b_coords": [-82.195931, 33.660127]}
    detected, name = contract._detect_shared_endpoint(desc, gpc)
    assert detected is True
    assert name == "Thurmond Sub / THURMOND DAM #5"


# --- error conditions --------------------------------------------------------

def test_503_dataset_count_mismatch(projects):
    short = projects[:9]
    with pytest.raises(contract.ContractError) as ei:
        contract.build_opportunities(short, dataset_version=DATASET_VERSION)
    assert ei.value.status == 503
    assert ei.value.code == "data_unavailable"
    assert ei.value.details["reason"] == "dataset_project_count_mismatch"
    assert ei.value.details["expected"] == 10
    assert ei.value.details["found"] == 9


def test_503_duplicate_id_is_count_mismatch(projects):
    dup = copy.deepcopy(projects)
    dup[1] = copy.deepcopy(dup[0])
    with pytest.raises(contract.ContractError) as ei:
        contract.build_opportunities(dup, dataset_version=DATASET_VERSION)
    assert ei.value.details["reason"] == "dataset_project_count_mismatch"


def test_503_unparseable_date(projects):
    bad = copy.deepcopy(projects)
    for p in bad:
        if p["id"] == "GPC_2":
            p["in_service_date"] = "2027-6-1"
    with pytest.raises(contract.ContractError) as ei:
        contract.build_opportunities(bad, dataset_version=DATASET_VERSION)
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
        contract.build_opportunities(bad, dataset_version=DATASET_VERSION)
    assert ei.value.status == 503
    assert ei.value.details["reason"] == "no_known_endpoint"
    assert ei.value.details["project_id"] == "DESC_4"


def test_400_invalid_project_id():
    with pytest.raises(contract.ContractError) as ei:
        contract.validate_project_id("desc_1")
    assert ei.value.status == 400
    assert ei.value.code == "invalid_project_id"


def test_error_body_shape():
    err = contract.ContractError(400, "invalid_project_id", "bad", project_id="x")
    body = err.body()
    assert set(body["error"].keys()) == {"code", "message", "http_status", "details"}
    assert body["error"]["code"] == "invalid_project_id"
    assert body["error"]["http_status"] == 400


def test_null_date_gap(projects):
    bad = copy.deepcopy(projects)
    for p in bad:
        if p["id"] == "GPC_1":
            p["in_service_date"] = None
    payload = contract.build_opportunities(bad, dataset_version=DATASET_VERSION)
    for o in payload["data"]:
        if o["gpc_project_id"] == "GPC_1":
            assert o["date_gap_days"] is None
            assert o["date_gap_days_signed"] is None
    assert "DESC_2__GPC_1" in {o["opportunity_id"] for o in payload["data"]}


# --- HTTP layer: /opportunities is APPROVED-ONLY ----------------------------

def test_http_opportunities_is_empty_envelope():
    r = client.get("/opportunities")
    assert r.status_code == 200
    body = r.json()
    assert body["data"] == []
    assert set(body["meta"].keys()) == META_FIELDS
    assert body["meta"]["count"] == 0
    assert body["meta"]["total_count"] == 0


def test_http_opportunities_never_serves_reference_pairs():
    body = client.get("/opportunities").json()
    assert body["data"] == []  # the six reference pairs must NOT appear here


# --- HTTP layer: /reference/opportunities -----------------------------------

def test_http_reference_unfiltered():
    r = client.get("/reference/opportunities")
    assert r.status_code == 200
    body = r.json()
    assert {o["opportunity_id"] for o in body["data"]} == EXPECTED_IDS
    assert body["meta"]["count"] == 6
    assert body["meta"]["total_count"] == 6
    assert body["meta"]["filter_project_id"] is None
    assert set(body["meta"].keys()) == META_FIELDS


def test_http_reference_filtered_preserves_rank():
    full = client.get("/reference/opportunities").json()
    r = client.get("/reference/opportunities", params={"project_id": "GPC_1"})
    assert r.status_code == 200
    sub = r.json()
    ids = {o["opportunity_id"] for o in sub["data"]}
    assert ids == {"DESC_1__GPC_1", "DESC_2__GPC_1"}   # matches either pair member
    full_ranks = {o["opportunity_id"]: o["rank"] for o in full["data"]}
    for o in sub["data"]:
        assert o["rank"] == full_ranks[o["opportunity_id"]]  # ranks NOT renumbered
    assert sub["meta"]["count"] == 2
    assert sub["meta"]["total_count"] == 6
    assert sub["meta"]["filter_project_id"] == "GPC_1"


def test_http_reference_no_match_is_empty():
    r = client.get("/reference/opportunities", params={"project_id": "DESC_4"})
    assert r.status_code == 200
    body = r.json()
    assert body["data"] == []
    assert body["meta"]["count"] == 0
    assert body["meta"]["total_count"] == 6


def test_http_reference_unknown_query_param_400():
    r = client.get("/reference/opportunities", params={"bogus": "1"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_query_parameter"


def test_http_reference_invalid_project_id_400():
    r = client.get("/reference/opportunities", params={"project_id": "desc_1"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_project_id"


def test_http_non_get_405_with_allow_header():
    r = client.post("/opportunities")
    assert r.status_code == 405
    assert r.headers.get("Allow") == "GET"
    assert r.json()["error"]["code"] == "method_not_allowed"


def test_http_reference_non_get_405():
    r = client.post("/reference/opportunities")
    assert r.status_code == 405
    assert r.headers.get("Allow") == "GET"


# --- 40 km gate boundary at the contract layer (strict; 40.0 km EXCLUDED) ---
from pyproj import Geod as _Geod

_GEOD = _Geod(ellps="WGS84")


def _mk_project(pid, lon, lat):
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
    lon0, lat0 = -81.0, 32.5
    lon1, lat1, _ = _GEOD.fwd(lon0, lat0, 90.0, meters)
    return _mk_project("DESC_9", lon0, lat0), _mk_project("GPC_9", lon1, lat1)


class _VD:
    def __init__(self, ids):
        self.parsed_dates = {i: __import__("datetime").date(2027, 6, 1) for i in ids}


def test_contract_gate_comparator_is_strict_at_40km():
    assert contract.GATE_KM == 40.0
    assert not (40.0 < contract.GATE_KM)
    assert (39.999999 < contract.GATE_KM)


def test_contract_gate_includes_just_under_40km():
    d, g = _pair_at_geodesic_m(39600.0)
    row = contract._evaluate_pair(d, g, _VD([d["id"], g["id"]]))
    assert row is not None
    assert row["closest_distance_km"] < 40.0
    assert row["coordination_tier"] == "under_40_km"


def test_contract_gate_excludes_over_40km_pair():
    d, g = _pair_at_geodesic_m(40500.0)
    row = contract._evaluate_pair(d, g, _VD([d["id"], g["id"]]))
    assert row is None


def test_contract_rounding_km_3dp_half_up():
    assert contract._round(39.9995, 3) == 40.0
    assert contract._round(2.9925, 3) == 2.993
    assert contract._round(0.0005, 3) == 0.001


def test_contract_latlon_rounding_6dp():
    assert contract._round(-81.12345649, 6) == -81.123456
    assert contract._round(32.50000050, 6) == 32.500001


# --- /projects official-dataset envelope (final integration) ----------------

def test_projects_returns_official_envelope():
    r = client.get("/projects")
    assert r.status_code == 200
    body = r.json()
    assert "data" in body and "meta" in body
    assert body["meta"]["count"] == 10
    assert len(body["data"]) == 10
    # The official dataset uses full utility names (see projects_official.json);
    # both utilities are represented.
    utils = {p["utility"] for p in body["data"]}
    assert utils == {"Dominion Energy South Carolina", "Georgia Power"}
    # endpoint_only_count = rows whose geometry_confidence != "two_endpoints".
    assert body["meta"]["endpoint_only_count"] == 4
