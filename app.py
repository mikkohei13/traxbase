import json
from pathlib import Path

from flask import Flask, redirect, url_for

app = Flask(__name__)

MUSIC_DIR = Path(__file__).parent / "music"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac"}

tracks = []


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


@app.route("/")
def index():
    html = "<h1>Traxbase</h1>"
    if not tracks:
        html += '<p>No tracks loaded. <a href="/update">Scan music directory</a></p>'
    else:
        html += f'<p>{len(tracks)} tracks. <a href="/update">Rescan</a></p>'
        html += "<table border='1' cellpadding='4'>"
        html += "<tr><th>Filename</th><th>Caption</th><th>Title (DB)</th></tr>"
        for t in tracks:
            caption = t["caption"] or ""
            html += f"<tr><td>{t['id']}</td><td>{caption}</td><td></td></tr>"
        html += "</table>"
    return html


@app.route("/update")
def update():
    global tracks
    tracks = scan_music_dir()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
