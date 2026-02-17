from flask import Blueprint, render_template, send_from_directory

from traxbase.db import get_all_tracks, rebuild_tracks
from traxbase.scanner import MUSIC_DIR, scan_music_dir

main = Blueprint("main", __name__)


@main.route("/")
def index():
    tracks = get_all_tracks()
    return render_template("index.html", tracks=tracks)


@main.route("/update")
def update():
    tracks = scan_music_dir()
    skipped = rebuild_tracks(tracks)
    imported_count = len(tracks) - len(skipped)
    return render_template(
        "update.html",
        imported_count=imported_count,
        skipped=skipped,
    )


@main.route("/audio/<path:filepath>")
def serve_audio(filepath):
    return send_from_directory(MUSIC_DIR, filepath)
