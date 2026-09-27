"""P2 Revision 2.2 opportunities contract for the official challenge dataset.

This layer wires the deterministic official overlap engine (data/official) into
the shape defined by docs/specs/EDGE_CASES.md (Revision 2.2). It is offline and
deterministic: no runtime network calls, no invented coordinates, no tuning.

Distance model (ruling (a) on Blocker 3): the closest points between two
geometries are found in the metric projection EPSG:32617 (UTM 17N) via shapely
(the same method the engine already uses), and the reported distance is the
WGS 84 geodesic distance (pyproj.Geod) between those two closest points.
center_distance is the geodesic distance between the two projects' published
center points.

Rounding: serialized numbers use Decimal ROUND_HALF_UP. Python's built-in
round() is forbidden for serialized values (EDGE_CASES X15).

Errors: exactly three 503 reasons (dataset_project_count_mismatch,
unparseable_in_service_date, no_known_endpoint) and 400 invalid_project_id.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from pyproj import Geod, Transformer
from shapely.geometry import shape
from shapely.ops import nearest_points, transform

# --- constants ---------------------------------------------------------------

GATE_KM = 40.0                 # strict: qualify iff closest_distance_km < 40.0
GATE_M = GATE_KM * 1000.0
_KM_PER_MI = 1.609344
SHARED_ENDPOINT_KM = 0.001     # known-endpoint coincidence threshold

# Tier upper bounds in km. Boundary values fall into the NEXT-larger tier
# (strict < upper), e.g. 1.6 -> under_8_km, 8.0 -> under_40_km.
_TIER_BOUNDS = [
    ("under_1_6_km", 1.6),
    ("under_8_km", 8.0),
    ("under_40_km", 40.0),
]
_TIER_LABELS = {
    "touching_crossing": "Touching / crossing",
    "under_1_6_km": "Shared right-of-way, access, permits",
    "under_8_km": "Shared laydown yards and deliveries",
    "under_40_km": "Shared crews and equipment",
}
_SHARED_ENDPOINT_LABEL = "Shared endpoint facility"

OFFICIAL_IDS = {f"DESC_{i}" for i in range(1, 6)} | {f"GPC_{i}" for i in range(1, 6)}

_GEOD = Geod(ellps="WGS84")
_PROJECTED_CRS = "EPSG:32617"  # UTM 17N
_fwd = Transformer.from_crs("EPSG:4326", _PROJECTED_CRS, always_xy=True).transform
_inv = Transformer.from_crs(_PROJECTED_CRS, "EPSG:4326", always_xy=True).transform

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ContractError(Exception):
    """Raised for the contract's 503/400 conditions. Carries an HTTP status and
    a structured error body (see EDGE_CASES §1.1)."""

    def __init__(self, status: int, message: str, **details):
        super().__init__(message)
        self.status = status
        self.message = message
        self.details = details

    def body(self) -> dict:
        return {"error": {"message": self.message, "details": self.details}}


# --- helpers -----------------------------------------------------------------

def _round(value: float, places: int) -> float:
    """Decimal ROUND_HALF_UP to `places` decimals, returned as float. Never
    uses Python's round() (EDGE_CASES X15)."""
    q = Decimal(1).scaleb(-places)  # e.g. places=3 -> Decimal('0.001')
    return float(Decimal(repr(value)).quantize(q, rounding=ROUND_HALF_UP))


def _km_to_mi(km: float) -> float:
    return km / _KM_PER_MI


def _parse_date_strict(value, project_id: str):
    """Parse a strict YYYY-MM-DD date or None. Raise ContractError(503) for a
    non-null value that is not a valid strict calendar date."""
    if value in (None, ""):
        return None
    s = str(value)
    if not _ISO_DATE_RE.match(s):
        raise ContractError(
            503, "In-service date is not a valid strict YYYY-MM-DD date.",
            reason="unparseable_in_service_date", project_id=project_id, value=s,
        )
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise ContractError(
            503, "In-service date is not a valid strict YYYY-MM-DD date.",
            reason="unparseable_in_service_date", project_id=project_id, value=s,
        )


def _known_endpoints(project: dict) -> list[tuple[str, list]]:
    """Return [(label, [lon,lat]), ...] for endpoints with known coordinates."""
    out = []
    a_c, b_c = project.get("endpoint_a_coords"), project.get("endpoint_b_coords")
    if a_c is not None:
        out.append((project.get("endpoint_a_name"), a_c))
    if b_c is not None:
        out.append((project.get("endpoint_b_name"), b_c))
    return out


def _geometry_kind(project: dict) -> str:
    """'endpoint_pair' when both endpoints known, else 'endpoint_only'."""
    conf = project.get("geometry_confidence")
    # map dataset vocabulary two_endpoints -> endpoint_pair
    if conf == "two_endpoints":
        return "endpoint_pair"
    if conf == "endpoint_only":
        return "endpoint_only"
    # derive from coordinates as a fallback
    return "endpoint_pair" if len(_known_endpoints(project)) == 2 else "endpoint_only"


