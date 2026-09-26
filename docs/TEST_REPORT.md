# Test Report
All 17 synthetic-fixture engine tests passed in the sandbox.

Tests cover: point-point, point-line, line-line, intersecting geometries, all 4 tier boundaries (1.6 km, 8 km, 40 km just inside/outside), a 60 km line whose nearest point is 5 km away, unknown/no-overlap/partial/full timeline scenarios, approximate-geometry confidence penalty, cross-utility-only filtering, and approved-only filtering.

Run yourself: `cd backend && pip install -r requirements.txt && pytest -v`
