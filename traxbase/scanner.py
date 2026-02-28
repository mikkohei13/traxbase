import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import mutagen

MUSIC_DIR = Path(__file__).resolve().parent.parent / "music"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac"}

_TITLE_RE = re.compile(r"^\[Title:\s*(.+?)\]")


def parse_title_raw(lyrics):
    """Extract the title from the first line of lyrics.

    Looks for a pattern like ``[Title: Songname is Here]`` on the first line
    and returns the title text, or None if not found.
    """
    if not lyrics:
        return None
    first_line = lyrics.split("\n", 1)[0].strip()
    m = _TITLE_RE.match(first_line)
    if m:
        return m.group(1).strip()
    return None


def get_audio_duration(filepath):
    """Return the duration of an audio file in seconds (rounded), or None."""
    try:
        audio = mutagen.File(filepath)
        if audio is not None and audio.info is not None:
            return round(audio.info.length)
    except Exception:
        pass
    return None


def _str_field(meta, key, maxlen):
    """Read a string field from metadata, truncating to maxlen."""
    val = meta.get(key)
    return str(val)[:maxlen] if val is not None else None


def _int_field(meta, key):
    """Read an integer field from metadata, returning None on failure."""
    val = meta.get(key)
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _normalize_metadata(raw: dict) -> dict:
    """Normalize metadata to ace-gui-v1 flat structure. Detects ace-api-v1
    (task_id + result) and ace-gui-v1 (flat) formats."""
    if "task_id" not in raw or "result" not in raw:
        return raw  # ace-gui-v1: already flat
    result = raw.get("result") or {}
    metas = result.get("metas") or {}
    lyrics = raw.get("lyrics") or result.get("lyrics") or metas.get("lyrics")
    caption = raw.get("prompt") or result.get("prompt") or metas.get("prompt")
    seed_val = result.get("seed_value")
    seed = None
    if seed_val is not None:
        parts = str(seed_val).split(",")
        if parts:
            try:
                seed = int(parts[0].strip())
            except (ValueError, TypeError):
                pass
    return {
        "lyrics": lyrics,
        "caption": caption,
        "bpm": metas.get("bpm"),
        "keyscale": metas.get("keyscale"),
        "timesignature": metas.get("timesignature"),
        "duration": metas.get("duration"),
        "instrumental": False,
        "seed": seed,
        "lm_negative_prompt": None,
    }


def scan_music_dir():
    """Scan the music directory for audio files and their JSON metadata."""
    found = []
    if not MUSIC_DIR.exists():
        return found
    for filepath in MUSIC_DIR.rglob("*"):
        if filepath.suffix.lower() in AUDIO_EXTENSIONS:
            track_id = filepath.stem
            json_path = filepath.with_suffix(".json")
            meta = {}
            if json_path.exists():
                try:
                    with open(json_path) as f:
                        meta = json.load(f)
                    if isinstance(meta, dict):
                        meta = _normalize_metadata(meta)
                except (json.JSONDecodeError, OSError):
                    pass
                if not isinstance(meta, dict):
                    meta = {}

            lyrics = _str_field(meta, "lyrics", 4096)
            title_raw = parse_title_raw(lyrics)
            if title_raw is not None:
                title_raw = title_raw[:256]

            try:
                mtime = os.path.getmtime(filepath)
                file_modified = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            except OSError:
                file_modified = None

            found.append({
                "id": track_id,
                "path": str(filepath.relative_to(MUSIC_DIR)),
                "caption": _str_field(meta, "caption", 1024),
                "lyrics": lyrics,
                "title_raw": title_raw,
                "instrumental": bool(meta.get("instrumental", False)),
                "bpm": _int_field(meta, "bpm"),
                "keyscale": _str_field(meta, "keyscale", 32),
                "timesignature": _str_field(meta, "timesignature", 32),
                "duration": _int_field(meta, "duration"),
                "duration_output": get_audio_duration(filepath),
                "file_modified": file_modified,
                "seed": _int_field(meta, "seed"),
                "lm_negative_prompt": _str_field(meta, "lm_negative_prompt", 512),
            })
    found.sort(key=lambda t: t["id"])
    return found
