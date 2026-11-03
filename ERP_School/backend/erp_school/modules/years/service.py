"""Independent academic/fiscal calendars and explicit, atomic year transitions.

A carry-over refers to the original receivable. It never creates another
invoice or journal. Later payments settle that same original receivable.
"""
import hashlib
import json

from ...core.errors import AppError
from ...core.values import now, uid, text, day
from ...core.validation import ids
from ..academics.service import writable_year
from ..audit.service import record_audit
from ..identity.permissions import require


def _hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode()).hexdigest()


def list_years(db):
    return {
        'academicYears': [dict(row) for row in db.execute('SELECT * FROM academic_years ORDER BY starts_on DESC')],
        'fiscalYears': [dict(row) for row in db.execute('SELECT * FROM fiscal_years ORDER BY starts_on DESC')],
    }


def save_year(db, user, payload, fiscal=False):
    require(user, 'finance.write' if fiscal else 'years.manage')
    table = 'fiscal_years' if fiscal else 'academic_years'
    title = text(payload, 'title', 'عنوان سال', 80)
    start, end = day(payload.get('starts_on')), day(payload.get('ends_on'))
    status = payload.get('status', 'draft')
    if start > end or status not in ('draft', 'active', 'closed'):
        raise AppError('بازه یا وضعیت سال معتبر نیست.')
    ident = payload.get('id') or uid()
    previous = db.execute(f'SELECT * FROM {table} WHERE id=?', (ident,)).fetchone()
    if previous and previous['status'] == 'closed':
        raise AppError('سال بسته را نمی‌توان ویرایش یا دوباره فعال کرد.', 409)
    if db.execute(f'SELECT 1 FROM {table} WHERE id<>? AND starts_on<=? AND ends_on>=?', (ident, end, start)).fetchone():
        raise AppError('این بازه با سال دیگری از همین نوع هم‌پوشانی دارد.', 409)
    if status == 'active' and db.execute(f"SELECT 1 FROM {table} WHERE status='active' AND id<>?", (ident,)).fetchone():
        raise AppError('ابتدا وضعیت سال فعال قبلی را تغییر دهید.', 409)
    db.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,starts_on=excluded.starts_on,ends_on=excluded.ends_on,status=excluded.status', (ident, title, start, end, status))
    record_audit(db, user, 'ذخیرهٔ سال مالی' if fiscal else 'ذخیرهٔ سال تحصیلی', ident)
    return {'ok': True, 'id': ident}


def _year_pair(db, source, target):
    first = db.execute('SELECT * FROM academic_years WHERE id=?', (source,)).fetchone()
    second = writable_year(db, target)
    if not first:
        raise AppError('سال مبدأ یافت نشد.', 404)
    if source == target or second['starts_on'] <= first['ends_on']:
        raise AppError('سال مقصد باید بعد از پایان سال مبدأ آغاز شود.')
    return first, second


def _copy_source(db, source):
    queries = {
        'students': 'SELECT * FROM enrollments WHERE academic_year_id=? ORDER BY student_id',
        'teachers': 'SELECT * FROM year_teachers WHERE academic_year_id=? ORDER BY teacher_id',
        'parents': 'SELECT * FROM year_guardians WHERE academic_year_id=? ORDER BY guardian_id',
        'classes': 'SELECT * FROM classes WHERE academic_year_id=? ORDER BY id',
    }
    return {key: [dict(row) for row in db.execute(sql, (source,))] for key, sql in queries.items()}


def copy_preview(db, user, source, target):
    require(user, 'years.manage')
    _year_pair(db, source, target)
    data = _copy_source(db, source)
    return {'counts': {key: len(rows) for key, rows in data.items()}, 'version': _hash(data),
            'notes': ['اطلاعات پایهٔ اشخاص تکرار نمی‌شود؛ فقط ارتباط با سال مقصد ایجاد می‌شود.',
                      'گذرواژه، نشست، شهریه، سند و برنامهٔ هفتگی کپی نمی‌شوند.',
                      'ارتقای پایه خودکار نیست؛ پایهٔ فعلی حفظ می‌شود.',
                      'بدون کپی کلاس، ثبت‌نام منتقل‌شده تا تخصیص دستی بدون کلاس می‌ماند.']}


