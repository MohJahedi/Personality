"""User administration, role assignments, own profile and password changes."""
import json
import re

from ...core.errors import AppError
from ...core.values import now, uid, text
from ...core.validation import ids, optional_text
from ..audit.service import record_audit
from .passwords import credentials, password_hash, password_matches
from .permissions import CATALOG, require


def list_roles(db, user):
    if not any(p in user['permissions'] for p in ('users.manage', 'roles.manage')):
        raise AppError('مجوز مشاهدهٔ نقش‌ها را ندارید.', 403)
    return {'roles': [dict(row, permissions=json.loads(row['permissions'])) for row in db.execute('SELECT * FROM roles ORDER BY built_in DESC,name')], 'permissions': CATALOG}


def save_role(db, user, payload):
    require(user, 'roles.manage')
    permissions = ids(payload.get('permissions', []), maximum=len(CATALOG))
    if any(permission not in CATALOG or permission not in user['permissions'] for permission in permissions):
        raise AppError('مجوز ناشناخته یا بیشتر از اختیار خودتان قابل واگذاری نیست.', 403)
    name = text(payload, 'name', 'نام نقش', 80)
    role_id = payload.get('id')
    if role_id:
        role = db.execute('SELECT * FROM roles WHERE id=?', (role_id,)).fetchone()
        if not role:
            raise AppError('نقش یافت نشد.', 404)
        if role['built_in']:
            raise AppError('نقش اصلی تغییر نمی‌کند؛ نقش جدید بسازید.', 409)
        if not set(json.loads(role['permissions'])).issubset(user['permissions']):
            raise AppError('این نقش در محدودهٔ اختیار شما نیست.', 403)
        db.execute('UPDATE roles SET name=?,permissions=? WHERE id=?', (name, json.dumps(permissions), role_id))
    else:
        role_id = uid()
        db.execute('INSERT INTO roles VALUES(?,?,?,0)', (role_id, name, json.dumps(permissions)))
    record_audit(db, user, 'ذخیرهٔ نقش و مجوزها', role_id)
    return {'ok': True, 'id': role_id}


def user_list(db, user):
    require(user, 'users.manage')
    result = []
    for row in db.execute('SELECT u.id,u.username,u.display_name,m.status FROM local_users u JOIN memberships m ON m.user_id=u.id WHERE m.owner=? ORDER BY u.username', (user['owner'],)):
        result.append(dict(row, roles=[r[0] for r in db.execute('SELECT role_id FROM user_roles WHERE user_id=?', (row['id'],))], studentIds=[r[0] for r in db.execute('SELECT student_id FROM user_student_scopes WHERE user_id=?', (row['id'],))], classIds=[r[0] for r in db.execute('SELECT class_id FROM user_class_assignments WHERE user_id=?', (row['id'],))]))
    return {'users': result}


def validate_assignments(db, actor, payload):
    role_ids = ids(payload.get('roles', []), maximum=30)
    student_ids = ids(payload.get('studentIds', []))
    class_ids = ids(payload.get('classIds', []), maximum=100)
    if not role_ids:
        raise AppError('حداقل یک نقش انتخاب کنید.')
    for role_id in role_ids:
        role = db.execute('SELECT permissions FROM roles WHERE id=?', (role_id,)).fetchone()
        if not role or not set(json.loads(role[0])).issubset(actor['permissions']):
            raise AppError('این نقش در محدودهٔ اختیار شما نیست.', 403)
    if 'student' in role_ids and len(student_ids) != 1:
        raise AppError('برای نقش دانش‌آموز دقیقاً یک پروندهٔ خودِ دانش‌آموز انتخاب کنید.')
    for student_id in student_ids:
        if not db.execute('SELECT 1 FROM students WHERE id=? AND owner=?', (student_id, actor['owner'])).fetchone():
            raise AppError('پروندهٔ مرتبط یافت نشد.', 404)
    for class_id in class_ids:
        if not db.execute('SELECT 1 FROM classes WHERE id=?', (class_id,)).fetchone():
            raise AppError('کلاس تخصیص‌یافته یافت نشد.', 404)
    return role_ids, student_ids, class_ids


def _assign(db, user_id, role_ids, student_ids, class_ids):
    for table in ('user_roles', 'user_student_scopes', 'user_class_scopes', 'user_class_assignments'):
        db.execute(f'DELETE FROM {table} WHERE user_id=?', (user_id,))
    db.executemany('INSERT INTO user_roles VALUES(?,?)', [(user_id, role) for role in role_ids])
    db.executemany('INSERT INTO user_student_scopes VALUES(?,?)', [(user_id, sid) for sid in student_ids])
    db.executemany('INSERT INTO user_class_assignments VALUES(?,?)', [(user_id, class_id) for class_id in class_ids])
    # Only the old v0.3 presentation consumes this label. Permissions are authoritative.
    legacy = next((r for r in ('manager', 'accountant', 'teacher', 'parent', 'student') if r in role_ids), 'custom')
    if 'system_admin' in role_ids:
        legacy = 'manager'
    db.execute('UPDATE memberships SET role=?,class_name=?,student_id=? WHERE user_id=?', (legacy, None, student_ids[0] if student_ids else None, user_id))


def _protect_last_admin(db, target, roles, status):
    was_admin = db.execute("SELECT 1 FROM user_roles WHERE user_id=? AND role_id='system_admin'", (target,)).fetchone()
    if was_admin and (status != 'active' or 'system_admin' not in roles):
        others = db.execute("SELECT COUNT(*) FROM memberships m JOIN user_roles r ON r.user_id=m.user_id WHERE r.role_id='system_admin' AND m.status='active' AND m.user_id<>?", (target,)).fetchone()[0]
        if not others:
            raise AppError('آخرین ادمین فعال را نمی‌توان غیرفعال یا بدون نقش ادمین کرد.', 409)


