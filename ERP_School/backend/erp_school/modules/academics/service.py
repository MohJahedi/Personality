"""Academic master data, enrollment and collision-checked weekly timetables."""
from ...core.errors import AppError
from ...core.values import uid, text
from ...core.validation import clock, integer, optional_text
from ..audit.service import record_audit
from ..identity.permissions import require


def writable_year(db, year_id):
    row = db.execute('SELECT * FROM academic_years WHERE id=?', (year_id,)).fetchone()
    if not row:
        raise AppError('سال تحصیلی یافت نشد.', 404)
    if row['status'] == 'closed':
        raise AppError('سال تحصیلی بسته قابل تغییر نیست.', 409)
    return row


def catalog(db, user, year_id):
    if not any(p in user['permissions'] for p in ('academics.read', 'academics.manage')):
        raise AppError('مجوز مشاهدهٔ اطلاعات آموزشی را ندارید.', 403)
    def rows(sql, values=()):
        return [dict(row) for row in db.execute(sql, values)]
    result = {
        'grades': rows('SELECT * FROM grades ORDER BY position,name'),
        'subjects': rows('SELECT * FROM subjects ORDER BY name'),
        'gradeSubjects': rows('SELECT * FROM grade_subjects'),
        'classes': rows('SELECT * FROM classes WHERE academic_year_id=? ORDER BY name', (year_id,)),
        'teachers': rows('SELECT t.id,t.name FROM teachers t JOIN year_teachers y ON y.teacher_id=t.id WHERE y.academic_year_id=? ORDER BY t.name', (year_id,)),
        'periods': rows('SELECT * FROM day_periods WHERE academic_year_id=? ORDER BY weekday,number', (year_id,)),
    }
    return result


def save_master(db, user, payload):
    require(user, 'academics.manage')
    kind = payload.get('kind')
    name = text(payload, 'name', 'نام')
    ident = payload.get('id') or uid()
    if kind == 'grade':
        position = integer(payload.get('position', 1), 1, 20, 'ترتیب پایه')
        db.execute('INSERT INTO grades VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,position=excluded.position', (ident, name, position))
    elif kind == 'subject':
        existing = db.execute('SELECT id FROM subjects WHERE name=?', (name,)).fetchone()
        if not payload.get('id') and existing:
            ident = existing[0]
        db.execute('INSERT INTO subjects VALUES(?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name', (ident, name))
        grade = text(payload, 'gradeId', 'پایه', 180)
        db.execute('INSERT OR IGNORE INTO grade_subjects VALUES(?,?)', (grade, ident))
    elif kind == 'teacher':
        year = text(payload, 'yearId', 'سال تحصیلی', 180)
        writable_year(db, year)
        db.execute('INSERT INTO teachers VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,phone=excluded.phone', (ident, name, optional_text(payload, 'phone', 25)))
        db.execute('INSERT OR IGNORE INTO year_teachers VALUES(?,?)', (year, ident))
    elif kind == 'class':
        year, grade = text(payload, 'yearId', 'سال تحصیلی', 180), text(payload, 'gradeId', 'پایه', 180)
        writable_year(db, year)
        capacity = integer(payload.get('capacity', 30), 1, 100, 'ظرفیت کلاس')
        existing = db.execute('SELECT * FROM classes WHERE id=?', (ident,)).fetchone()
        if existing and (existing['academic_year_id'] != year or existing['grade_id'] != grade):
            raise AppError('سال و پایهٔ کلاس موجود تغییر نمی‌کند؛ کلاس تازه بسازید.', 409)
        count = db.execute('SELECT COUNT(*) FROM enrollments WHERE class_id=?', (ident,)).fetchone()[0]
        if capacity < count:
            raise AppError('ظرفیت از تعداد ثبت‌نام‌شده کمتر است.', 409)
        db.execute('INSERT INTO classes VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,capacity=excluded.capacity', (ident, year, grade, name, capacity))
    else:
        raise AppError('نوع اطلاعات آموزشی شناخته نشد.')
    record_audit(db, user, 'ذخیرهٔ اطلاعات آموزشی: ' + kind, ident)
    return {'ok': True, 'id': ident}


