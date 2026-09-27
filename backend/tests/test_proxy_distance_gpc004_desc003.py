"""Reproducible proxy-distance regression test: GPC-004 <-> DESC-003.

Locks in the authorized deterministic result documented in
docs/PROXY_DISTANCE_RESULT.md. Both points are INFERRED substation proxies,
not confirmed project geometries. The pair is ~117 km apart and does NOT
qualify under the 40 km candidate threshold. This is an honest negative
result that validates the engine's threshold logic.
"""
from pyproj import Geod, Transformer
from shapely.geometry import Point
from shapely.ops import transform

# Human-approved inferred proxy geometries (GeoJSON [lon, lat]) from
# data/normalized/projects_proposed.csv, commit e527a46.
GPC004_WEST_MCINTOSH = (-81.1824528, 32.3543695)   # Effingham County 500 kV proxy
DESC003_CHURCH_CREEK = (-80.0702792, 32.8303196)   # Long Savannah 115 kV Tap proxy

CANDIDATE_RADIUS_M = 40000.0  # matches backend/gridlock/config.py


def _geodesic_m(a, b):
    """WGS84 geodesic meters == PostGIS ST_Distance on geography."""
    _, _, d = Geod(ellps="WGS84").inv(a[0], a[1], b[0], b[1])
    return d


def _utm17n_m(a, b):
    """UTM 17N planar meters == engine min_distance projection (EPSG:32617)."""
    fwd = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True).transform
    return transform(fwd, Point(a)).distance(transform(fwd, Point(b)))


def test_proxy_distance_geodesic_value():
    d = _geodesic_m(GPC004_WEST_MCINTOSH, DESC003_CHURCH_CREEK)
    # ~116,993 m; allow 1 m tolerance for library/version drift.
    assert abs(d - 116993.25) < 1.0


def test_proxy_distance_not_within_40km_threshold():
    d = _geodesic_m(GPC004_WEST_MCINTOSH, DESC003_CHURCH_CREEK)
    assert d > CANDIDATE_RADIUS_M  # honest negative: pair does NOT qualify


def test_geodesic_and_utm_methods_agree():
    dg = _geodesic_m(GPC004_WEST_MCINTOSH, DESC003_CHURCH_CREEK)
    du = _utm17n_m(GPC004_WEST_MCINTOSH, DESC003_CHURCH_CREEK)
    # Two independent methods should agree within 100 m at ~117 km.
    assert abs(dg - du) < 100.0