def save_user(db, actor, payload):
    require(actor, 'users.manage')
    roles, students, classes = validate_assignments(db, actor, payload)
    target = payload.get('id')
    status = payload.get('status', 'active')
    if status not in ('active', 'disabled'):
        raise AppError('وضعیت کاربر معتبر نیست.')
    if target:
        if not db.execute('SELECT 1 FROM memberships WHERE user_id=? AND owner=?', (target, actor['owner'])).fetchone():
            raise AppError('کاربر یافت نشد.', 404)
        previous_permissions = {p for r in db.execute('SELECT r.permissions FROM roles r JOIN user_roles ur ON ur.role_id=r.id WHERE ur.user_id=?', (target,)) for p in json.loads(r[0])}
        if not previous_permissions.issubset(actor['permissions']):
            raise AppError('اختیار تغییر دسترسی این حساب را ندارید.', 403)
        _protect_last_admin(db, target, roles, status)
        db.execute('UPDATE memberships SET status=? WHERE user_id=?', (status, target))
        db.execute('DELETE FROM local_sessions WHERE user_id=?', (target,))
    else:
        username, password = credentials(payload)
        name = text(payload, 'name', 'نام نمایشی')
        target = uid()
        db.execute('INSERT INTO local_users VALUES(?,?,?,?,?)', (target, username, name, password_hash(password), now()))
        db.execute('INSERT INTO memberships VALUES(?,?,?,?,?,?,?,?,?,?)', (target, actor['owner'], 'custom', name, username, status, None, None, None, now()))
        db.execute('INSERT INTO user_profiles(user_id) VALUES(?)', (target,))
        db.execute('INSERT INTO user_security VALUES(?,1)', (target,))
    _assign(db, target, roles, students, classes)
    record_audit(db, actor, 'ذخیرهٔ کاربر و نقش‌ها', target)
    return {'ok': True, 'id': target}


def own_profile(db, user):
    return dict(db.execute('SELECT first_name,last_name,phone,email FROM user_profiles WHERE user_id=?', (user['id'],)).fetchone(), name=user['display_name'], username=user['username'])


def update_profile(db, user, payload):
    name = text(payload, 'name', 'نام نمایشی')
    first, last, phone, email = [optional_text(payload, key, limit) for key, limit in [('first_name', 80), ('last_name', 80), ('phone', 25), ('email', 160)]]
    if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise AppError('رایانامه معتبر نیست.')
    db.execute('UPDATE user_profiles SET first_name=?,last_name=?,phone=?,email=? WHERE user_id=?', (first, last, phone, email, user['id']))
    db.execute('UPDATE local_users SET display_name=? WHERE id=?', (name, user['id']))
    db.execute('UPDATE memberships SET display_name=? WHERE user_id=?', (name, user['id']))
    record_audit(db, user, 'تکمیل مشخصات فردی', user['id'])
    return {'ok': True}


def change_password(db, user, payload, identity):
    current = db.execute('SELECT password_hash FROM local_users WHERE id=?', (user['id'],)).fetchone()[0]
    if not password_matches(str(payload.get('currentPassword', '')), current):
        raise AppError('گذرواژهٔ فعلی صحیح نیست.', 403)
    _, password = credentials({'username': user['username'], 'password': payload.get('newPassword')})
    if password_matches(password, current):
        raise AppError('گذرواژهٔ جدید باید متفاوت باشد.')
    db.execute('UPDATE local_users SET password_hash=? WHERE id=?', (password_hash(password), user['id']))
    db.execute('UPDATE user_security SET must_change_password=0 WHERE user_id=?', (user['id'],))
    db.execute('DELETE FROM local_sessions WHERE user_id=?', (user['id'],))
    record_audit(db, user, 'تغییر گذرواژه و ابطال نشست‌ها', user['id'])
    return {'ok': True}, identity.new_session(db, user['id'])


def reset_password(db, actor, payload):
    require(actor, 'users.manage')
    target = text(payload, 'userId', 'کاربر', 180)
    if target == actor['id']:
        raise AppError('برای حساب خود از تغییر گذرواژه با گذرواژهٔ فعلی استفاده کنید.')
    row = db.execute('SELECT u.username FROM local_users u JOIN memberships m ON m.user_id=u.id WHERE u.id=? AND m.owner=?', (target, actor['owner'])).fetchone()
    if not row:
        raise AppError('کاربر یافت نشد.', 404)
    target_permissions = {p for r in db.execute('SELECT r.permissions FROM roles r JOIN user_roles ur ON ur.role_id=r.id WHERE ur.user_id=?', (target,)) for p in json.loads(r[0])}
    if not target_permissions.issubset(actor['permissions']):
        raise AppError('اختیار تغییر گذرواژهٔ این حساب را ندارید.', 403)
    _, password = credentials({'username': row[0], 'password': payload.get('password')})
    db.execute('UPDATE local_users SET password_hash=? WHERE id=?', (password_hash(password), target))
    db.execute('UPDATE user_security SET must_change_password=1 WHERE user_id=?', (target,))
    db.execute('DELETE FROM local_sessions WHERE user_id=?', (target,))
    record_audit(db, actor, 'بازنشانی گذرواژه و الزام تغییر', target)
    return {'ok': True}
