from flask import Blueprint, redirect, render_template, url_for

from traxbase.db import get_all_tracks, rebuild_tracks
from traxbase.scanner import scan_music_dir

main = Blueprint("main", __name__)


@main.route("/")
def index():
    tracks = get_all_tracks()
    return render_template("index.html", tracks=tracks)


@main.route("/update")
def update():
    tracks = scan_music_dir()
    rebuild_tracks(tracks)
    return redirect(url_for("main.index"))
