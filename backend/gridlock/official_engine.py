"""Overlap engine for the official challenge dataset (data/official).

Deterministic, offline. Compares every DESC project to every GPC project
(5 x 5 = 25 pairs) and returns ranked coordination opportunities.

Spec:
  - Primary metric : closest-point distance between full geometries
                     (LineString for two-endpoint projects, Point for
                     endpoint_only projects). Never center-to-center.
  - Inclusion gate : < 40 km (25 mi).
  - Secondary field: in-service date gap in days (absolute).
  - Coordination tier (by closest-point distance):
        touching / crossing  -> outage + crossing-structure coordination
        < 1.6 km             -> shared right-of-way / access / permits
        < 8 km               -> shared laydown yards / deliveries
        < 40 km              -> shared crews / equipment
  - Output: opportunities sorted by distance ascending.

Distances are computed in a metric CRS (UTM 17N) via shapely; this matches the
approach already used by gridlock.engine.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date, datetime

from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

# Metric projection for the SC/GA border region (same as gridlock.engine).
_PROJECTED_CRS = "EPSG:32617"  # UTM 17N
_fwd = Transformer.from_crs("EPSG:4326", _PROJECTED_CRS, always_xy=True).transform

# Inclusion gate and tier thresholds, in meters.
GATE_M = 40_000.0
MILES_PER_METER = 1 / 1609.344

# (tier_name, upper_bound_m, coordination_action)
# Evaluated in order; "crossing" is the touching/crossing case (distance == 0).
TIERS = [
    ("crossing", 0.0, "Coordinate outage timing and crossing structures"),
    ("shared_row", 1_600.0, "Share right-of-way, access roads, permits"),
    ("shared_logistics", 8_000.0, "Share laydown yards and deliveries"),
    ("shared_crews", GATE_M, "Share crews and equipment"),
]

ROOT = pathlib.Path(__file__).resolve().parents[2]
OFFICIAL_JSON = ROOT / "data" / "official" / "projects_official.json"


def load_official_projects(path: pathlib.Path | None = None) -> list[dict]:
    """Load the normalized official projects list produced by the data build."""
    path = path or OFFICIAL_JSON
    return json.loads(path.read_text())


def _parse_date(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def closest_point_distance_m(geom_a: dict, geom_b: dict) -> tuple[float, bool]:
    """Closest-point distance (meters) between two GeoJSON geometries and
    whether they touch/cross. Uses full geometries, never centroids."""
    ga = transform(_fwd, shape(geom_a))
    gb = transform(_fwd, shape(geom_b))
    return ga.distance(gb), ga.intersects(gb)


def coordination_tier(distance_m: float, touching: bool) -> tuple[str, str]:
    """Return (tier_name, coordination_action) for a qualifying distance."""
    if touching or distance_m <= 0.0:
        name, _, action = TIERS[0]
        return name, action
    for name, upper, action in TIERS[1:]:
        if distance_m < upper:
            return name, action
    # Should not happen for qualifying pairs (gate is the last upper bound).
    name, _, action = TIERS[-1]
    return name, action


def day_gap(a: dict, b: dict) -> int | None:
    """Absolute in-service date gap in days, or None if either date missing."""
    da, db = _parse_date(a.get("in_service_date")), _parse_date(b.get("in_service_date"))
    if da is None or db is None:
        return None
    return abs((da - db).days)


def find_opportunities(projects: list[dict]) -> list[dict]:
    """Compare every DESC project to every GPC project and return ranked
    opportunities that pass the < 40 km inclusion gate.

    Utility grouping is by id prefix (DESC_* vs GPC_*), matching the official
    dataset. Output is sorted by distance ascending, then by id pair.
    """
    desc = [p for p in projects if p["id"].startswith("DESC_")]
    gpc = [p for p in projects if p["id"].startswith("GPC_")]

    opportunities = []
    for a in desc:
        for b in gpc:
            distance_m, touching = closest_point_distance_m(a["geometry"], b["geometry"])
            if distance_m >= GATE_M:
                continue  # fails the inclusion gate
            tier_name, action = coordination_tier(distance_m, touching)
            opportunities.append({
                "desc_id": a["id"],
                "gpc_id": b["id"],
                "distance_m": round(distance_m, 1),
                "distance_km": round(distance_m / 1000.0, 3),
                "distance_mi": round(distance_m * MILES_PER_METER, 3),
                "day_gap": day_gap(a, b),
                "tier": tier_name,
                "coordination_action": action,
                "confidence": {
                    "desc": a.get("geometry_confidence"),
                    "gpc": b.get("geometry_confidence"),
                },
                "desc_name": a.get("project_name"),
                "gpc_name": b.get("project_name"),
            })

    opportunities.sort(key=lambda o: (o["distance_m"], o["desc_id"], o["gpc_id"]))
    return opportunities


if __name__ == "__main__":
    ops = find_opportunities(load_official_projects())
    print(f"{len(ops)} qualifying opportunities (< 40 km):\n")
    hdr = f"{'DESC':7} {'GPC':6} {'dist_km':>8} {'dist_mi':>8} {'gap_d':>6} {'tier':16} conf(desc/gpc)"
    print(hdr)
    print("-" * len(hdr))
    for o in ops:
        print(f"{o['desc_id']:7} {o['gpc_id']:6} {o['distance_km']:8.3f} {o['distance_mi']:8.3f} "
              f"{str(o['day_gap']):>6} {o['tier']:16} {o['confidence']['desc']}/{o['confidence']['gpc']}")
