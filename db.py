import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "traxbase.db"


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def rebuild_tracks(tracks):
    """Drop and recreate the tracks table, then insert all scanned tracks."""
    db = get_db()
    db.execute("DROP TABLE IF EXISTS tracks")
    db.execute("""
        CREATE TABLE tracks (
            id TEXT PRIMARY KEY,
            path TEXT,
            caption TEXT
        )
    """)
    db.executemany(
        "INSERT INTO tracks (id, path, caption) VALUES (?, ?, ?)",
        [(t["id"], t["path"], t["caption"]) for t in tracks],
    )
    db.commit()
    db.close()


def get_all_tracks():
    """Return all tracks from the database."""
    db = get_db()
    try:
        rows = db.execute("SELECT id, path, caption FROM tracks").fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        db.close()
    return [dict(row) for row in rows]
