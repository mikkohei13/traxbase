import json
import re
from pathlib import Path

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
                except (json.JSONDecodeError, OSError):
                    pass

            caption = meta.get("caption")
            if caption is not None:
                caption = str(caption)[:1024]

            keyscale = meta.get("keyscale")
            if keyscale is not None:
                keyscale = str(keyscale)[:32]

            timesignature = meta.get("timesignature")
            if timesignature is not None:
                timesignature = str(timesignature)[:32]

            lm_negative_prompt = meta.get("lm_negative_prompt")
            if lm_negative_prompt is not None:
                lm_negative_prompt = str(lm_negative_prompt)[:512]

            bpm = meta.get("bpm")
            if bpm is not None:
                try:
                    bpm = int(bpm)
                except (ValueError, TypeError):
                    bpm = None

            duration = meta.get("duration")
            if duration is not None:
                try:
                    duration = int(duration)
                except (ValueError, TypeError):
                    duration = None

            seed = meta.get("seed")
            if seed is not None:
                try:
                    seed = int(seed)
                except (ValueError, TypeError):
                    seed = None

            lyrics = meta.get("lyrics")
            if lyrics is not None:
                lyrics = str(lyrics)[:4096]

            title_raw = parse_title_raw(lyrics)
            if title_raw is not None:
                title_raw = title_raw[:256]

            found.append({
                "id": track_id,
                "path": str(filepath.relative_to(MUSIC_DIR)),
                "caption": caption,
                "lyrics": lyrics,
                "title_raw": title_raw,
                "instrumental": bool(meta.get("instrumental", False)),
                "bpm": bpm,
                "keyscale": keyscale,
                "timesignature": timesignature,
                "duration": duration,
                "seed": seed,
                "lm_negative_prompt": lm_negative_prompt,
            })
    found.sort(key=lambda t: t["id"])
    return found
