import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "traxbase.db"
USERDATA_DB_PATH = Path(__file__).resolve().parent.parent / "userdata.db"


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def get_userdata_db():
    db = sqlite3.connect(USERDATA_DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def ensure_userdata_schema():
    db = get_userdata_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS track_userdata (
            track_id TEXT PRIMARY KEY,
            custom_title TEXT,
            description TEXT,
            starred INTEGER NOT NULL DEFAULT 0,
            suno INTEGER NOT NULL DEFAULT 0,
            hide INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Add columns if upgrading from an older schema
    for col in ("starred", "suno", "hide"):
        try:
            db.execute(f"ALTER TABLE track_userdata ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # column already exists
    db.commit()
    db.close()


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
    """Return all tracks from the database, with userdata joined in."""
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
    tracks = [dict(row) for row in rows]

    userdata_db = get_userdata_db()
    try:
        ud_rows = userdata_db.execute(
            "SELECT track_id, custom_title, description, starred, suno, hide FROM track_userdata"
        ).fetchall()
    except sqlite3.OperationalError:
        ud_rows = []
    finally:
        userdata_db.close()
    ud_map = {row["track_id"]: dict(row) for row in ud_rows}

    for track in tracks:
        ud = ud_map.get(track["id"], {})
        track["custom_title"] = ud.get("custom_title") or ""
        track["description"] = ud.get("description") or ""
        track["starred"] = bool(ud.get("starred"))
        track["suno"] = bool(ud.get("suno"))
        track["hide"] = bool(ud.get("hide"))
        track["display_title"] = track["custom_title"] or track["title_raw"] or track["path"]

    return tracks


def get_track_by_id(track_id):
    """Return a single track as a dict, or None if not found."""
    db = get_db()
    try:
        row = db.execute(
            """SELECT id, path, caption, lyrics, title_raw, instrumental,
                      bpm, keyscale, timesignature, duration, duration_output,
                      file_modified, seed, lm_negative_prompt
               FROM tracks WHERE id = ?""",
            (track_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    finally:
        db.close()
    if row:
        return dict(row)
    return None


def get_track_userdata(track_id):
    """Return userdata for a single track, or empty defaults."""
    db = get_userdata_db()
    try:
        row = db.execute(
            "SELECT custom_title, description, starred, suno, hide FROM track_userdata WHERE track_id = ?",
            (track_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        row = None
    finally:
        db.close()
    if row:
        return {
            "custom_title": row["custom_title"] or "",
            "description": row["description"] or "",
            "starred": bool(row["starred"]),
            "suno": bool(row["suno"]),
            "hide": bool(row["hide"]),
        }
    return {"custom_title": "", "description": "", "starred": False, "suno": False, "hide": False}


def save_track_userdata(track_id, custom_title, description, starred, suno, hide):
    """Insert or update userdata for a track."""
    db = get_userdata_db()
    db.execute(
        """INSERT INTO track_userdata (track_id, custom_title, description, starred, suno, hide)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(track_id) DO UPDATE SET
               custom_title = excluded.custom_title,
               description = excluded.description,
               starred = excluded.starred,
               suno = excluded.suno,
               hide = excluded.hide""",
        (track_id, custom_title, description, int(starred), int(suno), int(hide)),
    )
    db.commit()
    db.close()
