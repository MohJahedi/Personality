"""modules / attendance / service.py: extracted from the real v0.3 pilot."""
from __future__ import annotations

from ...core.errors import AppError
from ...core.values import now, uid, text, day
from ...core.policy import student_scope
from ..audit.service import record_audit


def execute(db, user, payload):
    owner, created_at, record_id = (user['owner'], now(), uid())
    if not any(p in user.get('permissions', ()) for p in ('attendance.write.all', 'attendance.write.assigned')):
        raise AppError('این نقش اجازهٔ ثبت حضور ندارد.', 403)
    student_id, status, selected_day = (text(payload, 'studentId', 'دانش\u200cآموز', 180), payload.get('status'), day(payload.get('day')))
    if status not in ('present', 'absent', 'late'):
        raise AppError('وضعیت معتبر نیست.')
    scope, args = student_scope(user, 'attendance.write', payload.get('yearId'))
    if not db.execute('SELECT s.id FROM students s WHERE s.owner=? AND s.id=?' + scope, [owner, student_id, *args]).fetchone():
        raise AppError('به این دانش\u200cآموز دسترسی ندارید.', 403)
    db.execute('INSERT INTO attendance VALUES(?,?,?,?,?,?) ON CONFLICT(owner,student_id,day)\n               DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at', (record_id, owner, student_id, selected_day, status, created_at))
    record_audit(db, user, 'ثبت حضور و غیاب', student_id)
    return {'ok': True, 'id': record_id}
