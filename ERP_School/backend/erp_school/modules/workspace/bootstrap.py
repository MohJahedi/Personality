"""modules / workspace / bootstrap.py: extracted from the real v0.3 pilot."""
from __future__ import annotations
from ...core.values import uid, now
from ...core.policy import CLASSES

def initialize_workspace(db, owner, seed_demo=False):
    created_at = now()
    db.execute('INSERT INTO workspaces VALUES(?,?,?,?,?)', (owner, 'مدرسهٔ آزمایشی', '۱۴۰۵–۱۴۰۶', owner + ':sample:1', created_at))
    if not seed_demo:
        return
    for i, (fee, paid) in enumerate(zip([40, 42, 39, 41, 44, 40], [12, 18, 0, 20, 10, 16]), 1):
        student_id, invoice_id = (f'{owner}:sample:{i}', f'{owner}:invoice:{i}')
        db.execute('INSERT INTO students VALUES(?,?,?,?,?,?,?,?)', (student_id, owner, f'دانش\u200cآموز نمونهٔ {i}', f'S-00{i}', CLASSES[0 if i <= 3 else 1], f'ولی نمونهٔ {i}', '', created_at))
        db.execute('INSERT INTO invoices VALUES(?,?,?,?,?,?,?)', (invoice_id, owner, student_id, 'شهریهٔ نمونهٔ سال تحصیلی', fee * 10000000, '2026-11-15', created_at))
        db.execute('INSERT INTO journals VALUES(?,?,?,?,?,?,?,?,?,?)', (uid(), owner, student_id, invoice_id, 'invoice', 'مطالبهٔ شهریهٔ نمونه', '1301', '2101', fee * 10000000, created_at))
        if paid:
            receipt = uid()
            db.execute('INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)', (receipt, owner, invoice_id, paid * 10000000, 'bank', 'دادهٔ ساختگی', f'seed-{i}', created_at))
            db.execute('INSERT INTO journals VALUES(?,?,?,?,?,?,?,?,?,?)', (uid(), owner, student_id, receipt, 'receipt', 'دریافت نمونهٔ شهریه', '1101', '1301', paid * 10000000, created_at))
