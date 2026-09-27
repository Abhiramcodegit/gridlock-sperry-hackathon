#!/usr/bin/env python3
# GridLock projection / model-error Monte Carlo — reproduction tool for GEOMETRY_MATH.md section 8.
#
# PINNED ENVIRONMENT (required for byte-identical output):
#   numpy==1.26.4
#   pyproj==3.7.1   (only needed for the wgs84_model_error population)
# NumPy does not guarantee identical random streams across versions. Other
# versions may produce different sample maxima.
#
# Usage:  python3 docs/specs/tools/projection_error_mc.py
# Output: JSON on stdout. Runtime is roughly 10 seconds.
#
# Classification of results (read before quoting any number):
#   ga_sc_all, ga_sc_within_40km, continental_us:
#       PROJECTION ERROR INTERNAL TO THE SPHERICAL MODEL. Reference is the
#       spec's own sphere (haversine, R = 6371.0088 km). This is a
#       self-consistency measurement, NOT an accuracy measurement.
#   wgs84_model_error:
#       ACCURACY AGAINST WGS 84. Reference is the WGS 84 ellipsoid geodesic
#       (pyproj.Geod). Compares the spherical model and UTM 17N planar distance.
# All figures are sample statistics, not proven bounds.
# Every population uses its own independent generator seeded with 7.
import json
import sys

import numpy as np

R = 6371.0088
GASC = ((30.3, 35.3), (-85.7, -78.5))
CONUS = ((25.0, 49.0), (-125.0, -67.0))


def hv(p1, l1, p2, l2):
    p1, l1, p2, l2 = map(np.radians, (p1, l1, p2, l2))
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2
    a = np.clip(a, 0.0, 1.0)
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def engine(P, A, B):
    phi0 = np.radians((P[0] + A[0] + B[0]) / 3.0)
    c = np.cos(phi0)
    pr = lambda q: np.array([R * np.radians(q[1]) * c, R * np.radians(q[0])])
    p, a, b = pr(P), pr(A), pr(B)
    v = b - a
    L2 = v @ v
    t = 0.0 if L2 < 1e-12 else float(np.clip((p - a) @ v / L2, 0.0, 1.0))
    q = a + t * v
    return float(hv(P[0], P[1], np.degrees(q[1] / R), np.degrees(q[0] / (R * c))))


def reference(P, A, B, n):
    t = np.linspace(0.0, 1.0, n)
    return float(hv(P[0], P[1], A[0] + t * (B[0] - A[0]), A[1] + t * (B[1] - A[1])).min())


def population(name, box, n_samples, n_ref, seed, near=False):
    rng = np.random.default_rng(seed)
    rel, ab = [], []
    while len(rel) < n_samples:
        A = (rng.uniform(*box[0]), rng.uniform(*box[1]))
        B = (rng.uniform(*box[0]), rng.uniform(*box[1]))
        if near:
            u = rng.uniform(0, 1)
            P = (A[0] + u * (B[0] - A[0]) + rng.uniform(-0.35, 0.35),
                 A[1] + u * (B[1] - A[1]) + rng.uniform(-0.40, 0.40))
        else:
            P = (rng.uniform(*box[0]), rng.uniform(*box[1]))
        g = reference(P, A, B, n_ref)
        if g < 0.5 or (near and g >= 40.0):
            continue
        o = engine(P, A, B)
        rel.append((o - g) / g)
        ab.append(o - g)
    rel, ab = np.array(rel), np.array(ab)
    return {"population": name,
            "classification": "projection error internal to the spherical model",
            "seed": seed, "samples": n_samples, "reference_points": n_ref,
            "max_rel_pct": round(float(rel.max() * 100), 4),
            "p99_rel_pct": round(float(np.percentile(rel, 99) * 100), 4),
            "max_abs_m": round(float(ab.max() * 1000), 1)}


def wgs84_model_error(seed=7, n=4000):
    from pyproj import Geod, Transformer
    geod = Geod(ellps="WGS84")
    tr = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True)
    rng = np.random.default_rng(seed)
    lat = rng.uniform(*GASC[0], n)
    lon = rng.uniform(*GASC[1], n)
    az = rng.uniform(0, 2 * np.pi, n)
    dist_km = rng.uniform(0.5, 40.0, n)
    lon2, lat2, _ = geod.fwd(lon, lat, np.degrees(az), dist_km * 1000)
    g = np.asarray(geod.inv(lon, lat, lon2, lat2)[2]) / 1000
    s = hv(lat, lon, lat2, lon2)
    x1, y1 = tr.transform(lon, lat)
    x2, y2 = tr.transform(lon2, lat2)
    u = np.hypot(np.asarray(x2) - np.asarray(x1), np.asarray(y2) - np.asarray(y1)) / 1000
    border = (lon > -82.5) & (lon < -80.5) & (lat > 32.0) & (lat < 34.0)
    pct = lambda m: (m - g) / g * 100
    rs, ru = pct(s), pct(u)
    return {"population": "wgs84_model_error",
            "classification": "accuracy against WGS 84 geodesic (pyproj.Geod)",
            "seed": seed, "point_pairs": n, "separation_km": [0.5, 40.0],
            "sphere_rel_pct_range": [round(float(rs.min()), 4), round(float(rs.max()), 4)],
            "sphere_max_abs_m": round(float(np.abs(s - g).max() * 1000), 1),
            "utm17n_rel_pct_range": [round(float(ru.min()), 4), round(float(ru.max()), 4)],
            "utm17n_max_abs_m": round(float(np.abs(u - g).max() * 1000), 1),
            "utm17n_border_subregion_rel_pct_range": [round(float(ru[border].min()), 4),
                                                      round(float(ru[border].max()), 4)]}


if __name__ == "__main__":
    import pyproj
    out = {"numpy": np.__version__, "pyproj": pyproj.__version__, "results": [
        population("ga_sc_all", GASC, 3000, 20001, 7),
        population("ga_sc_within_40km", GASC, 1500, 40001, 7, near=True),
        population("continental_us", CONUS, 2000, 20001, 7),
        wgs84_model_error(7),
    ]}
    json.dump(out, sys.stdout, indent=2)
    print()
