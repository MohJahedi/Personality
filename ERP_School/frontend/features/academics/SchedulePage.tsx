import { useEffect, useState } from 'react';
import { post } from '../../shared/api';
import { useResource } from '../../shared/hooks';
import type { Catalog, Timetable, User } from '../../shared/types';
import { Alert, Field, FormCard, Panel, ResourceState, Table } from '../../shared/ui';
import { number, weekdays } from '../../shared/format';
type Slot = {
    starts_at: string;
    ends_at: string;
};
function defaultSlot(index: number): Slot {
    const time = (minutes: number) => String(Math.floor(minutes / 60)).padStart(2, '0') + ':' + String(minutes % 60).padStart(2, '0');
    return { starts_at: time(480 + index * 50), ends_at: time(525 + index * 50) };
}
export default function SchedulePage({ user, yearId }: {
    user: User;
    yearId: string;
}) {
    const catalog = useResource<Catalog>('/academics?yearId=' + yearId), schedule = useResource<{
        timetable: Timetable[];
    }>('/timetable?yearId=' + yearId);
    const [grade, setGrade] = useState(''), [weekday, setWeekday] = useState(0), [slots, setSlots] = useState<Slot[]>([]), [classId, setClassId] = useState(''), [removeError, setRemoveError] = useState('');
    const canWrite = user.permissions.includes('academics.manage');
    useEffect(() => { setSlots((catalog.data?.periods || []).filter(p => p.grade_id === grade && p.weekday === weekday).map(p => ({ starts_at: p.starts_at, ends_at: p.ends_at }))); }, [catalog.data, grade, weekday]);
    const classroom = catalog.data?.classes.find(c => c.id === classId);
    async function refresh() { await catalog.refresh(); await schedule.refresh(); }
    return <><ResourceState {...catalog}/><ResourceState {...schedule}/>{canWrite && <div className="two-columns"><FormCard title="تعداد زنگ‌های روزانهٔ پایه" disabled={!yearId} reset={false} onSave={async () => { await post('/periods', { yearId, gradeId: grade, weekday, periods: slots }); await refresh(); }}>
    <Field label="پایه برای تنظیم زنگ‌ها"><select value={grade} onChange={e => setGrade(e.target.value)} required><option value="">انتخاب کنید…</option>{catalog.data?.grades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}</select></Field>
    <div className="form-grid"><Field label="روز هفته"><select value={weekday} onChange={e => setWeekday(Number(e.target.value))}>{weekdays.map((name, index) => <option key={name} value={index}>{name}</option>)}</select></Field><Field label="تعداد زنگ این روز"><input type="number" min={0} max={12} value={slots.length} onChange={e => { const count = Math.max(0, Math.min(12, Number(e.target.value))); setSlots(Array.from({ length: count }, (_, i) => slots[i] || defaultSlot(i))); }}/></Field></div>
    {slots.map((slot, index) => <div className="slot-row" key={index}><strong>زنگ {number(index + 1)}</strong><Field label={'شروع زنگ ' + number(index + 1)}><input type="time" required value={slot.starts_at} onChange={e => setSlots(slots.map((s, i) => i === index ? { ...s, starts_at: e.target.value } : s))}/></Field><Field label={'پایان زنگ ' + number(index + 1)}><input type="time" required value={slot.ends_at} onChange={e => setSlots(slots.map((s, i) => i === index ? { ...s, ends_at: e.target.value } : s))}/></Field></div>)}
    <p className="muted">صفر زنگ یعنی روز بدون کلاس. زنگ دارای برنامه را تا حذف درس آن نمی‌توان برداشت. هم‌پوشانی زمان‌ها در سرور کنترل می‌شود.</p>
  </FormCard><FormCard title="تخصیص درس و معلم به زنگ" disabled={!yearId} onSave={async (values) => { await post('/timetable', values); await schedule.refresh(); }}>
    <Field label="کلاس برنامه"><select name="classId" required value={classId} onChange={e => setClassId(e.target.value)}><option value="">انتخاب کنید…</option>{catalog.data?.classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
    <Field label="زنگ برنامه"><select name="periodId" key={'period-' + classId} required defaultValue=""><option value="">انتخاب کنید…</option>{catalog.data?.periods.filter(p => p.grade_id === classroom?.grade_id).map(p => <option key={p.id} value={p.id}>{weekdays[p.weekday]} · زنگ {number(p.number)} · {p.starts_at}–{p.ends_at}</option>)}</select></Field>
    <Field label="درس برنامه"><select name="subjectId" key={'subject-' + classId} required defaultValue=""><option value="">انتخاب کنید…</option>{catalog.data?.gradeSubjects.filter(link => link.grade_id === classroom?.grade_id).map(link => <option key={link.subject_id} value={link.subject_id}>{catalog.data?.subjects.find(s => s.id === link.subject_id)?.name}</option>)}</select></Field>
    <Field label="معلم برنامه"><select name="teacherId" defaultValue=""><option value="">فعلاً بدون معلم</option>{catalog.data?.teachers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select></Field>
    <p className="muted">ثبت دوبارهٔ همان کلاس و زنگ، تخصیص آن زنگ را ویرایش می‌کند. تداخل زمانی معلم با کلاس دیگر پذیرفته نمی‌شود.</p>
  </FormCard></div>}
  <Panel title="برنامهٔ هفتگی سال انتخاب‌شده">{removeError && <Alert>{removeError}</Alert>}<Table head={['کلاس', 'روز', 'زنگ', 'زمان', 'درس', 'معلم', ...(canWrite ? ['عملیات'] : [])]}>{schedule.data?.timetable.map(row => <tr key={row.id}><td>{row.class_name}</td><td>{weekdays[row.weekday]}</td><td>{number(row.number)}</td><td dir="ltr">{row.starts_at}–{row.ends_at}</td><td>{row.subject_name}</td><td>{row.teacher_name || 'تخصیص نیافته'}</td>{canWrite && <td><button onClick={async () => { setRemoveError(''); try {
        await post('/timetable/remove', { id: row.id });
        await schedule.refresh();
    }
    catch (e) {
        setRemoveError(e instanceof Error ? e.message : 'برداشتن برنامه انجام نشد.');
    } }}>برداشتن درس</button></td>}</tr>)}</Table></Panel>
  </>;
}
