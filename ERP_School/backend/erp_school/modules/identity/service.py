"""modules / identity / service.py: extracted from the real v0.3 pilot."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hmac
import re
import secrets
import time
from ...core.errors import AppError
from ...core.values import now, uid, text
from ...core.policy import CLASSES
from ..audit.service import record_audit
from .passwords import credentials, digest, password_hash, password_matches
from .permissions import initialize_member, resolve_user, require


class IdentityService:

    def __init__(self, database, initialize_workspace, setup_token=None):
        self.database = database
        self.initialize_workspace = initialize_workspace
        self.setup_digest = digest(setup_token) if setup_token else None
        self.dummy_hash = password_hash(secrets.token_urlsafe(24))


    def session_user(self, db, token):
        if not token or len(token) > 100:
            return None
        row = db.execute('SELECT u.id,u.username,u.display_name,m.owner,m.role,m.status,m.class_name,m.student_id\n          FROM local_sessions s JOIN local_users u ON u.id=s.user_id JOIN memberships m ON m.user_id=u.id\n          WHERE s.token_hash=? AND s.expires_at>?', (digest(token), int(time.time()))).fetchone()
        return resolve_user(db, row)

    def active_user(self, db, token, manager=False, allow_password_change=False):
        user = self.session_user(db, token)
        if not user:
            raise AppError('ورود به حساب لازم است.', 401)
        if user['status'] != 'active':
            raise AppError('دسترسی شما توسط مدیر غیرفعال شده است.', 403)
        if user['must_change_password'] and not allow_password_change:
            raise AppError('پیش از ادامه، گذرواژهٔ موقت خود را تغییر دهید.', 403)
        if manager:
            require(user, 'users.manage')
        return user

    def new_session(self, db, user_id):
        token = secrets.token_urlsafe(32)
        db.execute('DELETE FROM local_sessions WHERE expires_at<=?', (int(time.time()),))
        db.execute('INSERT INTO local_sessions VALUES(?,?,?)', (digest(token), user_id, int(time.time()) + 8 * 3600))
        return token

    def auth(self, action, payload, context):
        if action == 'logout':
            with self.database.transaction() as db:
                if context.session_token:
                    db.execute('DELETE FROM local_sessions WHERE token_hash=?', (digest(context.session_token),))
            return {'ok': True}, None
        if action not in ('login', 'setup', 'register'):
            raise AppError('عملیات شناخته نشد.')
        if action == 'setup' and self.setup_digest and (not hmac.compare_digest(digest(str(payload.get('setupToken', ''))), self.setup_digest)):
            raise AppError('کد راه\u200cاندازی سرور صحیح نیست.', 403)
        username, password = credentials(payload)
        key = digest(context.remote_address + ':' + username)
        ipkey = digest('ip:' + context.remote_address)
        with self.database.connection() as db:
            for k in (key, ipkey):
                limit = db.execute('SELECT * FROM login_limits WHERE key=?', (k,)).fetchone()
                if limit and limit['failures'] >= 10 and (limit['until_at'] > int(time.time())):
                    raise AppError('تلاش\u200cهای ناموفق زیاد است؛ ۱۵ دقیقه بعد دوباره تلاش کنید.', 429)
            existing = db.execute('SELECT * FROM local_users WHERE username=?', (username,)).fetchone()
        if action == 'login':
            good = password_matches(password, existing['password_hash'] if existing else self.dummy_hash)
            if not existing or not good:
                with self.database.transaction() as db:
                    for k in (key, ipkey):
                        db.execute('INSERT INTO login_limits VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET\n                          failures=CASE WHEN until_at<=? THEN 1 ELSE failures+1 END,\n                          until_at=CASE WHEN until_at<=? THEN excluded.until_at ELSE until_at END', (k, int(time.time()) + 900, int(time.time()), int(time.time())))
                raise AppError('نام کاربری یا گذرواژه صحیح نیست.', 401)
            with self.database.transaction() as db:
                member = db.execute('SELECT * FROM memberships WHERE user_id=?', (existing['id'],)).fetchone()
                if not member or member['status'] != 'active':
                    raise AppError('دسترسی این حساب غیرفعال شده است.', 403)
                db.execute('DELETE FROM login_limits WHERE key=?', (key,))
                header = self.new_session(db, existing['id'])
                record_audit(db, member, 'ورود به حساب محلی', existing['id'])
            return {'ok': True}, header
        name = text(payload, 'name', 'نام نمایشی')
        encoded = password_hash(password)
        with self.database.transaction() as db:
            if existing or db.execute('SELECT id FROM local_users WHERE username=?', (username,)).fetchone():
                raise AppError('این نام کاربری قبلاً ثبت شده است.', 409)
            user_id, created_at = (uid(), now())
            if action == 'setup':
                if db.execute('SELECT id FROM local_users LIMIT 1').fetchone():
                    raise AppError('مدیر اولیه قبلاً ساخته شده است.', 409)
                owner, role, class_name, student_id, invite_id = (user_id, 'manager', None, None, None)
                self.initialize_workspace(db, owner)
            else:
                token = text(payload, 'token', 'کد دعوت', 100)
                if not re.fullmatch('[a-fA-F0-9]{64}', token):
                    raise AppError('کد دعوت معتبر نیست.')
                invite = db.execute('SELECT * FROM invitations WHERE token_hash=? AND revoked=0 AND used_by IS NULL AND expires_at>?', (digest(token), created_at)).fetchone()
                if not invite:
                    raise AppError('کد دعوت مصرف\u200cشده، لغوشده یا منقضی است.', 409)
                owner, role, class_name, student_id, invite_id = [invite[k] for k in ('owner', 'role', 'class_name', 'student_id', 'id')]
            db.execute('INSERT INTO local_users VALUES(?,?,?,?,?)', (user_id, username, name, encoded, created_at))
            db.execute('INSERT INTO memberships VALUES(?,?,?,?,?,?,?,?,?,?)', (user_id, owner, role, name, username, 'active', class_name, student_id, invite_id, created_at))
            initialize_member(db, user_id, 'system_admin' if action == 'setup' else role, class_name, student_id)
            if invite_id:
                db.execute('UPDATE invitations SET used_by=? WHERE id=? AND used_by IS NULL', (user_id, invite_id))
            member = db.execute('SELECT * FROM memberships WHERE user_id=?', (user_id,)).fetchone()
            record_audit(db, member, 'ساخت حساب مدیر' if action == 'setup' else 'پیوستن کاربر دعوت\u200cشده', user_id)
            header = self.new_session(db, user_id)
        return {'ok': True}, header

    def access_operation(self, db, user, payload):
        created_at, owner = (now(), user['owner'])
        if payload.get('action') == 'invite':
            role, label = (payload.get('role'), text(payload, 'label', 'عنوان دعوت', 80))
            if role not in ('accountant', 'teacher', 'parent'):
                raise AppError('نقش دعوت معتبر نیست.')
            class_name = text(payload, 'className', 'کلاس') if role == 'teacher' else None
            student_id = text(payload, 'studentId', 'دانش\u200cآموز', 180) if role == 'parent' else None
            if class_name and class_name not in CLASSES:
                raise AppError('کلاس معتبر نیست.')
            if student_id and (not db.execute('SELECT id FROM students WHERE id=? AND owner=?', (student_id, owner)).fetchone()):
                raise AppError('دانش\u200cآموز یافت نشد.', 404)
            count = db.execute('SELECT COUNT(*) FROM invitations WHERE owner=? AND revoked=0 AND used_by IS NULL AND expires_at>?', (owner, created_at)).fetchone()[0]
            if count >= 10:
                raise AppError('حداکثر ۱۰ دعوت فعال مجاز است؛ دعوت قبلی را لغو کنید.', 409)
            token, record_id = (secrets.token_hex(32), uid())
            expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            db.execute('INSERT INTO invitations VALUES(?,?,?,?,?,?,?,?,?,?,?)', (record_id, owner, digest(token), role, label, class_name, student_id, expires, 0, None, created_at))
            record_audit(db, user, 'ایجاد دعوت کاربر', record_id)
            return {'ok': True, 'token': token, 'expiresAt': expires}
        if payload.get('action') == 'revokeInvite':
            record_id = text(payload, 'id', 'دعوت', 100)
            updated = db.execute('UPDATE invitations SET revoked=1 WHERE id=? AND owner=? AND used_by IS NULL', (record_id, owner)).rowcount
            if not updated:
                raise AppError('دعوت قابل لغو یافت نشد.', 404)
            record_audit(db, user, 'لغو دعوت کاربر', record_id)
            return {'ok': True}
        if payload.get('action') == 'memberStatus':
            target, status = (text(payload, 'userId', 'کاربر', 180), payload.get('status'))
            if status not in ('active', 'disabled'):
                raise AppError('وضعیت معتبر نیست.')
            if not db.execute("SELECT user_id FROM memberships WHERE owner=? AND user_id=? AND role<>'manager'", (owner, target)).fetchone():
                raise AppError('این کاربر قابل تغییر نیست.', 403)
            db.execute('UPDATE memberships SET status=? WHERE owner=? AND user_id=?', (status, owner, target))
            if status == 'disabled':
                db.execute('DELETE FROM local_sessions WHERE user_id=?', (target,))
            record_audit(db, user, 'فعال\u200cسازی دسترسی' if status == 'active' else 'غیرفعال\u200cسازی دسترسی', target)
            return {'ok': True}
        raise AppError('عملیات شناخته نشد.')
