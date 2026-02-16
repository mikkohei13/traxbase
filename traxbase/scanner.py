import json
from pathlib import Path

MUSIC_DIR = Path(__file__).resolve().parent.parent / "music"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac"}


def scan_music_dir():
    """Scan the music directory for audio files and their JSON metadata."""
    found = []
    if not MUSIC_DIR.exists():
        return found
    for filepath in MUSIC_DIR.rglob("*"):
        if filepath.suffix.lower() in AUDIO_EXTENSIONS:
            track_id = filepath.stem
            json_path = filepath.with_suffix(".json")
            caption = None
            if json_path.exists():
                try:
                    with open(json_path) as f:
                        metadata = json.load(f)
                    caption = metadata.get("caption")
                except (json.JSONDecodeError, OSError):
                    pass
            found.append({
                "id": track_id,
                "path": str(filepath.relative_to(MUSIC_DIR)),
                "caption": caption,
            })
    found.sort(key=lambda t: t["id"])
    return found
