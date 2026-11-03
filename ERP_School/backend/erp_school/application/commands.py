"""Application command dispatch: HTTP and modules share no routing code."""
from ..core.errors import AppError
from ..modules.students.service import execute as create_student
from ..modules.tuition.service import execute as create_invoice
from ..modules.receipts.service import execute as create_receipt
from ..modules.attendance.service import execute as mark_attendance

HANDLERS = {
    'student': create_student,
    'invoice': create_invoice,
    'receipt': create_receipt,
    'attendance': mark_attendance,
}

def execute_school_command(db, user, payload):
    if payload.get('role', user['role']) != user['role']:
        raise AppError('نقش درخواست با حساب شما تطابق ندارد.', 403)
    handler = HANDLERS.get(payload.get('action'))
    if handler is None:
        raise AppError('عملیات شناخته نشد.')
    return handler(db, user, payload)
