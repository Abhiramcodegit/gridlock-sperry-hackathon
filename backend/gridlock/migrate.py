"""Startup migration / ingestion for GridLock.

Run once at process startup (or manually) to load the proposed rows from
projects_proposed.csv into PostGIS. Kept OUT of the per-request path so
/opportunities stays a read-only query.

CLI usage:
    export GRIDLOCK_DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/gridlock
    python -m gridlock.migrate
"""
import sys

from . import db


def run() -> int:
    """Ingest proposed rows into PostGIS. Returns the number of rows loaded.

    No-op (returns 0) when no database is configured, so importing/calling this
    is safe in file-only mode.
    """
    if not db.database_url():
        return 0
    with db.connect() as conn:
        return db.ingest_csv(conn)


if __name__ == "__main__":
    if not db.database_url():
        print("GRIDLOCK_DATABASE_URL not set — nothing to migrate.")
        sys.exit(0)
    n = run()
    print(f"Ingested {n} proposed rows into PostGIS.")
