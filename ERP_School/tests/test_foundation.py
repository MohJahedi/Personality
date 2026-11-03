"""End-to-end application contracts through the real WSGI boundary and SQLite."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import School

PASSWORD = 'Temporary-test-only-12345'
NEW_PASSWORD = 'Changed-test-only-67890'


class ApplicationCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.app = School(self.directory.name)
        self.cookie = ''
        self.call('/auth', {'action': 'setup', 'username': 'admin', 'name': 'مدیر آزمون', 'password': PASSWORD})
        self.cookie = self.last_cookie

    def request(self, path, payload=None, cookie=None, app=None, **overrides):
        route, _, query = path.partition('?')
        raw = json.dumps(payload or {}, ensure_ascii=False).encode()
        environ = {'REQUEST_METHOD': 'GET' if payload is None else 'POST', 'PATH_INFO': route,
                   'QUERY_STRING': query, 'HTTP_HOST': 'localhost:8765', 'HTTP_ORIGIN': 'http://localhost:8765',
                   'REMOTE_ADDR': '127.0.0.1', 'HTTP_COOKIE': self.cookie if cookie is None else cookie,
                   'CONTENT_TYPE': 'application/json', 'CONTENT_LENGTH': str(len(raw)),
                   'HTTP_X_SCHOOL_ERP': '1', 'wsgi.input': io.BytesIO(raw)}
        environ.update(overrides)
        captured = {}
        def start(status, headers):
            captured.update(status=int(status.split()[0]), headers=dict(headers))
        data = b''.join((app or self.app)(environ, start))
        result = json.loads(data) if captured['headers'].get('Content-Type', '').startswith('application/json') else data
        self.last_cookie = captured['headers'].get('Set-Cookie', '').split(';')[0]
        return captured['status'], result

    def call(self, path, payload=None, expected=200, **kwargs):
        status, result = self.request('/api/v1' + path, payload, **kwargs)
        self.assertEqual(status, expected, (path, result))
        return result

    def year(self, title='۱۴۰۵–۱۴۰۶', start='2026-09-23', end='2027-09-22'):
        return self.call('/years', {'title': title, 'starts_on': start, 'ends_on': end})['id']

    def fixture(self):
        self.y1 = self.year()
        self.y2 = self.year('۱۴۰۶–۱۴۰۷', '2027-09-23', '2028-09-22')
        self.fiscal = self.call('/fiscal-years', {'title': 'مالی ۱۴۰۵', 'starts_on': '2026-03-21', 'ends_on': '2027-03-20'})['id']
        self.grade = self.call('/academics', {'kind': 'grade', 'name': 'پنجم', 'position': 5})['id']
        self.class_a = self.call('/academics', {'kind': 'class', 'name': 'پنجم الف', 'yearId': self.y1, 'gradeId': self.grade})['id']
        self.class_b = self.call('/academics', {'kind': 'class', 'name': 'پنجم ب', 'yearId': self.y1, 'gradeId': self.grade})['id']
        self.s1 = self.student('S1', 'دانش‌آموز اول')
        self.s2 = self.student('S2', 'دانش‌آموز دوم')

    def student(self, code, name, class_id=None):
        return self.call('/students', {'name': name, 'code': code, 'guardianName': 'ولی ' + code,
                                      'yearId': self.y1, 'classId': class_id or self.class_a})['id']

    def invoice(self, student=None, event='fee-one', amount='1000'):
        return self.call('/finance/invoices', {'studentId': student or self.s1, 'title': 'شهریهٔ آزمون',
            'amount': amount, 'eventKey': event, 'dueDate': '2026-12-01', 'yearId': self.y1,
            'fiscalYearId': self.fiscal, 'postedOn': '2026-11-03'})['id']

    def pay(self, invoice, amount='200', event='pay-one'):
        return self.call('/finance/receipts', {'invoiceId': invoice, 'amount': amount,
            'reference': 'آزمون', 'eventKey': event, 'fiscalYearId': self.fiscal, 'postedOn': '2026-11-03'})

    def create_user(self, name, roles, students=None, classes=None):
        user_id = self.call('/users', {'username': name, 'name': name, 'password': PASSWORD,
            'roles': roles, 'studentIds': students or [], 'classIds': classes or []})['id']
        self.call('/auth', {'action': 'login', 'username': name, 'password': PASSWORD}, cookie='')
        cookie = self.last_cookie
        self.call('/password', {'currentPassword': PASSWORD, 'newPassword': NEW_PASSWORD}, cookie=cookie)
        return user_id, self.last_cookie


class IdentityTests(ApplicationCase):
    def test_editing_own_roles_rotates_cookie_and_enforces_reduced_rights(self):
        self.create_user('secondadmin', ['system_admin'])
        admin = self.call('/context')['user']['id']
        old_cookie = self.cookie
        self.call('/users', {'id': admin, 'roles': ['manager']})
        self.cookie = self.last_cookie
        self.assertTrue(self.cookie)
        self.call('/profile', cookie=old_cookie, expected=401)
        self.assertEqual(self.call('/context')['user']['roles'], ['manager'])
        self.call('/users', expected=403)

    def test_setup_creates_system_admin_and_no_demo_records(self):
        context = self.call('/context')
        self.assertEqual(context['user']['roles'], ['system_admin'])
        self.assertEqual(self.call('/students')['students'], [])
        self.call('/auth', {'action': 'setup', 'username': 'another', 'name': 'دوم', 'password': PASSWORD}, expected=409)
        self.assertEqual(self.request('/api/school')[0], 404)

    def test_independent_installations_do_not_share_sessions(self):
        with tempfile.TemporaryDirectory() as other:
            app = School(other)
            context = self.call('/context', app=app)
            self.assertTrue(context['setupRequired'])
            self.assertIsNone(context['user'])

    def test_temporary_password_profile_and_session_revocation(self):
        uid = self.call('/users', {'username': 'newuser', 'name': 'جدید', 'password': PASSWORD, 'roles': ['teacher']})['id']
        self.call('/auth', {'action': 'login', 'username': 'newuser', 'password': PASSWORD}, cookie='')
        temporary_cookie = self.last_cookie
        self.call('/years', cookie=temporary_cookie, expected=403)
        self.call('/password', {'currentPassword': 'wrong', 'newPassword': NEW_PASSWORD}, cookie=temporary_cookie, expected=403)
        self.call('/password', {'currentPassword': PASSWORD, 'newPassword': NEW_PASSWORD}, cookie=temporary_cookie)
        active_cookie = self.last_cookie
        self.call('/profile', cookie=temporary_cookie, expected=401)
        self.call('/profile', {'name': 'نام تکمیل‌شده', 'first_name': 'نام', 'last_name': 'خانوادگی', 'phone': '09000000000', 'email': 'qa@example.test'}, cookie=active_cookie)
        self.assertEqual(self.call('/profile', cookie=active_cookie)['last_name'], 'خانوادگی')
        self.call('/users/reset-password', {'userId': uid, 'password': PASSWORD})
        self.call('/profile', cookie=active_cookie, expected=401)

    def test_last_admin_and_permission_delegation(self):
        admin = self.call('/context')['user']['id']
        self.call('/users', {'id': admin, 'roles': ['teacher']}, expected=409)
        role = self.call('/roles', {'name': 'فقط ساختار خواندنی', 'permissions': ['academics.read']})['id']
        _, cookie = self.create_user('reader', [role])
        self.call('/academics', cookie=cookie)
        self.call('/academics', {'kind': 'grade', 'name': 'غیرمجاز'}, cookie=cookie, expected=403)
        self.call('/roles', {'name': 'ادمین جعلی', 'permissions': ['users.manage']}, cookie=cookie, expected=403)
        self.assertEqual(self.call('/finance', cookie=cookie)['invoices'], [])

    def test_multiple_roles_and_multiple_children_are_scoped(self):
        self.fixture()
        self.invoice(self.s1, 'one')
        self.invoice(self.s2, 'two')
        third = self.student('S3', 'نام نامرتبط')
        self.invoice(third, 'three')
        _, cookie = self.create_user('family', ['parent'], [self.s1, self.s2])
        result = self.call('/balances?yearId=' + self.y1, cookie=cookie)
        self.assertEqual(result['total'], 20000)
        self.assertEqual({r['id'] for r in result['balances']}, {self.s1, self.s2})
        self.assertEqual(len(self.call('/finance', cookie=cookie)['invoices']), 2)
        self.assertEqual(self.call('/finance', cookie=cookie)['journals'], [])
        self.call('/users', {'username': 'badstudent', 'name': 'بد', 'password': PASSWORD, 'roles': ['student'], 'studentIds': [self.s1, self.s2]}, expected=400)

    def test_five_fonts_three_sizes_and_five_themes_are_real_and_persisted(self):
        from backend.erp_school.modules.preferences.service import FONTS, SIZES, THEMES
        self.assertGreaterEqual(len(FONTS), 5)
        self.assertGreaterEqual(len(SIZES), 3)
        self.assertGreaterEqual(len(THEMES), 5)
        for font in FONTS:
            data = {'font': font, 'size': 'large', 'theme': 'rose', 'accent': '#123456'}
            self.call('/preferences', data)
            self.assertEqual(self.call('/preferences'), data)
            asset = Path(__file__).resolve().parents[1] / 'public/fonts' / (font + '-regular.woff2')
            self.assertEqual(asset.read_bytes()[:4], b'wOF2')
        self.call('/preferences', {'font': 'invented', 'size': 'normal', 'theme': 'sky'}, expected=400)


class AcademicTests(ApplicationCase):
    def test_dates_fiscal_independence_and_closed_year(self):
        ident = self.year()
        self.year('بعدی', '2027-09-23', '2028-09-22')
        self.call('/years', {'title': 'هم‌پوشان', 'starts_on': '2027-01-01', 'ends_on': '2027-12-01'}, expected=409)
        fiscal = self.call('/fiscal-years', {'title': 'مالی مستقل', 'starts_on': '2026-03-21', 'ends_on': '2027-03-20'})
        self.assertTrue(fiscal['id'])
        self.call('/years', {'id': ident, 'title': 'اول', 'starts_on': '2026-09-23', 'ends_on': '2027-09-22', 'status': 'closed'})
        self.call('/years', {'id': ident, 'title': 'بازگشایی', 'starts_on': '2026-09-23', 'ends_on': '2027-09-22'}, expected=409)

    def test_selective_copy_is_atomic_idempotent_and_does_not_copy_finance_or_passwords(self):
        self.fixture()
        self.invoice()
        self.call('/academics', {'kind': 'teacher', 'name': 'معلم نمونه', 'yearId': self.y1})
        preview = self.call('/years/copy-preview?sourceId=' + self.y1 + '&targetId=' + self.y2)
        payload = {'sourceId': self.y1, 'targetId': self.y2, 'version': preview['version'], 'eventKey': 'copy-one', 'options': {'students': True, 'teachers': False, 'parents': True, 'classes': False}}
        self.call('/years/copy', payload)
        self.assertTrue(self.call('/years/copy', payload)['repeated'])
        catalog = self.call('/academics?yearId=' + self.y2)
        self.assertEqual(catalog['classes'], [])
        self.assertEqual(catalog['teachers'], [])
        with self.app.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM local_users').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0], 1)
            copied = list(db.execute('SELECT * FROM enrollments WHERE academic_year_id=?', (self.y2,)))
            self.assertEqual(len(copied), 2)
            self.assertTrue(all(row['class_id'] is None for row in copied))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM guardians').fetchone()[0], 2)

    def test_changed_copy_preview_is_rejected(self):
        self.fixture()
        preview = self.call('/years/copy-preview?sourceId=' + self.y1 + '&targetId=' + self.y2)
        self.student('S4', 'چهارم')
        self.call('/years/copy', {'sourceId': self.y1, 'targetId': self.y2, 'version': preview['version'], 'eventKey': 'stale', 'options': dict(students=True, teachers=True, parents=True, classes=True)}, expected=409)
        self.assertEqual(self.call('/academics?yearId=' + self.y2)['classes'], [])

    def test_daily_period_counts_teacher_collision_and_rollback(self):
        self.fixture()
        subject = self.call('/academics', {'kind': 'subject', 'name': 'ریاضی', 'gradeId': self.grade})['id']
        teacher = self.call('/academics', {'kind': 'teacher', 'name': 'معلم', 'yearId': self.y1})['id']
        day = {'yearId': self.y1, 'gradeId': self.grade, 'weekday': 0, 'periods': [{'starts_at': '08:00', 'ends_at': '08:45'}, {'starts_at': '09:00', 'ends_at': '09:45'}]}
        self.call('/periods', day)
        self.call('/periods', {**day, 'weekday': 1, 'periods': day['periods'][:1]})
        periods = self.call('/academics?yearId=' + self.y1)['periods']
        self.assertEqual([p['weekday'] for p in periods], [0, 0, 1])
        first, second = periods[0]['id'], periods[1]['id']
        self.call('/timetable', {'classId': self.class_a, 'periodId': first, 'subjectId': subject, 'teacherId': teacher})
        self.call('/timetable', {'classId': self.class_b, 'periodId': first, 'subjectId': subject, 'teacherId': teacher}, expected=409)
        self.call('/timetable', {'classId': self.class_b, 'periodId': second, 'subjectId': subject, 'teacherId': teacher})
        self.call('/periods', {**day, 'periods': []}, expected=409)
        self.call('/periods', {**day, 'periods': [{'starts_at': '09:00', 'ends_at': '08:00'}]}, expected=400)
        self.assertEqual(len(self.call('/timetable?yearId=' + self.y1)['timetable']), 2)


class FinancialTransitionTests(ApplicationCase):
    def test_database_itself_rejects_negative_amount_and_overpayment(self):
        self.fixture()
        invoice = self.invoice()
        owner = self.call('/context')['user']['id']
        with self.app.connection() as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('UPDATE invoices SET amount=-1 WHERE id=?', (invoice,))
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)', ('bad', owner, invoice, 10001, 'bank', 'QA', 'bad-event', '2026-11-03T00:00:00Z'))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0], 0)

    def test_failed_journal_rolls_back_invoice_and_year_link(self):
        self.fixture()
        with self.app.connection() as db:
            db.execute("CREATE TRIGGER reject_journal BEFORE INSERT ON journals BEGIN SELECT RAISE(ABORT,'synthetic journal failure'); END")
        self.call('/finance/invoices', {'studentId': self.s1, 'title': 'برگشت آزمون', 'amount': '1000', 'eventKey': 'rollback', 'dueDate': '2026-12-01', 'yearId': self.y1, 'fiscalYearId': self.fiscal, 'postedOn': '2026-11-03'}, expected=409)
        with self.app.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invoice_years').fetchone()[0], 0)

    def test_carry_preserves_original_claim_and_later_payments_reduce_next_year_balance(self):
        self.fixture()
        invoice = self.invoice()
        self.pay(invoice)
        preview = self.call('/years/carry-preview?sourceId=' + self.y1 + '&targetId=' + self.y2)
        payload = {'sourceId': self.y1, 'targetId': self.y2, 'version': preview['version'], 'eventKey': 'carry-one', 'studentIds': []}
        self.call('/years/carry', payload)
        self.assertTrue(self.call('/years/carry', payload)['repeated'])
        self.pay(invoice, '100', 'after-carry')
        result = self.call('/balances?yearId=' + self.y2)
        self.assertEqual(result['total'], 7000)
        self.assertEqual(result['openingSnapshot'], 8000)
        with self.app.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM journals').fetchone()[0], 3)

    def test_stale_carry_and_fiscal_date_reject_without_side_effects(self):
        self.fixture()
        invoice = self.invoice()
        preview = self.call('/years/carry-preview?sourceId=' + self.y1 + '&targetId=' + self.y2)
        self.pay(invoice)
        self.call('/years/carry', {'sourceId': self.y1, 'targetId': self.y2, 'version': preview['version'], 'eventKey': 'stale-carry'}, expected=409)
        self.call('/finance/invoices', {'studentId': self.s1, 'title': 'اشتباه', 'amount': '1000', 'eventKey': 'bad-period', 'dueDate': '2026-12-01', 'yearId': self.y1, 'fiscalYearId': self.fiscal, 'postedOn': '2028-01-01'}, expected=400)
        with self.app.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM carried_claims').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0], 1)

    def test_copy_conflict_rolls_back_all_changes(self):
        self.fixture()
        self.call('/academics', {'kind': 'class', 'name': 'پنجم ب', 'yearId': self.y2, 'gradeId': self.grade, 'capacity': 50})
        preview = self.call('/years/copy-preview?sourceId=' + self.y1 + '&targetId=' + self.y2)
        self.call('/years/copy', {'sourceId': self.y1, 'targetId': self.y2, 'version': preview['version'], 'eventKey': 'rollback-copy', 'options': dict(students=True, teachers=True, parents=True, classes=True)}, expected=409)
        self.assertEqual(len(self.call('/academics?yearId=' + self.y2)['classes']), 1)
        with self.app.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM enrollments WHERE academic_year_id=?', (self.y2,)).fetchone()[0], 0)


class DataLifecycleTests(ApplicationCase):
    def test_backup_can_boot_as_an_independent_restored_application(self):
        self.fixture()
        self.invoice()
        status, backup = self.request('/api/backup')
        self.assertEqual(status, 200)
        with tempfile.TemporaryDirectory() as restored:
            Path(restored, 'school.sqlite3').write_bytes(backup)
            app = School(restored)
            self.call('/auth', {'action': 'login', 'username': 'admin', 'password': PASSWORD}, app=app, cookie='')
            cookie = self.last_cookie
            self.assertEqual(len(self.call('/students?yearId=' + self.y1, app=app, cookie=cookie)['students']), 2)
            self.assertEqual(self.call('/balances?yearId=' + self.y1, app=app, cookie=cookie)['total'], 10000)
            with app.connection() as db:
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(list(db.execute('PRAGMA foreign_key_check')), [])

    def test_more_than_400_records_and_stable_teacher_class_scope(self):
        self.fixture()
        classes = []
        for index in range(5):
            classes.append(self.call('/academics', {'kind': 'class', 'name': 'گروه ' + str(index), 'yearId': self.y1, 'gradeId': self.grade, 'capacity': 100})['id'])
        for index in range(405):
            self.student('LOAD-' + str(index), 'پروندهٔ ساختگی ' + str(index), classes[index % 5])
        self.assertEqual(len(self.call('/students?yearId=' + self.y1)['students']), 407)
        _, teacher_cookie = self.create_user('scopedteacher', ['teacher'], classes=[classes[0]])
        scoped = self.call('/students?yearId=' + self.y1, cookie=teacher_cookie)['students']
        self.assertEqual(len(scoped), 81)
        self.assertTrue(all(student['class_id'] == classes[0] for student in scoped))
        # Renaming a class never transfers permission to a different class with its old name.
        self.call('/academics', {'kind': 'class', 'id': classes[0], 'name': 'نام تازه', 'yearId': self.y1, 'gradeId': self.grade, 'capacity': 100})
        self.assertEqual(len(self.call('/students?yearId=' + self.y1, cookie=teacher_cookie)['students']), 81)


class MigrationTests(unittest.TestCase):
    def test_v3_additive_migration_preserves_data_and_private_backup(self):
        from erp_school.modules.identity.passwords import password_hash
        from erp_school.modules.workspace.bootstrap import initialize_workspace
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / 'school.sqlite3'
            with sqlite3.connect(database_path) as db:
                schema = Path(__file__).resolve().parents[1] / 'backend/erp_school/infrastructure/migrations/003_pilot_baseline.sql'
                db.executescript(schema.read_text())
                initialize_workspace(db, 'legacy-owner', seed_demo=True)
                db.execute('INSERT INTO local_users VALUES(?,?,?,?,?)', ('legacy-owner', 'legacy', 'قدیمی', password_hash(PASSWORD), '2026-11-03T00:00:00Z'))
                db.execute('INSERT INTO memberships VALUES(?,?,?,?,?,?,?,?,?,?)', ('legacy-owner', 'legacy-owner', 'manager', 'قدیمی', 'legacy', 'active', None, None, None, '2026-11-03T00:00:00Z'))
            app = School(directory)
            with app.connection() as db:
                self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 4)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM students').fetchone()[0], 6)
                self.assertEqual(db.execute('SELECT role_id FROM user_roles').fetchone()[0], 'system_admin')
                self.assertEqual(list(db.execute('PRAGMA foreign_key_check')), [])
            backups = list(Path(directory).glob('school.pre-v4.*.sqlite3'))
            self.assertEqual(len(backups), 1)
            with sqlite3.connect(backups[0]) as db:
                self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 3)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM students').fetchone()[0], 6)


if __name__ == '__main__':
    unittest.main()
