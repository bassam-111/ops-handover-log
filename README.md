# Ops Handover Log

A small Flask + SQLite web app for operations teams: record what happened
on a shift, what is still pending, and what is blocking work, so the next
person on duty can pick up without a handover meeting.

## What it does

- Lists handover notes, filterable by shift (Morning / Evening / Night)
  and status (Open / Handed over / Resolved)
- Add a note with date, shift, outgoing and incoming team members,
  pending items, blockers, and status
- Detail page per note, plus a summary page with counts by status and
  shift and the number of unresolved notes that have blockers
- Seeds itself on first run from `data/sample_handover_notes.csv`
  (3 sample notes) into a local SQLite database (`handover.db`)

## Skills used

Python, Flask, SQL (SQLite), HTML/CSS — all on the author's resume.
No claimed expertise beyond that.

## How to run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Then open http://127.0.0.1:5000 in a browser.

## How to test

```bash
.venv/bin/python test_app.py
```

## Sample output

Running the tests prints:

```
All tests passed: index, filter, summary, add, detail, validation, 404.
```

And the summary page with the sample data shows:

```
Total notes: 3 | Unresolved notes with blockers: 2
By status: Handed over: 1, Open: 2
By shift: Morning: 2, Evening: 1
```

## Files

- `app.py` — Flask app and SQLite logic
- `templates/` — index, add, detail, summary pages
- `static/style.css` — styling
- `data/sample_handover_notes.csv` — sample seed data
- `requirements.txt` — Flask only
- `test_app.py` — smoke tests (uses a throwaway test database)
