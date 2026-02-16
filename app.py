from flask import Flask, redirect, url_for

from db import get_all_tracks, rebuild_tracks
from scanner import scan_music_dir

app = Flask(__name__)


@app.route("/")
def index():
    tracks = get_all_tracks()
    html = "<h1>Traxbase</h1>"
    if not tracks:
        html += '<p>No tracks found. <a href="/update">Scan music directory</a></p>'
    else:
        html += f'<p>{len(tracks)} tracks. <a href="/update">Rescan</a></p>'
        html += "<table border='1' cellpadding='4'>"
        html += "<tr><th>Filename</th><th>Caption</th></tr>"
        for t in tracks:
            caption = t["caption"] or ""
            html += f"<tr><td>{t['id']}</td><td>{caption}</td></tr>"
        html += "</table>"
    return html


@app.route("/update")
def update():
    tracks = scan_music_dir()
    rebuild_tracks(tracks)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
