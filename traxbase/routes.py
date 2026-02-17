from flask import Blueprint, jsonify, render_template, request, send_from_directory

from traxbase.db import (
    ensure_userdata_schema,
    get_all_tracks,
    get_track_userdata,
    rebuild_tracks,
    save_track_userdata,
)
from traxbase.scanner import MUSIC_DIR, scan_music_dir

main = Blueprint("main", __name__)

ensure_userdata_schema()


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


@main.route("/track/<track_id>/userdata")
def track_userdata_get(track_id):
    data = get_track_userdata(track_id)
    return jsonify(data)


@main.route("/track/<track_id>/userdata", methods=["POST"])
def track_userdata_post(track_id):
    custom_title = (request.form.get("custom_title") or "").strip()[:256]
    description = (request.form.get("description") or "").strip()[:4096]
    save_track_userdata(track_id, custom_title, description)
    return jsonify({"ok": True})
