"""The compatibility adapter persists pairs inside the caller's transaction.

The independent domain supports multi-line validation. The v0.3 schema and
read model still persist pairs only; full ledger persistence is future work.
"""
from .domain import JournalEntry
from ...core.values import uid

def record_pair(db, owner, student_id, event_id, event_type, description,
                debit_account, credit_account, amount, created_at):
    JournalEntry.pair(debit_account, credit_account, amount)
    db.execute(
        'INSERT INTO journals VALUES(?,?,?,?,?,?,?,?,?,?)',
        (uid(), owner, student_id, event_id, event_type, description,
         debit_account, credit_account, amount, created_at),
    )
