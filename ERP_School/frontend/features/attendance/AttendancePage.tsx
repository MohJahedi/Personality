import { useState } from 'react';
import { post } from '../../shared/api';
import { useResource } from '../../shared/hooks';
import type { Student, User } from '../../shared/types';
import { Alert, Field, Panel, ResourceState, Table } from '../../shared/ui';
import { today } from '../../shared/format';
type AttendanceData = {
    students: Student[];
    attendance: {
        student_id: string;
        status: string;
    }[];
};
const names: Record<string, string> = { present: 'حاضر', absent: 'غایب', late: 'با تأخیر' };
export default function AttendancePage({ user, yearId }: {
    user: User;
    yearId: string;
}) {
    const [day, setDay] = useState(today()), [error, setError] = useState(''), [busy, setBusy] = useState(false);
    const resource = useResource<AttendanceData>('/attendance?yearId=' + yearId + '&day=' + day);
    const canWrite = user.permissions.some(p => p === 'attendance.write.all' || p === 'attendance.write.assigned');
    return <Panel title="حضور و غیاب روزانه" subtitle="فقط پرونده‌های مجاز در سال و کلاس تخصیص‌یافته نمایش داده می‌شوند."><ResourceState {...resource}/>{error && <Alert>{error}</Alert>}<Field label="روز حضور و غیاب"><input type="date" required value={day} onChange={e => setDay(e.target.value)}/></Field>
    <Table head={['دانش‌آموز', 'وضعیت', ...(canWrite ? ['ثبت وضعیت'] : [])]}>{resource.data?.students.filter(s => s.grade_id).map(student => <tr key={student.id}><td>{student.name}</td><td>{names[resource.data?.attendance.find(a => a.student_id === student.id)?.status || ''] || 'ثبت نشده'}</td>{canWrite && <td><div className="inline-fields">{Object.entries(names).map(([status, label]) => <button key={status} disabled={busy || !yearId || !day} onClick={async () => { setBusy(true); setError(''); try {
        await post('/attendance', { studentId: student.id, status, day, yearId });
        await resource.refresh();
    }
    catch (e) {
        setError(e instanceof Error ? e.message : 'ثبت حضور انجام نشد.');
    }
    finally {
        setBusy(false);
    } }}>{label}</button>)}</div></td>}</tr>)}</Table>
  </Panel>;
}
