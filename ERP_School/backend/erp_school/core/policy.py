"""Role and row scope policy. Never trust a role supplied by the client."""

CLASSES = ('پنجم الف', 'پنجم ب')
ROLES = ('manager', 'accountant', 'teacher', 'parent')

def student_scope(user, capability='students.read', year_id=None):
    permissions = set(user.get('permissions', ()))
    if capability + '.all' in permissions:
        return '', []
    clauses, values = [], []
    if year_id is not None and capability + '.assigned' in permissions and user.get('class_ids'):
        class_ids = user['class_ids']
        clauses.append('s.id IN (SELECT student_id FROM enrollments WHERE academic_year_id=? AND class_id IN (' + ','.join('?' for _ in class_ids) + '))')
        values.extend([year_id, *class_ids])
    elif year_id is None and capability + '.assigned' in permissions and user.get('class_names'):
        names = user['class_names']
        clauses.append('s.class_name IN (' + ','.join('?' for _ in names) + ')')
        values.extend(names)
    if (capability + '.linked' in permissions or capability + '.self' in permissions) and user.get('student_ids'):
        ids = user['student_ids']
        clauses.append('s.id IN (' + ','.join('?' for _ in ids) + ')')
        values.extend(ids)
    return (' AND (' + ' OR '.join(clauses) + ')', values) if clauses else (' AND 0', [])
