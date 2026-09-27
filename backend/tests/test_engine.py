from datetime import date
import pytest
from pyproj import Transformer
from gridlock.engine import Project, min_distance, tier, timeline, find_opportunities, score
inv = Transformer.from_crs("EPSG:32617","EPSG:4326",always_xy=True).transform
X0, Y0 = 500000, 3550000  # SYNTHETIC TEST DATA ONLY — not real utility projects
def pt(dx=0, dy=0): return {"type":"Point","coordinates":list(inv(X0+dx,Y0+dy))}
def ln(*xy): return {"type":"LineString","coordinates":[list(inv(X0+x,Y0+y)) for x,y in xy]}

def test_point_point(): assert min_distance(pt(), pt(3000))[0] == pytest.approx(3000, abs=0.01)
def test_point_line(): assert min_distance(pt(0,500), ln((-1000,0),(1000,0)))[0] == pytest.approx(500, abs=0.01)
def test_line_line(): assert min_distance(ln((0,0),(1000,0)), ln((0,2000),(1000,2000)))[0] == pytest.approx(2000, abs=0.01)
def test_intersecting():
    d, x, _ = min_distance(ln((-1000,0),(1000,0)), ln((0,-1000),(0,1000)))
    assert x and tier(d, x)[0] == "crossing"
@pytest.mark.parametrize("d,exp",[(1599.9,"shared_land"),(1600,"shared_logistics"),(7999.9,"shared_logistics"),
    (8000,"shared_crews"),(39999.9,"shared_crews"),(40000,None),(40000.1,None)])
def test_boundaries(d, exp):
    t = tier(d, False); assert (t[0] if t else None) == exp
def test_long_line_centroid_far_but_segment_close():
    line = ln((0,0),(60000,0)); d = min_distance(pt(-5000,0), line)[0]
    assert d == pytest.approx(5000, abs=0.01) and tier(d, False)[0] == "shared_logistics"
def P(s,e,u="A"): return Project("x",u,"x",pt(),"confirmed_point",s,e)
def test_unknown(): assert timeline(P(None,None), P(date(2027,1,1),date(2027,6,1)))[0] == "unknown"
def test_no_overlap(): assert timeline(P(date(2026,1,1),date(2026,6,1)), P(date(2027,1,1),date(2027,6,1)))[0] == "no_overlap"
def test_partial(): assert timeline(P(date(2026,1,1),date(2026,12,31)), P(date(2026,7,1),date(2027,6,1)))[0] == "partial_overlap"
def test_full(): assert timeline(P(date(2026,1,1),date(2026,12,31)), P(date(2026,3,1),date(2026,4,1)))[0] == "full_overlap"
def test_approx_penalty():
    assert score(1000,False,0,"approximate_corridor","confirmed_point")[0] < score(1000,False,0,"confirmed_point","confirmed_point")[0]
def test_cross_utility_only_and_approved_only():
    a = Project("a","DESC","a",pt(),"confirmed_point",review_status="approved")
    b = Project("b","DESC","b",pt(100),"confirmed_point",review_status="approved")
    c = Project("c","GPC","c",pt(200),"confirmed_point",review_status="approved")
    d = Project("d","GPC","d",pt(50),"confirmed_point",review_status="proposed")
    ids = {(o["project_a"],o["project_b"]) for o in find_opportunities([a,b,c,d])}
    assert ids == {("a","c"),("b","c")}


# --- 40 km gate boundary parity (strict <40000; 40000.0 m EXCLUDED) ---
# Regression for the gate-semantics divergence: engine.tier() and db._tier()
# must both reject exactly 40000.0 m so they agree with the contract's strict
# closest_km_full < 40.0 gate.
def test_engine_tier_excludes_exact_40000():
    # exactly at the boundary -> no tier (excluded)
    assert tier(40000.0, False) is None
def test_engine_tier_includes_just_under_40000():
    t = tier(39999.999, False)
    assert t is not None and t[0] == "shared_crews"
def test_db_tier_excludes_exact_40000():
    from gridlock.db import _tier as db_tier
    assert db_tier(40000.0, False) is None
def test_db_tier_includes_just_under_40000():
    from gridlock.db import _tier as db_tier
    t = db_tier(39999.999, False)
    assert t is not None and t[0] == "shared_crews"
def test_engine_and_db_tier_agree_at_boundary():
    from gridlock.db import _tier as db_tier
    for d in (39999.999, 40000.0, 40000.001):
        e = tier(d, False)
        b = db_tier(d, False)
        assert (e[0] if e else None) == (b[0] if b else None)