def _replay(db, user, payload, kind):
    event = text(payload, 'eventKey', 'شناسهٔ عملیات', 100)
    fingerprint = _hash({'user': user['id'], 'kind': kind, 'payload': payload})
    old = db.execute('SELECT * FROM completed_operations WHERE event_key=?', (event,)).fetchone()
    if old:
        if old['fingerprint'] != fingerprint:
            raise AppError('شناسهٔ عملیات قبلاً برای درخواست متفاوتی استفاده شده است.', 409)
        return event, fingerprint, {**json.loads(old['result']), 'repeated': True}
    return event, fingerprint, None


def _finish(db, event, fingerprint, result):
    db.execute('INSERT INTO completed_operations VALUES(?,?,?,?)', (event, fingerprint, json.dumps(result), now()))
    return result


def copy_year(db, user, payload):
    require(user, 'years.manage')
    event, fingerprint, replay = _replay(db, user, payload, 'copy-year')
    if replay:
        return replay
    source, target = text(payload, 'sourceId', 'سال مبدأ', 180), text(payload, 'targetId', 'سال مقصد', 180)
    preview = copy_preview(db, user, source, target)
    if payload.get('version') != preview['version']:
        raise AppError('اطلاعات مبدأ تغییر کرده است؛ پیش‌نمایش را دوباره بگیرید.', 409)
    options = payload.get('options')
    if not isinstance(options, dict) or set(options) != {'students', 'teachers', 'parents', 'classes'} or any(type(v) is not bool for v in options.values()) or not any(options.values()):
        raise AppError('حداقل یک گزینهٔ کپی را مشخص کنید.')
    data, class_map = _copy_source(db, source), {}
    copied = dict.fromkeys(options, 0)
    if options['classes']:
        for row in data['classes']:
            old = db.execute('SELECT * FROM classes WHERE academic_year_id=? AND name=?', (target, row['name'])).fetchone()
            if old and (old['grade_id'], old['capacity']) != (row['grade_id'], row['capacity']):
                raise AppError('کلاس همنام مقصد مشخصات متفاوت دارد؛ هیچ اطلاعاتی بازنویسی نشد.', 409)
            ident = old['id'] if old else uid()
            copied['classes'] += db.execute('INSERT OR IGNORE INTO classes VALUES(?,?,?,?,?)', (ident, target, row['grade_id'], row['name'], row['capacity'])).rowcount
            class_map[row['id']] = ident
    for option, table, column in [('teachers', 'year_teachers', 'teacher_id'), ('parents', 'year_guardians', 'guardian_id')]:
        if options[option]:
            for row in data[option]:
                copied[option] += db.execute(f'INSERT OR IGNORE INTO {table} VALUES(?,?)', (target, row[column])).rowcount
    if options['students']:
        for row in data['students']:
            class_id = class_map.get(row['class_id'])
            old = db.execute('SELECT * FROM enrollments WHERE academic_year_id=? AND student_id=?', (target, row['student_id'])).fetchone()
            if old:
                if (old['grade_id'], old['class_id']) != (row['grade_id'], class_id):
                    raise AppError('ثبت‌نام متفاوتی برای دانش‌آموز در مقصد وجود دارد؛ بازنویسی انجام نشد.', 409)
                continue
            if class_id:
                classroom = db.execute('SELECT capacity FROM classes WHERE id=?', (class_id,)).fetchone()
                count = db.execute('SELECT COUNT(*) FROM enrollments WHERE class_id=?', (class_id,)).fetchone()[0]
                if count >= classroom[0]:
                    raise AppError('ظرفیت کلاس مقصد برای کپی کافی نیست.', 409)
            db.execute('INSERT INTO enrollments VALUES(?,?,?,?)', (target, row['student_id'], row['grade_id'], class_id))
            copied['students'] += 1
    record_audit(db, user, 'کپی انتخابی ارتباطات سال تحصیلی', target)
    return _finish(db, event, fingerprint, {'ok': True, 'copied': copied})


