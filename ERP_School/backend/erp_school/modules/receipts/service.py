"""modules / receipts / service.py: extracted from the real v0.3 pilot."""
from __future__ import annotations
from ...core.errors import AppError
from ..identity.permissions import require
from ...core.values import now, uid, text, money
from ..audit.service import record_audit
from ..accounting.service import record_pair
from ...core.validation import optional_text

def execute(db, user, payload):
    owner, created_at, record_id = (user['owner'], now(), uid())
    require(user, 'finance.write')
    amount, event = (money(payload.get('amount', '')), text(payload, 'eventKey', 'شناسهٔ درخواست', 100))
    invoice = text(payload, 'invoiceId', 'شهریه', 180)
    reference = optional_text(payload, 'reference', 100)
    old = db.execute('SELECT * FROM receipts WHERE owner=? AND event_key=?', (owner, event)).fetchone()
    if old:
        if (old['invoice_id'], old['amount'], old['reference']) != (invoice, amount, reference):
            raise AppError('شناسهٔ درخواست قبلاً برای دریافت دیگری مصرف شده است.', 409)
        return {'ok': True, 'repeated': True}
    fee = db.execute('SELECT i.*,i.amount-COALESCE((SELECT SUM(r.amount) FROM receipts r WHERE r.owner=i.owner AND r.invoice_id=i.id),0) remaining\n                   FROM invoices i WHERE i.owner=? AND i.id=?', (owner, invoice)).fetchone()
    if not fee:
        raise AppError('شهریه یافت نشد.', 404)
    if amount > fee['remaining']:
        raise AppError('مبلغ دریافت از ماندهٔ شهریه بیشتر است.', 409)
    db.execute('INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)', (record_id, owner, invoice, amount, 'bank', reference, event, created_at))
    record_pair(db, owner, fee['student_id'], record_id, 'receipt', 'دریافت شهریه · ' + reference, '1101', '1301', amount, created_at)
    record_audit(db, user, 'ثبت دریافت و سند مرتبط', record_id)
    return {'ok': True, 'id': record_id}
