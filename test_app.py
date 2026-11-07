"""Smoke tests for the Ops Handover Log (run: python test_app.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as app_module

# Use a throwaway DB so tests never touch the real handover.db.
app_module.DB_PATH = app_module.BASE_DIR / "test_handover.db"
if app_module.DB_PATH.exists():
    app_module.DB_PATH.unlink()

with app_module.app.app_context():
    app_module.init_db()

client = app_module.app.test_client()

r = client.get("/")
assert r.status_code == 200 and b"Ops Handover Log" in r.data, "index failed"
assert b"Ayesha" in r.data, "seed data missing from index"

r = client.get("/?shift=Morning")
assert r.status_code == 200 and b"Ayesha" in r.data, "shift filter failed"

r = client.get("/note/1")
assert r.status_code == 200 and b"Meridian" in r.data, "seed detail missing"

r = client.get("/summary")
assert r.status_code == 200 and b"Total notes: 3" in r.data, "summary failed"

r = client.post("/add", data={
    "log_date": "2026-10-30", "shift": "Night",
    "outgoing": "Sara", "incoming": "Bilal",
    "pending_items": "Test pending item", "blockers": "",
    "status": "Open",
}, follow_redirects=True)
assert r.status_code == 200 and b"Test pending item" not in r.data  # list shows blockers, not pending
assert b"Sara" in r.data and b"Bilal" in r.data, "added note missing from index"

r = client.get("/note/4")
assert r.status_code == 200 and b"Test pending item" in r.data, "detail page failed"

r = client.post("/add", data={"log_date": "", "shift": "Night",
                              "outgoing": "", "incoming": ""})
assert r.status_code == 400, "invalid add should be rejected"

r = client.get("/note/999")
assert r.status_code == 404, "missing note should 404"

app_module.DB_PATH.unlink()
print("All tests passed: index, filter, summary, add, detail, validation, 404.")
