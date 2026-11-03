"""http / application.py: extracted from the real v0.3 pilot."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import parse_qs
import json
import mimetypes
import sqlite3
import sys
import tempfile
import secrets
from ..core.errors import AppError
from ..application.commands import execute_school_command
from ..application.queries import read_school_data
from ..modules.identity.permissions import require
from .api import handle_api
from .security import request_context, session_header


class SchoolApplication:

    def __init__(self, database, identity, allowed_hosts, web_root):
        self.database = database
        self.identity = identity
        self.allowed_hosts = {host.lower() for host in allowed_hosts}
        self.web_root = Path(web_root)
        self.legacy_api = False
        self.secure_cookie = False

    @property
    def db_path(self):
        return self.database.db_path

    @property
    def setup_digest(self):
        return self.identity.setup_digest

    def connection(self):
        return self.database.connection()

    def transaction(self):
        return self.database.transaction()


    def json_response(self, obj, status=200, extra=None):
        return (status, [('Content-Type', 'application/json; charset=utf-8'), *(extra or [])], json.dumps(obj, ensure_ascii=False).encode('utf-8'))

    def handle(self, environ):
        method, path = (environ.get('REQUEST_METHOD', 'GET'), environ.get('PATH_INFO', '/'))
        versioned = path.startswith('/api/v1/')
        host = environ.get('HTTP_HOST', '').lower()
        if host not in self.allowed_hosts:
            raise AppError('نشانی میزبان مجاز نیست.', 403)
        if method not in ('GET', 'HEAD', 'POST'):
            raise AppError('روش درخواست مجاز نیست.', 405)
        payload = {}
        if method == 'POST':
            origin = environ.get('HTTP_ORIGIN')
            if origin and origin not in {scheme + '://' + h for h in self.allowed_hosts for scheme in ('http', 'https')}:
                raise AppError('مبدأ درخواست مجاز نیست.', 403)
            if environ.get('HTTP_SEC_FETCH_SITE') == 'cross-site' or environ.get('HTTP_X_SCHOOL_ERP') != '1' or (not environ.get('CONTENT_TYPE', '').startswith('application/json')):
                raise AppError('درخواست مجاز نیست.', 403)
            try:
                length = int(environ.get('CONTENT_LENGTH', '0'))
                if not 0 < length <= (64000 if versioned else 16000):
                    raise AppError('حجم درخواست معتبر نیست.', 413)
                payload = json.loads(environ['wsgi.input'].read(length))
                if not isinstance(payload, dict):
                    raise ValueError()
                for key, value in payload.items():
                    if (key == 'id' or key.endswith('Id')) and value is not None and (not isinstance(value, str) or len(value) > 180):
                        raise AppError('شناسهٔ درخواست معتبر نیست.')
            except (ValueError, UnicodeDecodeError):
                raise AppError('درخواست معتبر نیست.')
        if path in ('/health/live', '/health/ready') and method == 'GET':
            if path.endswith('ready'):
                with self.database.connection() as db:
                    if db.execute('PRAGMA user_version').fetchone()[0] != 4:
                        raise AppError('Database is not ready.', 503)
            return self.json_response({'status': 'ok', 'version': '0.4.0'})
        if path in ('/api/auth', '/api/v1/auth') and method == 'POST':
            result, token = self.identity.auth(payload.get('action'), payload, request_context(environ))
            return self.json_response(result, extra=[session_header(token, self.secure_cookie)])
        if versioned:
            return handle_api(self, path[len('/api/v1'):], method, payload, environ)
        if not self.legacy_api and (path == '/api/school' or (path == '/api/access' and (method == 'POST' or environ.get('QUERY_STRING')))):
            raise AppError('از API نسخهٔ رسمی استفاده کنید.', 404)
        if path == '/api/access' and method == 'GET':
            with self.database.connection() as db:
                user = self.identity.session_user(db, request_context(environ).session_token)
                if parse_qs(environ.get('QUERY_STRING', '')).get('manage') == ['1']:
                    user = self.identity.active_user(db, request_context(environ).session_token, True)
                    members = [dict(r) for r in db.execute('SELECT user_id,display_name,email,role,status,class_name,student_id,created_at FROM memberships WHERE owner=? ORDER BY created_at', (user['owner'],))]
                    invites = [dict(r) for r in db.execute('SELECT id,label,role,class_name,student_id,expires_at,revoked,used_by,created_at FROM invitations WHERE owner=? ORDER BY created_at DESC LIMIT 50', (user['owner'],))]
                    return self.json_response({'members': members, 'invitations': invites})
                setup = not db.execute('SELECT id FROM local_users LIMIT 1').fetchone()
                return self.json_response({'setupRequired': setup, 'setupProtected': bool(self.identity.setup_digest), 'user': {'name': user['display_name'], 'email': user['username']} if user else None, 'member': {'role': user['role'], 'status': user['status'], 'className': user['class_name'], 'studentId': user['student_id']} if user else None})
        if path == '/api/access' and method == 'POST':
            with self.database.transaction() as db:
                user = self.identity.active_user(db, request_context(environ).session_token, True)
                return self.json_response(self.identity.access_operation(db, user, payload))
        if path == '/api/school' and method in ('GET', 'POST'):
            with (self.database.snapshot() if method == 'GET' else self.database.transaction()) as db:
                user = self.identity.active_user(db, request_context(environ).session_token)
                requested = parse_qs(environ.get('QUERY_STRING', '')).get('role', [user['role']])[0]
                if requested != user['role']:
                    raise AppError('نقش درخواست با حساب شما تطابق ندارد.', 403)
                return self.json_response(read_school_data(db, user) if method == 'GET' else execute_school_command(db, user, payload))
        if path == '/api/backup' and method == 'GET':
            with self.database.connection() as db:
                user = self.identity.active_user(db, request_context(environ).session_token)
                require(user, 'backup.export')
                with tempfile.TemporaryDirectory() as temporary:
                    backup = Path(temporary) / 'backup.sqlite3'
                    dest = sqlite3.connect(backup)
                    try:
                        db.backup(dest)
                    finally:
                        dest.close()
                    data = backup.read_bytes()
            return (200, [('Content-Type', 'application/vnd.sqlite3'), ('Content-Disposition', f'attachment; filename="school-backup-{date.today().isoformat()}.sqlite3"')], data)
        if path == '/font.css' and method in ('GET', 'HEAD'):
            rules = []
            for filename, weight in [('IRANSans-Regular.woff2', '400'), ('IRANSans-Bold.woff2', '700')]:
                if (self.web_root / 'fonts' / filename).is_file():
                    rules.append('@font-face{font-family:IRANSans;src:url("/fonts/' + filename + '") format("woff2");font-weight:' + weight + ';font-style:normal;font-display:swap;}')
            return (200, [('Content-Type', 'text/css; charset=utf-8')], '\n'.join(rules).encode())
        if path.startswith('/api/'):
            raise AppError('مسیر یافت نشد.', 404)
        if method == 'POST':
            raise AppError('مسیر یافت نشد.', 404)
        if path == '/dashboard':
            with self.database.connection() as db:
                user = self.identity.session_user(db, request_context(environ).session_token)
                if not user or user['status'] != 'active':
                    return (302, [('Location', '/')], b'')
        if path not in ('/', '/login', '/dashboard', '/logout', '/favicon.svg') and (not path.startswith('/assets/')) and (not path.startswith('/fonts/')):
            raise AppError('مسیر یافت نشد.', 404)
        relative = 'index.html' if path in ('/', '/login', '/dashboard', '/logout') else path.lstrip('/')
        file = (self.web_root / relative).resolve()
        if not file.is_relative_to((self.web_root).resolve()) or not file.is_file():
            raise AppError('فایل رابط یافت نشد؛ پوشهٔ web را همراه برنامه نگه دارید.', 404)
        return (200, [('Content-Type', mimetypes.guess_type(file)[0] or 'application/octet-stream')], file.read_bytes())

    def __call__(self, environ, start_response):
        request_id = secrets.token_hex(12)
        try:
            status, headers, body = self.handle(environ)
        except AppError as error:
            status, headers, body = self.json_response({'error': str(error)}, error.status)
        except sqlite3.IntegrityError:
            status, headers, body = self.json_response({'error': 'شناسه تکراری است یا ارتباط داده معتبر نیست.'}, 409)
        except Exception:
            print('School request failed; request_id=' + request_id, file=sys.stderr)
            status, headers, body = self.json_response({'error': 'عملیات انجام نشد. دوباره تلاش کنید.'}, 500)
        base = [('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'), ('X-Frame-Options', 'SAMEORIGIN'), ('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'none'")]
        headers.extend(base)
        headers.append(('X-Request-ID', request_id))
        headers.append(('Content-Length', str(len(body))))
        reason = {200: 'OK', 302: 'Found', 400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden', 404: 'Not Found', 405: 'Method Not Allowed', 409: 'Conflict', 413: 'Payload Too Large', 429: 'Too Many Requests', 500: 'Internal Server Error'}.get(status, 'Error')
        start_response(f'{status} {reason}', headers)
        return [b'' if environ.get('REQUEST_METHOD') == 'HEAD' else body]
