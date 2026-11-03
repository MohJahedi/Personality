"""Student records and the year-scoped student read model."""
from ...core.errors import AppError
from ...core.values import now, uid, text
from ...core.validation import optional_text
from ...core.policy import student_scope
from ..audit.service import record_audit
from ..identity.permissions import require
from ..academics.service import enroll


def create_student(db, user, payload):
    require(user, 'students.write')
    name, code, guardian_name = text(payload, 'name', 'نام دانش‌آموز'), text(payload, 'code', 'کد پرونده', 30), text(payload, 'guardianName', 'نام ولی')
    phone = optional_text(payload, 'guardianPhone', 25)
    student, guardian = uid(), uid()
    db.execute('INSERT INTO students VALUES(?,?,?,?,?,?,?,?)', (student, user['owner'], name, code, '', guardian_name, phone, now()))
    db.execute('INSERT INTO guardians VALUES(?,?,?)', (guardian, guardian_name, phone))
    db.execute('INSERT INTO student_guardians VALUES(?,?)', (student, guardian))
    enroll(db, user, {**payload, 'studentId': student})
    record_audit(db, user, 'ثبت پروندهٔ دانش‌آموز و ولی', student)
    return {'ok': True, 'id': student}


def read_students(db, user, year_id):
    scope, values = student_scope(user, year_id=year_id)
    rows = db.execute('SELECT s.*,e.class_id,e.grade_id,c.name enrolled_class FROM students s LEFT JOIN enrollments e ON e.student_id=s.id AND e.academic_year_id=? LEFT JOIN classes c ON c.id=e.class_id WHERE s.owner=?' + scope + ' ORDER BY s.code', [year_id, user['owner'], *values])
    return {'students': [dict(row) for row in rows]}