def enroll(db, user, payload):
    require(user, 'students.write')
    year, student, class_id = [text(payload, key, title, 180) for key, title in [('yearId', 'سال'), ('studentId', 'دانش‌آموز'), ('classId', 'کلاس')]]
    writable_year(db, year)
    if not db.execute('SELECT 1 FROM students WHERE id=? AND owner=?', (student, user['owner'])).fetchone():
        raise AppError('دانش‌آموز یافت نشد.', 404)
    classroom = db.execute('SELECT * FROM classes WHERE id=? AND academic_year_id=?', (class_id, year)).fetchone()
    if not classroom:
        raise AppError('کلاس این سال یافت نشد.', 404)
    count = db.execute('SELECT COUNT(*) FROM enrollments WHERE class_id=? AND student_id<>?', (class_id, student)).fetchone()[0]
    if count >= classroom['capacity']:
        raise AppError('ظرفیت کلاس تکمیل است.', 409)
    db.execute('INSERT INTO enrollments VALUES(?,?,?,?) ON CONFLICT(academic_year_id,student_id) DO UPDATE SET grade_id=excluded.grade_id,class_id=excluded.class_id', (year, student, classroom['grade_id'], class_id))
    # Kept only for compatibility with the old pilot. Formal queries use enrollment.
    active = db.execute("SELECT id FROM academic_years WHERE status='active'").fetchone()
    if active and active[0] == year:
        db.execute('UPDATE students SET class_name=? WHERE id=?', (classroom['name'], student))
    for guardian in db.execute('SELECT guardian_id FROM student_guardians WHERE student_id=?', (student,)):
        db.execute('INSERT OR IGNORE INTO year_guardians VALUES(?,?)', (year, guardian[0]))
    record_audit(db, user, 'تخصیص دانش‌آموز به کلاس سال تحصیلی', student)
    return {'ok': True}






def check_teacher_conflicts(db):
    conflict = db.execute('''SELECT 1 FROM timetable a JOIN day_periods pa ON pa.id=a.period_id
        JOIN timetable b ON b.teacher_id=a.teacher_id AND b.id>a.id
        JOIN day_periods pb ON pb.id=b.period_id
        WHERE a.teacher_id IS NOT NULL AND pa.academic_year_id=pb.academic_year_id
        AND pa.weekday=pb.weekday AND pa.starts_at<pb.ends_at AND pb.starts_at<pa.ends_at LIMIT 1''').fetchone()
    if conflict:
        raise AppError('زمان تدریس معلم با کلاس دیگری تداخل دارد.', 409)


def save_periods(db, user, payload):
    require(user, 'academics.manage')
    year, grade = text(payload, 'yearId', 'سال', 180), text(payload, 'gradeId', 'پایه', 180)
    writable_year(db, year)
    weekday = integer(payload.get('weekday'), 0, 6, 'روز هفته')
    periods = payload.get('periods')
    if not isinstance(periods, list) or len(periods) > 12 or any(not isinstance(row, dict) for row in periods):
        raise AppError('برای هر روز صفر تا ۱۲ زنگ تعریف کنید.')
    previous_end = ''
    checked = []
    for row in periods:
        start, end = clock(row.get('starts_at')), clock(row.get('ends_at'))
        if start >= end or start < previous_end:
            raise AppError('زمان زنگ‌ها باید مرتب، بدون هم‌پوشانی و دارای پایان بعد از شروع باشد.')
        checked.append((start, end))
        previous_end = end
    old = list(db.execute('SELECT * FROM day_periods WHERE academic_year_id=? AND grade_id=? AND weekday=? ORDER BY number', (year, grade, weekday)))
    for row in old[len(checked):]:
        if db.execute('SELECT 1 FROM timetable WHERE period_id=?', (row['id'],)).fetchone():
            raise AppError('ابتدا درس‌های زنگ حذف‌شونده را از برنامه بردارید.', 409)
        db.execute('DELETE FROM day_periods WHERE id=?', (row['id'],))
    for number, (start, end) in enumerate(checked, 1):
        record_id = old[number - 1]['id'] if number <= len(old) else uid()
        db.execute('INSERT INTO day_periods VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET starts_at=excluded.starts_at,ends_at=excluded.ends_at', (record_id, year, grade, weekday, number, start, end))
    check_teacher_conflicts(db)
    record_audit(db, user, 'تنظیم تعداد و زمان زنگ‌های روزانه', grade)
    return {'ok': True}