def _geodesic_km(lon1, lat1, lon2, lat2) -> float:
    _, _, dist_m = _GEOD.inv(lon1, lat1, lon2, lat2)
    return dist_m / 1000.0


def _closest_points_wgs84(geom_a: dict, geom_b: dict):
    """Find closest points in EPSG:32617, return them back in WGS84 as
    ([lon,lat] on A, [lon,lat] on B, intersects: bool)."""
    ga = transform(_fwd, shape(geom_a))
    gb = transform(_fwd, shape(geom_b))
    pa, pb = nearest_points(ga, gb)
    a_ll = list(_inv(pa.x, pa.y))
    b_ll = list(_inv(pb.x, pb.y))
    return a_ll, b_ll, ga.intersects(gb)


def _tier_for(distance_km: float, shared_endpoint: bool, touching: bool):
    """Return (coordination_tier, coordination_tier_label)."""
    if shared_endpoint:
        return "touching_crossing", _SHARED_ENDPOINT_LABEL
    if touching or distance_km <= SHARED_ENDPOINT_KM:
        return "touching_crossing", _TIER_LABELS["touching_crossing"]
    for name, upper in _TIER_BOUNDS:
        if distance_km < upper:
            return name, _TIER_LABELS[name]
    # qualifying pairs are always < 40.0, so this is unreachable for opportunities
    return "under_40_km", _TIER_LABELS["under_40_km"]


def _pair_geometry_confidence(desc_kind: str, gpc_kind: str) -> str:
    if desc_kind == "endpoint_only" and gpc_kind == "endpoint_only":
        return "both_endpoint_only"
    if desc_kind == "endpoint_pair" and gpc_kind == "endpoint_pair":
        return "both_endpoint_pair"
    return "mixed"


def _distance_basis(desc_kind: str, gpc_kind: str) -> str:
    if desc_kind == "endpoint_only" and gpc_kind == "endpoint_only":
        return "point_to_point"
    if desc_kind == "endpoint_pair" and gpc_kind == "endpoint_pair":
        return "segment_to_segment"
    return "point_to_segment"


def _detect_shared_endpoint(desc: dict, gpc: dict):
    """Return (detected: bool, name: str|None). A shared endpoint exists when a
    known DESC endpoint and a known GPC endpoint are within SHARED_ENDPOINT_KM.
    The name concatenates the two dataset labels verbatim (no case change)."""
    best = None
    for d_label, d_c in _known_endpoints(desc):
        for g_label, g_c in _known_endpoints(gpc):
            km = _geodesic_km(d_c[0], d_c[1], g_c[0], g_c[1])
            if km <= SHARED_ENDPOINT_KM and (best is None or km < best[0]):
                best = (km, d_label, g_label)
    if best is None:
        return False, None
    _, d_label, g_label = best
    return True, f"{d_label} / {g_label}"


# --- validation --------------------------------------------------------------

@dataclass
class ValidatedDataset:
    projects: dict          # id -> project
    parsed_dates: dict      # id -> date|None
    endpoint_only_count: int


def validate_dataset(projects: list[dict]) -> ValidatedDataset:
    """Enforce the three 503 dataset preconditions and pre-parse dates.

    - dataset_project_count_mismatch: count != 10 or id-set != the 10 official IDs
      (duplicates make the count wrong or the set incomplete).
    - no_known_endpoint: a project has neither endpoint known.
    - unparseable_in_service_date: a non-null date is not strict YYYY-MM-DD.
    """
    ids = [p["id"] for p in projects]
    if len(ids) != 10 or set(ids) != OFFICIAL_IDS or len(set(ids)) != len(ids):
        raise ContractError(
            503, "Approved dataset must contain exactly the ten official projects.",
            reason="dataset_project_count_mismatch", expected=10, found=len(ids),
        )
    by_id, parsed = {}, {}
    endpoint_only = 0
    for p in projects:
        pid = p["id"]
        if not _known_endpoints(p):
            raise ContractError(
                503, "Project has no known endpoint.",
                reason="no_known_endpoint", project_id=pid,
            )
        parsed[pid] = _parse_date_strict(p.get("in_service_date"), pid)
        if _geometry_kind(p) == "endpoint_only":
            endpoint_only += 1
        by_id[pid] = p
    return ValidatedDataset(by_id, parsed, endpoint_only)


# --- main contract build -----------------------------------------------------

