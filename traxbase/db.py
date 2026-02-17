import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "traxbase.db"


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def rebuild_tracks(tracks):
    """Drop and recreate the tracks table, then insert all scanned tracks.

    Returns a list of dicts describing skipped tracks, e.g.
    ``[{"id": "abc", "path": "Artist/abc.mp3", "reason": "duplicate id"}]``.
    An empty list means every track was inserted successfully.
    """
    skipped = []
    db = get_db()
    db.execute("DROP TABLE IF EXISTS tracks")
    db.execute("""
        CREATE TABLE tracks (
            id TEXT PRIMARY KEY,
            path TEXT,
            caption TEXT,
            lyrics TEXT,
            title_raw TEXT,
            instrumental INTEGER,
            bpm INTEGER,
            keyscale TEXT,
            timesignature TEXT,
            duration INTEGER,
            duration_output INTEGER,
            file_modified TEXT,
            seed INTEGER,
            lm_negative_prompt TEXT
        )
    """)
    for t in tracks:
        try:
            db.execute(
                """INSERT INTO tracks
                   (id, path, caption, lyrics, title_raw, instrumental, bpm,
                    keyscale, timesignature, duration, duration_output,
                    file_modified, seed, lm_negative_prompt)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    t["id"], t["path"], t["caption"], t["lyrics"],
                    t["title_raw"], int(t["instrumental"]),
                    t["bpm"], t["keyscale"], t["timesignature"],
                    t["duration"], t["duration_output"],
                    t["file_modified"], t["seed"],
                    t["lm_negative_prompt"],
                ),
            )
        except sqlite3.IntegrityError:
            skipped.append({"id": t["id"], "path": t["path"], "reason": "duplicate id"})
        except Exception as exc:
            skipped.append({"id": t["id"], "path": t["path"], "reason": str(exc)})
    db.commit()
    db.close()
    return skipped


def get_all_tracks():
    """Return all tracks from the database."""
    db = get_db()
    try:
        rows = db.execute(
            """SELECT id, path, caption, lyrics, title_raw, instrumental,
                      bpm, keyscale, timesignature, duration, duration_output,
                      file_modified, seed, lm_negative_prompt
               FROM tracks
               ORDER BY file_modified DESC"""
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        db.close()
    return [dict(row) for row in rows]
