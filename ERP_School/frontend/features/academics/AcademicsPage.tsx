import { post } from '../../shared/api';
import { useResource } from '../../shared/hooks';
import type { Catalog, User } from '../../shared/types';
import { Field, FormCard, Panel, ResourceState, Table, Empty } from '../../shared/ui';
import { number } from '../../shared/format';
export default function AcademicsPage({ user, yearId }: {
    user: User;
    yearId: string;
}) {
    const resource = useResource<Catalog>('/academics?yearId=' + yearId);
    const data = resource.data, canEdit = user.permissions.includes('academics.manage');
    async function save(kind: string, values: Record<string, string>) {
        await post('/academics', { ...values, kind, yearId, ...(kind === 'grade' ? { position: Number(values.position) } : {}), ...(kind === 'class' ? { capacity: Number(values.capacity) } : {}) });
        await resource.refresh();
    }
    return <><ResourceState {...resource}/>{!yearId && <Empty>ابتدا سال تحصیلی را در بخش سال‌ها تعریف کنید.</Empty>}
    {canEdit && <div className="two-columns"><FormCard title="تعریف پایهٔ تحصیلی" onSave={v => save('grade', v)}><Field label="نام پایه"><input name="name" required maxLength={100}/></Field><Field label="ترتیب پایه"><input name="position" type="number" required min={1} max={20} defaultValue={1}/></Field></FormCard>
    <FormCard title="تعریف درس برای پایه" onSave={v => save('subject', v)}><Field label="نام درس"><input name="name" required maxLength={100}/></Field><Field label="پایهٔ مربوط به درس"><select name="gradeId" required defaultValue=""><option value="">انتخاب کنید…</option>{data?.grades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}</select></Field></FormCard>
    <FormCard title="تعریف کلاس در سال انتخاب‌شده" disabled={!yearId} onSave={v => save('class', v)}><Field label="نام کلاس"><input name="name" required maxLength={100}/></Field><Field label="پایهٔ کلاس"><select name="gradeId" required defaultValue=""><option value="">انتخاب کنید…</option>{data?.grades.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}</select></Field><Field label="ظرفیت کلاس"><input name="capacity" type="number" required min={1} max={100} defaultValue={30}/></Field></FormCard>
    <FormCard title="تعریف معلم در سال انتخاب‌شده" disabled={!yearId} onSave={v => save('teacher', v)}><Field label="نام معلم"><input name="name" required maxLength={100}/></Field><Field label="شماره تماس معلم"><input name="phone" type="tel" maxLength={25} dir="ltr"/></Field></FormCard></div>}
    <Panel title="پایه‌ها و درس‌ها"><Table head={['پایه', 'ترتیب', 'دروس']}>{data?.grades.map(grade => <tr key={grade.id}><td>{grade.name}</td><td>{number(grade.position)}</td><td>{data.gradeSubjects.filter(link => link.grade_id === grade.id).map(link => data.subjects.find(s => s.id === link.subject_id)?.name).join('، ') || 'هنوز درسی تعریف نشده'}</td></tr>)}</Table></Panel>
    <Panel title="کلاس‌های این سال"><Table head={['کلاس', 'پایه', 'ظرفیت']}>{data?.classes.map(c => <tr key={c.id}><td>{c.name}</td><td>{data.grades.find(g => g.id === c.grade_id)?.name}</td><td>{number(c.capacity)}</td></tr>)}</Table></Panel>
    <Panel title="معلم‌های این سال"><div className="chips">{data?.teachers.map(t => <span key={t.id}>{t.name}</span>)}</div></Panel>
  </>;
}