def build_opportunities(projects: list[dict], *, result_source: str = "official_reference") -> dict:
    """Build the full Revision 2.2 opportunities payload from the dataset.

    Returns {"data": [...], "meta": {...}}. Raises ContractError for the
    documented 503 conditions. Only cross-utility (DESC x GPC) pairs under the
    strict < 40 km gate are returned, ranked per EDGE_CASES §5.
    """
    vd = validate_dataset(projects)
    desc = sorted([p for p in projects if p["id"].startswith("DESC_")], key=lambda p: p["id"])
    gpc = sorted([p for p in projects if p["id"].startswith("GPC_")], key=lambda p: p["id"])

    rows = []
    for a in desc:
        for b in gpc:
            row = _evaluate_pair(a, b, vd)
            if row is not None:
                rows.append(row)

    # Rank: full-precision km asc, then date_gap_days asc (null last), then
    # opportunity_id asc (bytewise).
    rows.sort(key=lambda r: (
        r["_full_km"],
        (1, 0) if r["date_gap_days"] is None else (0, r["date_gap_days"]),
        r["opportunity_id"],
    ))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
        del r["_full_km"]

    return {
        "data": rows,
        "meta": {
            "result_source": result_source,
            "gate_km": GATE_KM,
            "gate_m": GATE_M,
            "pair_count": 25,
            "opportunity_count": len(rows),
            "endpoint_only_count": vd.endpoint_only_count,
        },
    }


def _evaluate_pair(desc: dict, gpc: dict, vd: ValidatedDataset):
    """Evaluate one DESC x GPC pair. Return the opportunity dict, or None if it
    fails the strict < 40 km gate."""
    a_ll, b_ll, intersects = _closest_points_wgs84(desc["geometry"], gpc["geometry"])
    closest_km_full = 0.0 if intersects else _geodesic_km(a_ll[0], a_ll[1], b_ll[0], b_ll[1])

    if not (closest_km_full < GATE_KM):   # strict gate; 40.0 excluded
        return None

    desc_kind = _geometry_kind(desc)
    gpc_kind = _geometry_kind(gpc)
    shared_detected, shared_name = _detect_shared_endpoint(desc, gpc)
    tier, tier_label = _tier_for(closest_km_full, shared_detected, intersects)

    # center-to-center geodesic (reported, never used for the gate)
    dc, gc = desc.get("center_geometry"), gpc.get("center_geometry")
    center_km_full = _geodesic_km(dc[0], dc[1], gc[0], gc[1]) if dc and gc else None

    # dates
    d_date, g_date = vd.parsed_dates[desc["id"]], vd.parsed_dates[gpc["id"]]
    if d_date is None or g_date is None:
        gap_signed = gap_abs = None
    else:
        gap_signed = (g_date - d_date).days     # positive => GPC later
        gap_abs = abs(gap_signed)

    endpoint_only_side = desc_kind == "endpoint_only" or gpc_kind == "endpoint_only"

    return {
        "opportunity_id": f"{desc['id']}__{gpc['id']}",
        "rank": None,  # assigned after sort
        "desc_project_id": desc["id"],
        "gpc_project_id": gpc["id"],
        "closest_distance_km": _round(closest_km_full, 3),
        "closest_distance_mi": _round(_km_to_mi(closest_km_full), 3),
        "center_distance_km": None if center_km_full is None else _round(center_km_full, 3),
        "center_distance_mi": None if center_km_full is None else _round(_km_to_mi(center_km_full), 3),
        "coordination_tier": tier,
        "coordination_tier_label": tier_label,
        "tier_confidence": "reduced" if endpoint_only_side else "high",
        "date_gap_days": gap_abs,
        "date_gap_days_signed": gap_signed,
        "distance_basis": _distance_basis(desc_kind, gpc_kind),
        "pair_geometry_confidence": _pair_geometry_confidence(desc_kind, gpc_kind),
        "is_endpoint_only_estimate": endpoint_only_side,
        "shared_endpoint_detected": shared_detected,
        "shared_endpoint_name": shared_name,
        "closest_point_desc": [_round(a_ll[0], 6), _round(a_ll[1], 6)],
        "closest_point_gpc": [_round(b_ll[0], 6), _round(b_ll[1], 6)],
        "closest_connector": {
            "type": "LineString",
            "coordinates": [
                [_round(a_ll[0], 6), _round(a_ll[1], 6)],
                [_round(b_ll[0], 6), _round(b_ll[1], 6)],
            ],
        },
        "data_warnings": [],
        "result_source": "official_reference",
        # internal ranking key, removed before serialization
        "_full_km": closest_km_full,
    }


def validate_project_id(project_id: str) -> None:
    """Raise ContractError(400) if project_id is not one of the official IDs
    (case-sensitive)."""
    if project_id not in OFFICIAL_IDS:
        raise ContractError(
            400, "Unknown or wrong-case project_id.",
            reason="invalid_project_id", project_id=project_id,
        )


def filter_by_project(payload: dict, project_id: str) -> dict:
    """Return the payload subset for a single project, preserving original rank
    and order. Assumes project_id already validated."""
    subset = [
        r for r in payload["data"]
        if r["desc_project_id"] == project_id or r["gpc_project_id"] == project_id
    ]
    meta = dict(payload["meta"])
    meta["opportunity_count"] = len(subset)
    meta["filtered_project_id"] = project_id
    return {"data": subset, "meta": meta}
