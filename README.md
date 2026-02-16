# Traxbase
Music Track Database based on Flask, uv, and SQLite. Aims to help me to keep track of my music tracks. Most business logic will be in Flask, and frontend has only minimal vanilla JavaScript.

## Setup

To run the app, use:

```bash
uv run flask --app traxbase run --reload
```

The app is available at http://127.0.0.1:5000

## Architecture

- **Backend:** Flask (`app.py`), serves HTML and a REST API
- **Database:** SQLite via Python's built-in `sqlite3`
- **Frontend:** Server-rendered Jinja2 templates with minimal vanilla JS
- **Dependencies:** Managed with uv (`pyproject.toml` / `uv.lock`)

## Database

The SQLite database (`traxbase.db`) is a derived cache — the filesystem (`./music`) is the source of truth. The `tracks` table is dropped and rebuilt from scratch on every scan (`/update`), so schema changes in code take effect immediately with no migrations needed.

## Upcoming features (keep these in mind but **don't develop unless asked**)

- Web UI that shows a table of music tracks (mp3, wav, flac) from the ./music directory and subdirectories
- Shows metadata read from JSON files associated with each music file
- Allows user to save more data about each track, e.g. title, genre keywords, longer notes
- Shows a player UI to play the tracks
- Shows distinct icon for each track
- Allows quick filtering of the tracks

## Development principles

- Keep it simple
- This is one-person app, so avoid premature optimization
- No authentication

