"""Deterministic GridLock engine. No LLM decides anything here."""
from dataclasses import dataclass
from datetime import date
from typing import Optional
from shapely.geometry import shape
from shapely.ops import nearest_points, transform
from pyproj import Transformer
from . import config as C

_fwd = Transformer.from_crs("EPSG:4326", C.PROJECTED_CRS, always_xy=True).transform
_inv = Transformer.from_crs(C.PROJECTED_CRS, "EPSG:4326", always_xy=True).transform

@dataclass
class Project:
    id: str; utility: str; name: str; geometry: dict
    geometry_confidence: str = "unresolved"
    construction_start: Optional[date] = None
    construction_end: Optional[date] = None
    review_status: str = "proposed"

def min_distance(a: dict, b: dict):
    """Minimum distance in meters between FULL geometries (never centroids)."""
    ga, gb = transform(_fwd, shape(a)), transform(_fwd, shape(b))
    pa, pb = nearest_points(ga, gb)
    seg = [list(_inv(pa.x, pa.y)), list(_inv(pb.x, pb.y))]
    return ga.distance(gb), ga.intersects(gb), seg

def tier(distance_m: float, intersects: bool):
    if intersects or distance_m == 0: return C.TIERS[0]
    for t in C.TIERS[1:]:
        name, mx, inc, _ = t
        if distance_m < mx or (inc and distance_m == mx): return t
    return None

def timeline(a, b):
    if None in (a.construction_start, a.construction_end, b.construction_start, b.construction_end):
        return "unknown", 0.0
    s, e = max(a.construction_start, b.construction_start), min(a.construction_end, b.construction_end)
    if s > e: return "no_overlap", 0.0
    ov = (e - s).days + 1
    shortest = min((a.construction_end-a.construction_start).days, (b.construction_end-b.construction_start).days) + 1
    frac = ov / shortest
    return ("full_overlap" if frac >= 1 else "partial_overlap"), round(frac, 4)

def score(distance_m, intersects, t_frac, conf_a, conf_b):
    g = 1.0 if intersects else max(0.0, 1 - distance_m / C.CANDIDATE_RADIUS_M)
    c = min(C.CONFIDENCE_MULTIPLIER.get(conf_a, .5), C.CONFIDENCE_MULTIPLIER.get(conf_b, .5))
    return round(100 * (C.WEIGHT_GEO * g + C.WEIGHT_TIME * t_frac) * c, 2), c

def find_opportunities(projects, approved_only=True):
    ps = [p for p in projects if (p.review_status == "approved" or not approved_only)]
    out = []
    for i, a in enumerate(ps):
        for b in ps[i+1:]:
            if a.utility == b.utility: continue
            d, x, seg = min_distance(a.geometry, b.geometry)
            t = tier(d, x)
            if t is None: continue
            ts, tf = timeline(a, b)
            s, c = score(d, x, tf, a.geometry_confidence, b.geometry_confidence)
            out.append(dict(project_a=a.id, project_b=b.id, distance_m=round(d, 1), intersects=x,
                tier=t[0], coordination_action=t[3], timeline_status=ts, timeline_overlap_fraction=tf,
                confidence_multiplier=c, score=s, closest_segment=seg))
    return sorted(out, key=lambda o: (-o["score"], o["distance_m"]))
