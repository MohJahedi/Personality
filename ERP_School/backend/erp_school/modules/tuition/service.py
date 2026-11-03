"""modules / tuition / service.py: extracted from the real v0.3 pilot."""
from __future__ import annotations
from ...core.errors import AppError
from ..identity.permissions import require
from ...core.values import now, uid, text, money, day
from ..audit.service import record_audit
from ..accounting.service import record_pair

def execute(db, user, payload):
    owner, created_at, record_id = (user['owner'], now(), uid())
    require(user, 'finance.write')
    amount, event = (money(payload.get('amount', '')), text(payload, 'eventKey', 'شناسهٔ درخواست', 100))
    student_id, title, due = (text(payload, 'studentId', 'دانش\u200cآموز', 180), text(payload, 'title', 'عنوان شهریه'), day(payload.get('dueDate')))
    record_id = owner + ':invoice-event:' + event
    old = db.execute('SELECT * FROM invoices WHERE owner=? AND id=?', (owner, record_id)).fetchone()
    if old:
        if (old['student_id'], old['title'], old['amount'], old['due_date']) != (student_id, title, amount, due):
            raise AppError('شناسهٔ درخواست قبلاً برای شهریهٔ دیگری مصرف شده است.', 409)
        return {'ok': True, 'repeated': True}
    if not db.execute('SELECT id FROM students WHERE id=? AND owner=?', (student_id, owner)).fetchone():
        raise AppError('دانش\u200cآموز یافت نشد.', 404)
    db.execute('INSERT INTO invoices VALUES(?,?,?,?,?,?,?)', (record_id, owner, student_id, title, amount, due, created_at))
    record_pair(db, owner, student_id, record_id, 'invoice', title, '1301', '2101', amount, created_at)
    record_audit(db, user, 'تعریف شهریه و سند مرتبط', record_id)
    return {'ok': True, 'id': record_id}