def _claims(db, owner, source, target, student_ids):
    clauses, values = '', [source, source, owner]
    if student_ids:
        clauses = ' AND i.student_id IN (' + ','.join('?' for _ in student_ids) + ')'
        values.extend(student_ids)
    sql = '''SELECT i.id invoice_id,i.student_id,s.name student_name,i.title,i.amount,
        i.amount-COALESCE((SELECT SUM(r.amount) FROM receipts r WHERE r.invoice_id=i.id AND r.owner=i.owner),0) remaining
        FROM invoices i JOIN students s ON s.id=i.student_id AND s.owner=i.owner
        WHERE i.id IN (SELECT invoice_id FROM invoice_years WHERE academic_year_id=?
                       UNION SELECT invoice_id FROM carried_claims WHERE target_year_id=?) AND i.owner=?'''
    rows = []
    for row in db.execute(sql + clauses + ' ORDER BY i.id', values):
        if row['remaining'] > 0 and not db.execute('SELECT 1 FROM carried_claims WHERE target_year_id=? AND invoice_id=?', (target, row['invoice_id'])).fetchone():
            rows.append(dict(row))
    return rows


def carry_preview(db, user, source, target, student_ids=None):
    require(user, 'finance.write')
    require(user, 'finance.read.all')
    _year_pair(db, source, target)
    selected = ids(student_ids or [], 2000)
    claims = _claims(db, user['owner'], source, target, selected)
    return {'claims': claims, 'version': _hash(claims), 'amount': sum(row['remaining'] for row in claims),
            'studentCount': len({row['student_id'] for row in claims})}


def carry_debts(db, user, payload):
    require(user, 'finance.write')
    event, fingerprint, replay = _replay(db, user, payload, 'carry-debts')
    if replay:
        return replay
    source, target = text(payload, 'sourceId', 'سال مبدأ', 180), text(payload, 'targetId', 'سال مقصد', 180)
    preview = carry_preview(db, user, source, target, payload.get('studentIds', []))
    if payload.get('version') != preview['version']:
        raise AppError('مانده‌ها تغییر کرده‌اند؛ پیش‌نمایش تازه بگیرید.', 409)
    for row in preview['claims']:
        db.execute('INSERT INTO carried_claims VALUES(?,?,?,?,?)', (source, target, row['invoice_id'], row['remaining'], now()))
    record_audit(db, user, 'انتقال ارجاع ماندهٔ دانش‌آموزان بدون سند تکراری', target)
    return _finish(db, event, fingerprint, {'ok': True, 'amount': preview['amount'], 'claims': len(preview['claims'])})


def balances(db, user, year_id):
    from ...core.policy import student_scope
    scope, parameters = student_scope(user, 'finance.read')
    sql = '''SELECT s.id,s.name,s.code,i.id invoice_id,i.title,i.amount,
        COALESCE((SELECT SUM(r.amount) FROM receipts r WHERE r.invoice_id=i.id AND r.owner=i.owner),0) paid,
        coalesce(c.opening_amount,0) opening_amount
        FROM invoices i JOIN students s ON s.id=i.student_id AND s.owner=i.owner
        LEFT JOIN carried_claims c ON c.invoice_id=i.id AND c.target_year_id=?
        WHERE i.owner=? AND (i.id IN (SELECT invoice_id FROM invoice_years WHERE academic_year_id=?) OR c.invoice_id IS NOT NULL)'''
    rows = [dict(row, remaining=row['amount'] - row['paid']) for row in db.execute(sql + scope + ' ORDER BY s.code,i.created_at', [year_id, user['owner'], year_id, *parameters])]
    return {'balances': rows, 'total': sum(row['remaining'] for row in rows),
            'openingSnapshot': sum(row['opening_amount'] for row in rows)}
