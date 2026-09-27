"""Regression tests for the official-challenge overlap engine.

The FIXTURE below is a regression oracle ONLY. It encodes the expected set of
qualifying (DESC, GPC) pairs taken from the challenge spreadsheet's `overlaps`
sheet. It is NEVER used as an input/data source for the engine: the engine runs
purely on data/official/projects_official.json, and these tests assert that its
output reproduces the fixture.
"""
import pathlib

import pytest

from gridlock.official_engine import (
    load_official_projects,
    find_opportunities,
)

# Regression oracle: expected qualifying pairs (order-independent).
FIXTURE = {
    "OVL_1": ("DESC_2", "GPC_1"),
    "OVL_2": ("DESC_3", "GPC_2"),
    "OVL_3": ("DESC_3", "GPC_3"),
    "OVL_4": ("DESC_1", "GPC_1"),
    "OVL_5": ("DESC_5", "GPC_2"),
    "OVL_6": ("DESC_5", "GPC_3"),
}
EXPECTED_PAIRS = set(FIXTURE.values())

# Projects that must never appear in any opportunity (overlap_count == 0).
EXCLUDED_IDS = {"DESC_4", "GPC_4", "GPC_5"}


@pytest.fixture(scope="module")
def projects():
    return load_official_projects()


@pytest.fixture(scope="module")
def opportunities(projects):
    return find_opportunities(projects)


def test_dataset_has_ten_official_projects(projects):
    ids = {p["id"] for p in projects}
    assert len(projects) == 10
    assert {f"DESC_{i}" for i in range(1, 6)} <= ids
    assert {f"GPC_{i}" for i in range(1, 6)} <= ids


def test_exactly_six_qualifying_pairs(opportunities):
    assert len(opportunities) == 6


def test_pair_set_matches_fixture(opportunities):
    got = {(o["desc_id"], o["gpc_id"]) for o in opportunities}
    assert got == EXPECTED_PAIRS


def test_excluded_projects_absent(opportunities):
    seen = set()
    for o in opportunities:
        seen.add(o["desc_id"])
        seen.add(o["gpc_id"])
    assert not (seen & EXCLUDED_IDS), f"excluded ids leaked in: {seen & EXCLUDED_IDS}"


def test_every_opportunity_has_required_fields(opportunities):
    for o in opportunities:
        assert o["distance_m"] is not None
        assert "day_gap" in o  # may be None only if a date is missing; here all present
        assert o["day_gap"] is not None
        assert o["tier"] in {"crossing", "shared_row", "shared_logistics", "shared_crews"}
        assert o["coordination_action"]
        assert o["confidence"]["desc"] in {"endpoint_only", "two_endpoints"}
        assert o["confidence"]["gpc"] in {"endpoint_only", "two_endpoints"}


def test_ranked_by_distance_ascending(opportunities):
    distances = [o["distance_m"] for o in opportunities]
    assert distances == sorted(distances)


def test_all_pairs_under_gate(opportunities):
    for o in opportunities:
        assert o["distance_m"] < 40_000.0


def test_day_gaps_match_reference_sheet(opportunities):
    # Day gaps are computed from in-service dates and should match the sheet's
    # time_gap column exactly (the sheet and engine agree on dates).
    ref_gap = {
        ("DESC_2", "GPC_1"): 3074,
        ("DESC_3", "GPC_2"): 152,
        ("DESC_3", "GPC_3"): 517,
        ("DESC_1", "GPC_1"): 3074,
        ("DESC_5", "GPC_2"): 365,
        ("DESC_5", "GPC_3"): 730,
    }
    for o in opportunities:
        key = (o["desc_id"], o["gpc_id"])
        assert o["day_gap"] == ref_gap[key], f"day gap mismatch for {key}"
