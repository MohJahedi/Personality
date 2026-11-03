"""Fiscal years constrain accounting dates independently of school enrollment."""
from ...core.errors import AppError
from ...core.values import day, text


def validate_period(db, payload):
    fiscal_id = text(payload, 'fiscalYearId', 'سال مالی', 180)
    posted_on = day(payload.get('postedOn'))
    period = db.execute('SELECT * FROM fiscal_years WHERE id=?', (fiscal_id,)).fetchone()
    if not period or period['status'] == 'closed':
        raise AppError('سال مالی معتبر و باز انتخاب کنید.', 409)
    if not period['starts_on'] <= posted_on <= period['ends_on']:
        raise AppError('تاریخ حسابداری خارج از سال مالی انتخاب‌شده است.')
    return fiscal_id, posted_on


def attach_period(db, journal_id, period):
    old = db.execute('SELECT fiscal_year_id,posted_on FROM journal_periods WHERE journal_id=?', (journal_id,)).fetchone()
    if old and tuple(old) != period:
        raise AppError('همین شناسهٔ درخواست قبلاً با سال مالی یا تاریخ دیگری ثبت شده است.', 409)
    db.execute('INSERT OR IGNORE INTO journal_periods VALUES(?,?,?)', (journal_id, *period))
