import logging
import os

from flask import Blueprint, jsonify, render_template, request, send_from_directory

from traxbase.db import (
    ensure_userdata_schema,
    get_all_tracks,
    get_track_by_id,
    get_track_userdata,
    rebuild_tracks,
    save_track_userdata,
)
from traxbase.lyrics_to_image import generate_track_image
from traxbase.scanner import MUSIC_DIR, scan_music_dir

log = logging.getLogger(__name__)

main = Blueprint("main", __name__)

MUSIC_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "music_images")

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


@main.route("/music_image/<track_id>.png")
def serve_music_image(track_id):
    subdir = track_id[0]
    return send_from_directory(
        os.path.join(MUSIC_IMAGES_DIR, subdir), track_id + ".png"
    )


@main.route("/track/<track_id>/userdata")
def track_userdata_get(track_id):
    data = get_track_userdata(track_id)
    return jsonify(data)


@main.route("/track/<track_id>/userdata", methods=["POST"])
def track_userdata_post(track_id):
    custom_title = (request.form.get("custom_title") or "").strip()[:256]
    description = (request.form.get("description") or "").strip()[:4096]
    starred = request.form.get("starred") == "1"
    suno = request.form.get("suno") == "1"
    hide = request.form.get("hide") == "1"
    save_track_userdata(track_id, custom_title, description, starred, suno, hide)
    return jsonify({"ok": True})


@main.route("/track/<track_id>/generate_image", methods=["POST"])
def track_generate_image(track_id):
    subdir = track_id[0]
    dest_dir = os.path.join(MUSIC_IMAGES_DIR, subdir)
    base_path = os.path.join(dest_dir, track_id)

    if os.path.exists(base_path + ".png"):
        return jsonify({"ok": False, "error": "Image already exists"}), 409

    track = get_track_by_id(track_id)
    if not track:
        return jsonify({"ok": False, "error": "Track not found"}), 404

    ud = get_track_userdata(track_id)
    title = ud.get("custom_title") or track.get("title_raw") or "Album cover art illustration"
    style = track.get("caption") or ""
    lyrics = track.get("lyrics") or ""
    description = ud.get("description") or ""

    try:
        os.makedirs(dest_dir, exist_ok=True)
        generate_track_image(title, style, lyrics, base_path, description=description)
    except Exception:
        log.exception("Image generation failed for track %s", track_id)
        for suffix in (".png", "_original.png", "_prompts.json"):
            path = base_path + suffix
            if os.path.exists(path):
                os.remove(path)
        return jsonify({"ok": False, "error": "Image generation failed"}), 500

    return jsonify({"ok": True})
