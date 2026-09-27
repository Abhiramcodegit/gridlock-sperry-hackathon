"""PostGIS integration tests for the GridLock engine.

These tests hit a REAL PostGIS database. They are skipped automatically when
GRIDLOCK_DATABASE_URL is not set, so the unit suite still runs on machines
without a database. To run them:

    docker compose up -d db
    export GRIDLOCK_DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/gridlock
    pytest backend/tests/test_db_integration.py

The schema (db/schema.sql) is applied automatically by the postgis container
on first start (mounted as an init script in docker-compose.yml).
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("GRIDLOCK_DATABASE_URL"),
    reason="GRIDLOCK_DATABASE_URL not set — no PostGIS database available.",
)

from gridlock import db  # noqa: E402  (import after skip guard)


@pytest.fixture()
def conn():
    c = db.connect()
    # Clean slate each test so runs are deterministic.
    with c.cursor() as cur:
        cur.execute("TRUNCATE projects")
    c.commit()
    yield c
    c.close()


def test_ingest_loads_proposed_rows(conn):
    n = db.ingest_csv(conn)
    assert n > 0
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM projects")
        assert cur.fetchone()[0] == n
        # Only GPC-004 and DESC-003 currently carry geometry in the CSV.
        cur.execute("SELECT id FROM projects WHERE geom IS NOT NULL ORDER BY id")
        assert [r[0] for r in cur.fetchall()] == ["DESC-003", "GPC-004"]


def test_opportunities_empty_when_nothing_approved(conn):
    """All rows are 'proposed', so no approved pair exists -> empty list.

    This is the CORRECT answer, not a bug: the candidate_pairs view only
    considers review_status='approved' rows with geometry.
    """
    db.ingest_csv(conn)
    assert db.find_opportunities(conn) == []


def test_stdwithin_rejects_the_117km_proxy_pair(conn):
    """If GPC-004 and DESC-003 were both approved, they are ~117 km apart and
    must NOT pass the 40 km ST_DWithin candidate filter — matching the
    documented honest-negative proxy-distance result.
    """
    db.ingest_csv(conn)
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE projects SET review_status='approved' WHERE id IN ('GPC-004','DESC-003')"
        )
    conn.commit()
    # Distance must exceed the 40 km threshold, so the pair is filtered out.
    assert db.find_opportunities(conn) == []
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ST_Distance(a.geom, b.geom) FROM projects a, projects b "
            "WHERE a.id='GPC-004' AND b.id='DESC-003'"
        )
        dist = float(cur.fetchone()[0])
    assert dist > 40000  # ~116,993 m


def test_stdwithin_accepts_a_nearby_approved_cross_utility_pair(conn):
    """Positive control: two approved cross-utility rows placed <40 km apart
    (synthetic geometry) DO produce an opportunity. Proves the pipeline emits
    results when the data actually qualifies — so the empty result above is
    caused by the data, not a broken query.
    """
    db.ingest_csv(conn)
    with conn.cursor() as cur:
        # Move DESC-003 to ~5 km from GPC-004 and approve both. Synthetic
        # coordinate for TEST ONLY — never written back to the CSV.
        cur.execute(
            "UPDATE projects SET geom = ST_GeogFromText('POINT(-81.13 32.354)'), "
            "review_status='approved' WHERE id='DESC-003'"
        )
        cur.execute("UPDATE projects SET review_status='approved' WHERE id='GPC-004'")
    conn.commit()
    opps = db.find_opportunities(conn)
    assert len(opps) == 1
    pair = {opps[0]["project_a"], opps[0]["project_b"]}
    assert pair == {"GPC-004", "DESC-003"}
    assert opps[0]["distance_m"] < 40000
