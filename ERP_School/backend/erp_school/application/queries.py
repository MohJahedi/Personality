"""Read models join module data; writes remain in their owning modules."""
from ..core.policy import student_scope


def read_school_data(db, user):
    def rows(sql, values):
        return [dict(row) for row in db.execute(sql, values)]

    scope, parameters = student_scope(user)
    result = {
        'workspace': dict(db.execute('SELECT title,academic_year FROM workspaces WHERE owner=?', (user['owner'],)).fetchone()),
        'viewer': {'name': user['display_name'], 'email': user['username'], 'role': user['role'], 'className': user['class_name'], 'studentId': user['student_id']},
        'role': user['role'],
        'students': rows('SELECT s.* FROM students s WHERE s.owner=?' + scope + ' ORDER BY s.code', [user['owner'], *parameters]),
        'invoices': [], 'receipts': [], 'journals': [], 'attendance': [], 'audit': [],
    }
    scope, parameters = student_scope(user, 'finance.read')
    args = [user['owner'], *parameters]
    result['invoices'] = rows('SELECT i.*,s.name student_name,s.code student_code,iy.academic_year_id,COALESCE((SELECT SUM(r.amount) FROM receipts r WHERE r.owner=i.owner AND r.invoice_id=i.id),0) paid FROM invoices i JOIN students s ON s.id=i.student_id AND s.owner=i.owner LEFT JOIN invoice_years iy ON iy.invoice_id=i.id WHERE i.owner=?' + scope + ' ORDER BY i.created_at DESC', args)
    result['receipts'] = rows('SELECT r.*,s.name student_name,i.title invoice_title FROM receipts r JOIN invoices i ON i.id=r.invoice_id AND i.owner=r.owner JOIN students s ON s.id=i.student_id AND s.owner=i.owner WHERE r.owner=?' + scope + ' ORDER BY r.created_at DESC', args)
    scope, parameters = student_scope(user, 'attendance.read')
    result['attendance'] = rows('SELECT a.*,s.name student_name FROM attendance a JOIN students s ON s.id=a.student_id AND s.owner=a.owner WHERE a.owner=?' + scope + ' ORDER BY a.day DESC,s.code', [user['owner'], *parameters])
    if 'finance.read.all' in user['permissions']:
        result['journals'] = rows('SELECT j.*,s.name student_name,p.fiscal_year_id,p.posted_on FROM journals j JOIN students s ON s.id=j.student_id AND s.owner=j.owner LEFT JOIN journal_periods p ON p.journal_id=j.id WHERE j.owner=? ORDER BY j.created_at DESC,j.id', (user['owner'],))
    if 'years.manage' in user['permissions']:
        result['audit'] = rows('SELECT role,action,created_at FROM audit WHERE owner=? ORDER BY created_at DESC LIMIT 12', (user['owner'],))
    return result
