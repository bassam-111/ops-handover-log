"""Ops Handover Log — a small Flask + SQLite app for operations teams.

One page to record what happened on a shift, what is still pending, and
what is blocking work, so the next person on duty can pick up without a
meeting. Run with:  python app.py   then open http://127.0.0.1:5000
"""

import csv
import os
import sqlite3
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "handover.db"
SEED_CSV = BASE_DIR / "data" / "sample_handover_notes.csv"

app = Flask(__name__)

SHIFTS = ["Morning", "Evening", "Night"]
STATUSES = ["Open", "Handed over", "Resolved"]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the table and seed it from the sample CSV if it is empty."""
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT NOT NULL,
            shift TEXT NOT NULL,
            outgoing TEXT NOT NULL,
            incoming TEXT NOT NULL,
            pending_items TEXT NOT NULL DEFAULT '',
            blockers TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Open'
        )"""
    )
    count = db.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    if count == 0 and SEED_CSV.exists():
        with open(SEED_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                db.execute(
                    "INSERT INTO notes (log_date, shift, outgoing, incoming,"
                    " pending_items, blockers, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row["log_date"], row["shift"], row["outgoing"],
                     row["incoming"], row["pending_items"], row["blockers"],
                     row["status"]),
                )
    db.commit()


@app.before_request
def _ensure_db():
    # Also covers `flask run`, where the __main__ block never executes.
    if not getattr(app, "_db_ready", False):
        init_db()
        app._db_ready = True


@app.route("/")
def index():
    db = get_db()
    shift = request.args.get("shift", "")
    status = request.args.get("status", "")
    query = "SELECT * FROM notes WHERE 1=1"
    params = []
    if shift in SHIFTS:
        query += " AND shift = ?"
        params.append(shift)
    if status in STATUSES:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY log_date DESC, id DESC"
    notes = db.execute(query, params).fetchall()
    return render_template("index.html", notes=notes, shifts=SHIFTS,
                           statuses=STATUSES, shift=shift, status=status)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        log_date = request.form.get("log_date", "").strip()
        shift = request.form.get("shift", "")
        outgoing = request.form.get("outgoing", "").strip()
        incoming = request.form.get("incoming", "").strip()
        if not log_date or shift not in SHIFTS or not outgoing or not incoming:
            return render_template("add.html", shifts=SHIFTS, error=(
                "Date, shift, outgoing and incoming names are required.")), 400
        db = get_db()
        db.execute(
            "INSERT INTO notes (log_date, shift, outgoing, incoming,"
            " pending_items, blockers, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (log_date, shift, outgoing, incoming,
             request.form.get("pending_items", "").strip(),
             request.form.get("blockers", "").strip(),
             request.form.get("status", "Open")
             if request.form.get("status") in STATUSES else "Open"),
        )
        db.commit()
        return redirect(url_for("index"))
    return render_template("add.html", shifts=SHIFTS, error=None)


@app.route("/note/<int:note_id>")
def detail(note_id):
    note = get_db().execute(
        "SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if note is None:
        return "Handover note not found.", 404
    return render_template("detail.html", note=note)


@app.route("/summary")
def summary():
    db = get_db()
    by_status = db.execute(
        "SELECT status, COUNT(*) AS n FROM notes GROUP BY status").fetchall()
    by_shift = db.execute(
        "SELECT shift, COUNT(*) AS n FROM notes GROUP BY shift").fetchall()
    open_blockers = db.execute(
        "SELECT COUNT(*) FROM notes WHERE status != 'Resolved'"
        " AND TRIM(blockers) != ''").fetchone()[0]
    total = db.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    return render_template("summary.html", by_status=by_status,
                           by_shift=by_shift, open_blockers=open_blockers,
                           total=total)


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