def save_timetable(db, user, payload):
    require(user, 'academics.manage')
    class_id, period_id, subject = [text(payload, key, title, 180) for key, title in [('classId', 'کلاس'), ('periodId', 'زنگ'), ('subjectId', 'درس')]]
    classroom = db.execute('SELECT * FROM classes WHERE id=?', (class_id,)).fetchone()
    period = db.execute('SELECT * FROM day_periods WHERE id=?', (period_id,)).fetchone()
    if not classroom or not period or (classroom['academic_year_id'], classroom['grade_id']) != (period['academic_year_id'], period['grade_id']):
        raise AppError('زنگ با سال و پایهٔ کلاس تطابق ندارد.')
    writable_year(db, classroom['academic_year_id'])
    if not db.execute('SELECT 1 FROM grade_subjects WHERE grade_id=? AND subject_id=?', (classroom['grade_id'], subject)).fetchone():
        raise AppError('درس برای این پایه تعریف نشده است.')
    teacher = payload.get('teacherId') or None
    if teacher and not db.execute('SELECT 1 FROM year_teachers WHERE academic_year_id=? AND teacher_id=?', (classroom['academic_year_id'], teacher)).fetchone():
        raise AppError('معلم در این سال تعریف نشده است.')
    old = db.execute('SELECT id FROM timetable WHERE class_id=? AND period_id=?', (class_id, period_id)).fetchone()
    ident = old[0] if old else uid()
    db.execute('INSERT INTO timetable VALUES(?,?,?,?,?,?,?) ON CONFLICT(class_id,period_id) DO UPDATE SET subject_id=excluded.subject_id,teacher_id=excluded.teacher_id', (ident, classroom['academic_year_id'], classroom['grade_id'], class_id, period_id, subject, teacher))
    check_teacher_conflicts(db)
    record_audit(db, user, 'ذخیرهٔ برنامهٔ هفتگی', ident)
    return {'ok': True, 'id': ident}


def timetable(db, user, year_id):
    result = []
    all_classes = 'students.read.all' in user['permissions'] or 'academics.manage' in user['permissions']
    for row in db.execute('''SELECT t.*,p.weekday,p.number,p.starts_at,p.ends_at,c.name class_name,s.name subject_name,coalesce(te.name,'') teacher_name
        FROM timetable t JOIN day_periods p ON p.id=t.period_id JOIN classes c ON c.id=t.class_id
        JOIN subjects s ON s.id=t.subject_id LEFT JOIN teachers te ON te.id=t.teacher_id
        WHERE c.academic_year_id=? ORDER BY c.name,p.weekday,p.number''', (year_id,)):
        linked = False
        if user['student_ids']:
            linked = bool(db.execute('SELECT 1 FROM enrollments WHERE class_id=? AND academic_year_id=? AND student_id IN (' + ','.join('?' for _ in user['student_ids']) + ')', [row['class_id'], year_id, *user['student_ids']]).fetchone())
        if all_classes or row['class_id'] in user.get('class_ids', []) or linked:
            result.append(dict(row))
    return {'timetable': result}
