import { useState } from 'react';
import { get, post, runOperation } from '../../shared/api';
import type { User, Year, Years, Student } from '../../shared/types';
import { useResource } from '../../shared/hooks';
import { Field, FormCard, Panel, Table } from '../../shared/ui';
import { date, money, number, statuses } from '../../shared/format';
type CopyPreview = {
    counts: Record<string, number>;
    version: string;
    notes: string[];
};
type CarryPreview = {
    version: string;
    amount: number;
    studentCount: number;
    claims: {
        invoice_id: string;
        student_id: string;
        student_name: string;
        title: string;
        remaining: number;
    }[];
};
const optionNames: Record<string, string> = { students: 'دانش‌آموزان و ثبت‌نام‌ها', teachers: 'معلم‌ها', parents: 'اولیا', classes: 'کلاس‌ها' };
function YearForm({ fiscal, editing, onSave, onCancel }: {
    fiscal: boolean;
    editing: Year | null;
    onSave: () => Promise<void>;
    onCancel: () => void;
}) {
    return <FormCard key={editing?.id || String(fiscal)} title={(editing ? 'ویرایش ' : 'تعریف ') + (fiscal ? 'سال مالی' : 'سال تحصیلی')} note="تاریخ ورودی با تقویم مرورگر است؛ در فهرست به شمسی نمایش داده می‌شود." onSave={async (values) => { await post(fiscal ? '/fiscal-years' : '/years', { ...values, ...(editing ? { id: editing.id } : {}) }); onCancel(); await onSave(); }}>
    {editing && <button type="button" onClick={onCancel}>انصراف از ویرایش</button>}<Field label="عنوان سال"><input name="title" required maxLength={80} defaultValue={editing?.title || ''}/></Field>
    <div className="form-grid"><Field label="تاریخ شروع"><input name="starts_on" type="date" required defaultValue={editing?.starts_on}/></Field><Field label="تاریخ پایان"><input name="ends_on" type="date" required defaultValue={editing?.ends_on}/></Field></div>
    <Field label="وضعیت سال"><select name="status" defaultValue={editing?.status || 'draft'}><option value="draft">پیش‌نویس</option><option value="active">فعال</option><option value="closed">بسته؛ پس از ذخیره قابل بازگشایی نیست</option></select></Field>
  </FormCard>;
}
export default function YearsPage({ user, years, refresh }: {
    user: User;
    years: Years;
    refresh: () => Promise<void>;
}) {
    const [academicEdit, setAcademicEdit] = useState<Year | null>(null), [fiscalEdit, setFiscalEdit] = useState<Year | null>(null);
    const [source, setSource] = useState(''), [target, setTarget] = useState(''), [copy, setCopy] = useState<CopyPreview>(), [carry, setCarry] = useState<CarryPreview>();
    const [options, setOptions] = useState<Record<string, boolean>>({ students: false, teachers: false, parents: false, classes: false });
    const [studentIds, setStudentIds] = useState<string[]>([]), [reviewedCopy, setReviewedCopy] = useState(false), [reviewedCarry, setReviewedCarry] = useState(false);
    const sourceStudents = useResource<{
        students: Student[];
    }>(source && user.permissions.includes('students.read.all') ? '/students?yearId=' + source : null);
    const canYear = user.permissions.includes('years.manage'), canFinance = user.permissions.includes('finance.write');
    function invalidate() { setCopy(undefined); setCarry(undefined); setReviewedCopy(false); setReviewedCarry(false); }
    const selection = <div className="form-grid"><Field label="سال مبدأ"><select required value={source} onChange={e => { setSource(e.target.value); setStudentIds([]); invalidate(); }}><option value="">انتخاب کنید…</option>{years.academicYears.map(y => <option key={y.id} value={y.id}>{y.title}</option>)}</select></Field><Field label="سال مقصد"><select required value={target} onChange={e => { setTarget(e.target.value); invalidate(); }}><option value="">انتخاب کنید…</option>{years.academicYears.filter(y => y.status !== 'closed' && y.id !== source).map(y => <option key={y.id} value={y.id}>{y.title}</option>)}</select></Field></div>;
    function list(title: string, values: Year[], edit: (year: Year) => void, canEdit: boolean) { return <Panel title={title}><Table head={['عنوان', 'شروع', 'پایان', 'وضعیت', 'عملیات']}>{values.map(y => <tr key={y.id}><td>{y.title}</td><td>{date(y.starts_on)}</td><td>{date(y.ends_on)}</td><td><span className={'badge ' + y.status}>{statuses[y.status]}</span></td><td>{canEdit && y.status !== 'closed' && <button onClick={() => edit(y)}>ویرایش</button>}</td></tr>)}</Table>{!values.length && <p className="muted">هنوز سالی تعریف نشده است.</p>}</Panel>; }
    return <>{list('سال‌های تحصیلی', years.academicYears, setAcademicEdit, canYear)}{list('سال‌های مالی مستقل', years.fiscalYears, setFiscalEdit, canFinance)}
    <div className="two-columns">{canYear && <YearForm fiscal={false} editing={academicEdit} onCancel={() => setAcademicEdit(null)} onSave={refresh}/>}{canFinance && <YearForm fiscal editing={fiscalEdit} onCancel={() => setFiscalEdit(null)} onSave={refresh}/>}</div>
    {(canYear || canFinance) && <Panel title="آماده‌سازی سال بعد" subtitle="کپی اطلاعات و انتقال مانده دو عملیات جدا هستند. هیچ‌کدام سال مالی را تغییر نمی‌دهند.">{selection}</Panel>}
    <div className="two-columns">{canYear && <FormCard title="۱. کپی انتخابی اطلاعات" reset={false} disabled={!source || !target} button="اجرای کپی تأییدشده" onSave={async () => {
                if (!copy || !reviewedCopy)
                    throw new Error('ابتدا پیش‌نمایش را بگیرید و تأیید کنید.');
                await runOperation(user.id, '/years/copy', { sourceId: source, targetId: target, options, version: copy.version });
                invalidate();
                await refresh();
            }}>
      <fieldset className="checks"><legend>چه اطلاعاتی به سال مقصد مرتبط شود؟</legend>{Object.entries(optionNames).map(([key, label]) => <label className="check" key={key}><input type="checkbox" checked={options[key]} onChange={e => { setOptions({ ...options, [key]: e.target.checked }); setReviewedCopy(false); }}/>{label}</label>)}</fieldset>
      <PreviewButton onClick={async () => { setCopy(await get<CopyPreview>('/years/copy-preview?sourceId=' + source + '&targetId=' + target)); setReviewedCopy(false); }}/>
      {copy && <><ul>{Object.entries(copy.counts).map(([key, value]) => <li key={key}>{optionNames[key]}: {number(value)}</li>)}</ul>{copy.notes.map(note => <p className="muted" key={note}>{note}</p>)}<label className="check"><input type="checkbox" checked={reviewedCopy} onChange={e => setReviewedCopy(e.target.checked)}/>انتخاب‌ها و نتیجهٔ پیش‌نمایش را تأیید می‌کنم.</label></>}
    </FormCard>}
    {canFinance && <FormCard title="۲. انتقال ماندهٔ بدهی" reset={false} disabled={!source || !target} button="ثبت انتقال ماندهٔ تأییدشده" onSave={async () => {
                if (!carry || !reviewedCarry)
                    throw new Error('ابتدا مانده‌ها را پیش‌نمایش و تأیید کنید.');
                await runOperation(user.id, '/years/carry', { sourceId: source, targetId: target, studentIds, version: carry.version });
                invalidate();
                await refresh();
            }}>
      <p>بدهی هر دانش‌آموز جدا منتقل می‌شود؛ ولی مجموع فرزندان مرتبط خود را می‌بیند. سند و شهریهٔ تازه‌ای برای همان بدهی ساخته نمی‌شود.</p>
      <Field label="پرونده‌های انتقال؛ بدون انتخاب یعنی همهٔ بدهکاران مبدأ"><select multiple value={studentIds} onChange={e => { setStudentIds(Array.from(e.target.selectedOptions, o => o.value)); setCarry(undefined); setReviewedCarry(false); }}>{sourceStudents.data?.students.filter(s => s.grade_id).map(s => <option key={s.id} value={s.id}>{s.name} · {s.code}</option>)}</select></Field>
      <PreviewButton onClick={async () => { const query = new URLSearchParams({ sourceId: source, targetId: target }); studentIds.forEach(id => query.append('studentId', id)); setCarry(await get<CarryPreview>('/years/carry-preview?' + query)); setReviewedCarry(false); }}/>
      {carry && <><p><strong>{money(carry.amount)} تومان</strong> · {number(carry.studentCount)} دانش‌آموز</p><Table head={['دانش‌آموز', 'بابت', 'مانده تومان']}>{carry.claims.map(row => <tr key={row.invoice_id}><td>{row.student_name}</td><td>{row.title}</td><td>{money(row.remaining)}</td></tr>)}</Table><label className="check"><input type="checkbox" checked={reviewedCarry} onChange={e => setReviewedCarry(e.target.checked)}/>مانده‌های نمایش‌داده‌شده را برای انتقال تأیید می‌کنم.</label></>}
    </FormCard>}</div>
  </>;
}
function PreviewButton({ onClick }: {
    onClick: () => Promise<void>;
}) {
    const [error, setError] = useState(''), [busy, setBusy] = useState(false);
    return <><button type="button" disabled={busy} onClick={async () => { setError(''); setBusy(true); try {
        await onClick();
    }
    catch (e) {
        setError(e instanceof Error ? e.message : 'دریافت پیش‌نمایش ممکن نشد.');
    }
    finally {
        setBusy(false);
    } }}>{busy ? 'در حال دریافت…' : 'مشاهدهٔ پیش‌نمایش'}</button>{error && <p role="alert" className="error-text">{error}</p>}</>;
}
