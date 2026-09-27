TIERS = [
    ("crossing", 0.0, True, "Must coordinate: outage timing, crossing structures"),
    ("shared_land", 1600.0, False, "Share right-of-way, access roads, permits"),
    ("shared_logistics", 8000.0, False, "Share laydown yards, deliveries"),
    ("shared_crews", 40000.0, False, "Share crews and equipment"),
]
CANDIDATE_RADIUS_M = 40000.0
WEIGHT_GEO = 0.7
WEIGHT_TIME = 0.3
CONFIDENCE_MULTIPLIER = {
    "confirmed_route": 1.0, "confirmed_point": 1.0,
    "inferred_endpoints": 0.85, "approximate_corridor": 0.7, "unresolved": 0.5,
}
PROJECTED_CRS = "EPSG:32617"  # UTM 17N — most accurate for SC/GA border region
