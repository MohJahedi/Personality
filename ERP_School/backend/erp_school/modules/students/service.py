"""Legacy student command; formal records use registry.py, not fixed sample classes."""
from __future__ import annotations

from ...core.errors import AppError
from ..identity.permissions import require
from ...core.values import now, uid, text
from ...core.policy import CLASSES
from ..audit.service import record_audit


def execute(db, user, payload):
    owner, created_at, record_id = (user['owner'], now(), uid())
    require(user, 'students.write')
    name, code, guardian = (text(payload, 'name', 'نام دانش\u200cآموز'), text(payload, 'code', 'کد پرونده', 30), text(payload, 'guardianName', 'نام ولی'))
    class_name = text(payload, 'className', 'کلاس')
    if class_name not in CLASSES:
        raise AppError('کلاس معتبر نیست.')
    phone = str(payload.get('guardianPhone', '')).strip()
    if len(phone) > 25:
        raise AppError('تماس ولی معتبر نیست.')
    db.execute('INSERT INTO students VALUES(?,?,?,?,?,?,?,?)', (record_id, owner, name, code, class_name, guardian, phone, created_at))
    record_audit(db, user, 'ثبت دانش\u200cآموز و ولی', record_id)
    return {'ok': True, 'id': record_id}
