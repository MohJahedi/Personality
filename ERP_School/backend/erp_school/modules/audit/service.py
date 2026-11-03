"""modules / audit / service.py: extracted from the real v0.3 pilot."""
from __future__ import annotations
from ...core.values import uid, now

def record_audit(db, user, action, target):
    db.execute('INSERT INTO audit VALUES(?,?,?,?,?,?)', (uid(), user['owner'], user['role'], action, target, now()))
