"""Versioned API adapter. Every write is one database transaction."""
from urllib.parse import parse_qs

from ..core.errors import AppError
from ..core.values import text
from ..modules.identity import accounts
from ..modules.identity.permissions import require
from ..modules.preferences import service as preferences
from ..modules.academics import service as academics
from ..modules.students.registry import create_student, read_students
from ..modules.years import service as years
from ..modules.tuition.service import execute as create_invoice
from ..modules.receipts.service import execute as create_receipt
from ..modules.attendance.service import execute as mark_attendance
from ..core.policy import student_scope
from ..core.values import day
from .security import request_context, session_header
from ..application.queries import read_school_data
from ..modules.accounting.periods import validate_period, attach_period


def handle_api(app, path, method, payload, environ):
    query = parse_qs(environ.get('QUERY_STRING', ''))
    get = lambda key: query.get(key, [''])[0]
    if path == '/context' and method == 'GET':
        with app.database.snapshot() as db:
            user = app.identity.session_user(db, request_context(environ).session_token)
            if user and user['status'] != 'active':
                user = None
            return app.json_response({
                'setupRequired': not bool(db.execute('SELECT 1 FROM local_users LIMIT 1').fetchone()),
                'setupProtected': bool(app.setup_digest),
                'user': {key: user[key] for key in ('id', 'username', 'display_name', 'roles', 'permissions', 'must_change_password')} if user else None,
                'preferences': preferences.read(db, user) if user else dict(preferences.DEFAULT),
            })
    with (app.database.snapshot() if method == 'GET' else app.database.transaction()) as db:
        user = app.identity.active_user(db, request_context(environ).session_token, allow_password_change=path in ('/profile', '/password', '/preferences'))
        result = None
        if method == 'GET':
            if path == '/profile':
                result = accounts.own_profile(db, user)
            elif path == '/users':
                result = accounts.user_list(db, user)
            elif path == '/roles':
                result = accounts.list_roles(db, user)
            elif path == '/preferences':
                result = preferences.read(db, user)
            elif path == '/years':
                result = years.list_years(db)
            elif path == '/academics':
                result = academics.catalog(db, user, get('yearId'))
            elif path == '/students':
                result = read_students(db, user, get('yearId'))
            elif path == '/timetable':
                result = academics.timetable(db, user, get('yearId'))
            elif path == '/attendance':
                selected_day = day(get('day'))
                scope, parameters = student_scope(user, 'attendance.read', get('yearId'))
                rows = db.execute('SELECT a.student_id,a.status FROM attendance a JOIN students s ON s.id=a.student_id WHERE a.owner=? AND a.day=?' + scope, [user['owner'], selected_day, *parameters])
                result = {'students': read_students(db, user, get('yearId'))['students'], 'attendance': [dict(r) for r in rows]}
            elif path == '/years/copy-preview':
                result = years.copy_preview(db, user, get('sourceId'), get('targetId'))
            elif path == '/years/carry-preview':
                result = years.carry_preview(db, user, get('sourceId'), get('targetId'), query.get('studentId', []))
            elif path == '/balances':
                result = years.balances(db, user, get('yearId'))
            elif path == '/finance':
                data = read_school_data(db, user)
                result = {key: data[key] for key in ('students', 'invoices', 'receipts', 'journals')}
        elif method == 'POST':
            if path == '/profile':
                result = accounts.update_profile(db, user, payload)
            elif path == '/password':
                result, token = accounts.change_password(db, user, payload, app.identity)
                return app.json_response(result, extra=[session_header(token, app.secure_cookie)])
            elif path == '/users':
                result = accounts.save_user(db, user, payload)
                if result['id'] == user['id']:
                    token = app.identity.new_session(db, user['id']) if payload.get('status', 'active') == 'active' else None
                    return app.json_response(result, extra=[session_header(token, app.secure_cookie)])
            elif path == '/users/reset-password':
                result = accounts.reset_password(db, user, payload)
            elif path == '/roles':
                result = accounts.save_role(db, user, payload)
            elif path == '/preferences':
                result = preferences.save(db, user, payload)
            elif path in ('/years', '/fiscal-years'):
                result = years.save_year(db, user, payload, fiscal=path == '/fiscal-years')
            elif path == '/years/copy':
                result = years.copy_year(db, user, payload)
            elif path == '/years/carry':
                result = years.carry_debts(db, user, payload)
            elif path == '/academics':
                result = academics.save_master(db, user, payload)
            elif path == '/students':
                result = create_student(db, user, payload)
            elif path == '/enrollments':
                result = academics.enroll(db, user, payload)
            elif path == '/periods':
                result = academics.save_periods(db, user, payload)
            elif path == '/attendance':
                year_id = text(payload, 'yearId', 'سال تحصیلی', 180)
                year = academics.writable_year(db, year_id)
                selected_day = day(payload.get('day'))
                if not year['starts_on'] <= selected_day <= year['ends_on']:
                    raise AppError('تاریخ حضور خارج از سال تحصیلی انتخاب‌شده است.')
                student_id = text(payload, 'studentId', 'دانش‌آموز', 180)
                if not db.execute('SELECT 1 FROM enrollments WHERE academic_year_id=? AND student_id=?', (year_id, student_id)).fetchone():
                    raise AppError('دانش‌آموز در این سال ثبت‌نام نشده است.')
                result = mark_attendance(db, user, payload)
            elif path == '/timetable':
                result = academics.save_timetable(db, user, payload)
            elif path == '/timetable/remove':
                require(user, 'academics.manage')
                ident = text(payload, 'id', 'برنامه', 180)
                row = db.execute('SELECT c.academic_year_id FROM timetable t JOIN classes c ON c.id=t.class_id WHERE t.id=?', (ident,)).fetchone()
                if not row:
                    raise AppError('برنامه یافت نشد.', 404)
                academics.writable_year(db, row[0])
                db.execute('DELETE FROM timetable WHERE id=?', (ident,))
                result = {'ok': True}
            elif path == '/finance/invoices':
                period = validate_period(db, payload)
                year_id = text(payload, 'yearId', 'سال تحصیلی', 180)
                academics.writable_year(db, year_id)
                student_id = text(payload, 'studentId', 'دانش‌آموز', 180)
                if not db.execute('SELECT 1 FROM enrollments WHERE academic_year_id=? AND student_id=?', (year_id, student_id)).fetchone():
                    raise AppError('دانش‌آموز در این سال ثبت‌نام نشده است.')
                result = create_invoice(db, user, payload)
                invoice_id = result.get('id') or user['owner'] + ':invoice-event:' + payload['eventKey']
                old_year = db.execute('SELECT academic_year_id FROM invoice_years WHERE invoice_id=?', (invoice_id,)).fetchone()
                if old_year and old_year[0] != year_id:
                    raise AppError('شهریهٔ این شناسه به سال دیگری تعلق دارد.', 409)
                db.execute('INSERT OR IGNORE INTO invoice_years VALUES(?,?)', (invoice_id, year_id))
                journal = db.execute("SELECT id FROM journals WHERE event_id=? AND owner=? AND event_type='invoice'", (invoice_id, user['owner'])).fetchone()
                attach_period(db, journal[0], period)
            elif path == '/finance/receipts':
                period = validate_period(db, payload)
                result = create_receipt(db, user, payload)
                receipt = db.execute('SELECT id FROM receipts WHERE event_key=? AND owner=?', (payload['eventKey'], user['owner'])).fetchone()
                journal = db.execute("SELECT id FROM journals WHERE event_id=? AND owner=? AND event_type='receipt'", (receipt[0], user['owner'])).fetchone()
                attach_period(db, journal[0], period)
        if result is None:
            raise AppError('مسیر یا روش درخواست یافت نشد.', 404)
        return app.json_response(result)
