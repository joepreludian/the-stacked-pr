"""SQLite connection and the migration runner."""

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def connect(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn):
    """Apply every migration that has not run yet, in filename order."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
    applied = {row["name"] for row in conn.execute("SELECT name FROM schema_migrations")}
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in applied:
            continue
        conn.executescript(path.read_text())
        conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (path.name,))
    conn.commit()
