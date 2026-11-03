import { useState } from 'react';
import { post } from '../../shared/api';
import { useResource } from '../../shared/hooks';
import type { Catalog, Student, User } from '../../shared/types';
import { Field, FormCard, Panel, ResourceState, Table } from '../../shared/ui';
import { exportCsv, number } from '../../shared/format';
export default function StudentsPage({ user, yearId }: {
    user: User;
    yearId: string;
}) {
    const students = useResource<{
        students: Student[];
    }>('/students?yearId=' + yearId), catalog = useResource<Catalog>('/academics?yearId=' + yearId);
    const [query, setQuery] = useState(''), [classId, setClassId] = useState('');
    const canWrite = user.permissions.includes('students.write');
    const values = (students.data?.students || []).filter(s => (!classId || s.class_id === classId) && [s.name, s.code, s.guardian_name].join(' ').includes(query));
    return <><ResourceState {...students}/><ResourceState {...catalog}/><Panel title="پرونده‌های دانش‌آموزان و اولیا" subtitle={number(values.length) + ' پرونده در محدودهٔ دسترسی شما'}>
    <div className="filters"><Field label="جست‌وجوی پرونده"><input value={query} onChange={e => setQuery(e.target.value)} placeholder="نام، کد یا ولی…"/></Field><Field label="فیلتر کلاس"><select value={classId} onChange={e => setClassId(e.target.value)}><option value="">همهٔ پرونده‌ها</option>{catalog.data?.classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field><button onClick={() => exportCsv('students', [['کد', 'نام', 'کلاس', 'ولی'], ...values.map(s => [s.code, s.name, s.enrolled_class || '', s.guardian_name])])}>خروجی CSV</button></div>
    <Table head={['دانش‌آموز', 'کد پرونده', 'کلاس این سال', 'ولی', 'تماس']}>{values.map(s => <tr key={s.id}><td>{s.name}</td><td dir="ltr">{s.code}</td><td>{s.enrolled_class || 'ثبت‌نام یا تخصیص کلاس نشده'}</td><td>{s.guardian_name}</td><td dir="ltr">{s.guardian_phone || '—'}</td></tr>)}</Table>
  </Panel>{canWrite && <div className="two-columns"><FormCard title="ثبت دانش‌آموز و ولی" disabled={!yearId} onSave={async (values) => { await post('/students', { ...values, yearId }); await students.refresh(); }}>
    <Field label="نام دانش‌آموز"><input name="name" required maxLength={100}/></Field><Field label="کد پرونده"><input name="code" required maxLength={30} dir="ltr"/></Field><Field label="کلاس ثبت‌نام"><select name="classId" required defaultValue=""><option value="">انتخاب کنید…</option>{catalog.data?.classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field><Field label="نام ولی"><input name="guardianName" required maxLength={100}/></Field><Field label="تماس ولی"><input name="guardianPhone" type="tel" maxLength={25} dir="ltr"/></Field>
  </FormCard><FormCard title="تخصیص پروندهٔ موجود به کلاس این سال" disabled={!yearId} onSave={async (values) => { await post('/enrollments', { ...values, yearId }); await students.refresh(); }}>
    <Field label="پروندهٔ موجود"><select name="studentId" required defaultValue=""><option value="">انتخاب کنید…</option>{students.data?.students.map(s => <option key={s.id} value={s.id}>{s.name} · {s.code}</option>)}</select></Field><Field label="کلاس مقصد ثبت‌نام"><select name="classId" required defaultValue=""><option value="">انتخاب کنید…</option>{catalog.data?.classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
    <p className="muted">برای پرونده‌های کپی‌شده بدون کلاس، کلاس را اینجا مشخص کنید. ظرفیت کلاس در سرور کنترل می‌شود.</p>
  </FormCard></div>}</>;
}
