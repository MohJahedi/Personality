"""Permission catalog and role resolution for one isolated school installation."""
import json

from ...core.errors import AppError

CATALOG = {
    'users.manage': 'مدیریت کاربران و انتصاب نقش',
    'roles.manage': 'تعریف و ویرایش نقش',
    'years.manage': 'مدیریت و کپی سال تحصیلی',
    'academics.manage': 'مدیریت پایه، درس، کلاس و برنامه',
    'academics.read': 'مشاهدهٔ ساختار آموزشی',
    'students.read.all': 'مشاهدهٔ همهٔ پرونده‌ها',
    'students.read.assigned': 'مشاهدهٔ کلاس‌های تخصیص‌یافته',
    'students.read.linked': 'مشاهدهٔ فرزندان مرتبط',
    'students.read.self': 'مشاهدهٔ پروندهٔ خود',
    'students.write': 'ثبت و انتساب پرونده',
    'finance.read.all': 'مشاهدهٔ مالی همهٔ دانش‌آموزان',
    'finance.read.linked': 'مشاهدهٔ مالی فرزندان مرتبط',
    'finance.read.self': 'مشاهدهٔ مالی خود',
    'finance.write': 'ثبت شهریه، دریافت و انتقال مانده',
    'attendance.read.all': 'مشاهدهٔ همهٔ حضورها',
    'attendance.read.assigned': 'مشاهدهٔ حضور کلاس‌های خود',
    'attendance.read.linked': 'مشاهدهٔ حضور فرزندان',
    'attendance.read.self': 'مشاهدهٔ حضور خود',
    'attendance.write.all': 'ثبت حضور همهٔ کلاس‌ها',
    'attendance.write.assigned': 'ثبت حضور کلاس‌های تخصیص‌یافته',
    'backup.export': 'دریافت پشتیبان کامل مدرسه',
}
BUILTINS = {
    'system_admin': ('ادمین سیستم', list(CATALOG)),
    'manager': ('مدیر', [p for p in CATALOG if p not in ('users.manage', 'roles.manage', 'backup.export')]),
    'accountant': ('حسابدار', ['academics.read', 'students.read.all', 'finance.read.all', 'finance.write']),
    'teacher': ('معلم', ['academics.read', 'students.read.assigned', 'attendance.read.assigned', 'attendance.write.assigned']),
    'parent': ('ولی', ['academics.read', 'students.read.linked', 'finance.read.linked', 'attendance.read.linked']),
    'student': ('دانش‌آموز', ['academics.read', 'students.read.self', 'finance.read.self', 'attendance.read.self']),
}


def require(user, permission):
    if permission not in user.get('permissions', ()):
        raise AppError('مجوز انجام این عملیات را ندارید.', 403)


def initialize_roles(db):
    for role_id, (name, permissions) in BUILTINS.items():
        db.execute('INSERT OR IGNORE INTO roles VALUES(?,?,?,1)',
                   (role_id, name, json.dumps(permissions)))
    for member in db.execute('SELECT * FROM memberships').fetchall():
        if db.execute('SELECT 1 FROM user_roles WHERE user_id=?', (member['user_id'],)).fetchone():
            continue
        role = 'system_admin' if member['user_id'] == member['owner'] else member['role']
        initialize_member(db, member['user_id'], role, member['class_name'], member['student_id'])


def initialize_member(db, user_id, role, class_name=None, student_id=None):
    if role not in BUILTINS:
        raise AppError('نقش اولیه معتبر نیست.')
    db.execute('INSERT INTO user_roles VALUES(?,?)', (user_id, role))
    db.execute('INSERT INTO user_profiles(user_id) VALUES(?)', (user_id,))
    db.execute('INSERT INTO user_security VALUES(?,0)', (user_id,))
    if class_name:
        db.execute('INSERT INTO user_class_scopes VALUES(?,?)', (user_id, class_name))
    if student_id:
        db.execute('INSERT INTO user_student_scopes VALUES(?,?)', (user_id, student_id))


def resolve_user(db, row):
    if row is None:
        return None
    user = dict(row)
    roles = list(db.execute('SELECT r.* FROM roles r JOIN user_roles ur ON ur.role_id=r.id WHERE ur.user_id=?', (user['id'],)))
    user['roles'] = [r['id'] for r in roles]
    user['permissions'] = sorted({p for r in roles for p in json.loads(r['permissions'])})
    user['student_ids'] = [r[0] for r in db.execute('SELECT student_id FROM user_student_scopes WHERE user_id=?', (user['id'],))]
    user['class_names'] = [r[0] for r in db.execute('SELECT class_name FROM user_class_scopes WHERE user_id=?', (user['id'],))]
    user['class_ids'] = [r[0] for r in db.execute('SELECT class_id FROM user_class_assignments WHERE user_id=?', (user['id'],))]
    flag = db.execute('SELECT must_change_password FROM user_security WHERE user_id=?', (user['id'],)).fetchone()
    user['must_change_password'] = bool(flag and flag[0])
    return user
