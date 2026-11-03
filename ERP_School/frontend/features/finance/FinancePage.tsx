import { useState } from 'react';
import { runOperation } from '../../shared/api';
import { useResource } from '../../shared/hooks';
import type { Balances, Finance, Student, User, Years } from '../../shared/types';
import { Field, FormCard, Panel, ResourceState, Table } from '../../shared/ui';
import { date, exportCsv, money, today } from '../../shared/format';
const accounts: Record<string, string> = { '1101': 'بانک مدرسه', '1301': 'دریافتنی شهریه', '2101': 'تعهد خدمات آموزشی' };
export default function FinancePage({ user, yearId, years }: {
    user: User;
    yearId: string;
    years: Years;
}) {
    const finance = useResource<Finance>('/finance'), balances = useResource<Balances>('/balances?yearId=' + yearId);
    const registered = useResource<{students: Student[]}>('/students?yearId=' + yearId);
    const [tab, setTab] = useState('balances');
    const canWrite = user.permissions.includes('finance.write'), canLedger = user.permissions.includes('finance.read.all');
    const invoices = (finance.data?.invoices || []).filter(i => i.academic_year_id === yearId);
    const claimIds = new Set(balances.data?.balances.map(b => b.invoice_id));
    const payable = (finance.data?.invoices || []).filter(i => i.amount > i.paid && claimIds.has(i.id));
    const fiscalFields = <><Field label="سال مالی ثبت سند"><select name="fiscalYearId" required defaultValue=""><option value="">مستقل از سال تحصیلی انتخاب کنید…</option>{years.fiscalYears.filter(y => y.status !== 'closed').map(y => <option key={y.id} value={y.id}>{y.title}</option>)}</select></Field><Field label="تاریخ حسابداری سند"><input name="postedOn" type="date" required defaultValue={today()}/></Field></>;
    async function refresh() { await finance.refresh(); await balances.refresh(); }
    return <><ResourceState {...finance}/><ResourceState {...balances}/><div className="metrics"><article><span>ماندهٔ جاری این سال</span><strong>{money(balances.data?.total || 0)} <small>تومان</small></strong></article><article><span>ماندهٔ انتقالی در لحظهٔ انتقال</span><strong>{money(balances.data?.openingSnapshot || 0)} <small>تومان</small></strong></article></div>
    <Panel title="شهریه و حساب‌های دانش‌آموزان" subtitle="جمع ماندهٔ ولی فقط از پرونده‌های مرتبط محاسبه می‌شود. پرداخت بدهی انتقالی به همان طلب اصلی وصل می‌ماند.">
    <div className="tabs" role="tablist">{[['balances', 'ماندهٔ سال'], ['invoices', 'شهریه‌های سال'], ['receipts', 'دریافت‌ها'], ...(canLedger ? [['journals', 'اسناد و تراز']] : [])].map(([id, label]) => <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}>{label}</button>)}</div>
    {tab === 'balances' && <><button onClick={() => exportCsv('balances', [['دانش‌آموز', 'بابت', 'مانده تومان'], ...(balances.data?.balances.map(b => [b.name, b.title, b.remaining / 10]) || [])])}>خروجی مانده</button><Table head={['دانش‌آموز', 'بابت', 'مطالبه تومان', 'پرداخت تومان', 'مانده تومان', 'نوع']}>{balances.data?.balances.map(row => <tr key={row.invoice_id}><td>{row.name}</td><td>{row.title}</td><td>{money(row.amount)}</td><td>{money(row.paid)}</td><td><strong>{money(row.remaining)}</strong></td><td>{row.opening_amount ? 'ارجاع انتقالی' : 'شهریهٔ این سال'}</td></tr>)}</Table></>}
    {tab === 'invoices' && <Table head={['دانش‌آموز', 'عنوان', 'مبلغ تومان', 'پرداخت تومان', 'سررسید']}>{invoices.map(row => <tr key={row.id}><td>{row.student_name}</td><td>{row.title}</td><td>{money(row.amount)}</td><td>{money(row.paid)}</td><td>{date(row.due_date)}</td></tr>)}</Table>}
    {tab === 'receipts' && <Table head={['دانش‌آموز', 'بابت', 'مبلغ تومان', 'مرجع', 'زمان ثبت']}>{finance.data?.receipts.map(row => <tr key={row.id}><td>{row.student_name}</td><td>{row.invoice_title}</td><td>{money(row.amount)}</td><td>{row.reference}</td><td>{date(row.created_at)}</td></tr>)}</Table>}
    {tab === 'journals' && <><p className="muted">هستهٔ فعلی ثبت دوطرفهٔ شهریه و دریافت را دارد؛ حسابداری کامل، گردش تأیید و بستن سال در مراحل بعد تکمیل می‌شوند.</p><Table head={['شرح', 'دانش‌آموز', 'بدهکار', 'بستانکار', 'مبلغ هر طرف تومان', 'سال مالی', 'تاریخ حسابداری']}>{finance.data?.journals.map(row => <tr key={row.id}><td>{row.description}</td><td>{row.student_name}</td><td>{accounts[row.debit_account] || row.debit_account}</td><td>{accounts[row.credit_account] || row.credit_account}</td><td>{money(row.amount)}</td><td>{years.fiscalYears.find(y => y.id === row.fiscal_year_id)?.title || 'سند پایلوت قدیمی'}</td><td>{row.posted_on ? date(row.posted_on) : '—'}</td></tr>)}</Table><p className="success">جمع بدهکار و بستانکار این اسناد: {money(finance.data?.journals.reduce((sum, j) => sum + j.amount, 0) || 0)} تومان برای هر طرف</p></>}
    </Panel>{canWrite && <div className="two-columns"><FormCard title="تعریف شهریهٔ سال انتخاب‌شده" disabled={!yearId} onSave={async (values) => { await runOperation(user.id, '/finance/invoices', { ...values, yearId }); await refresh(); }}>
      <Field label="دانش‌آموز شهریه"><select name="studentId" required defaultValue=""><option value="">دانش‌آموز را انتخاب کنید…</option>{registered.data?.students.filter(s => s.grade_id !== null).map(s => <option key={s.id} value={s.id}>{s.name} · {s.code}</option>)}</select></Field><Field label="عنوان شهریه"><input name="title" required maxLength={100}/></Field><Field label="مبلغ شهریه به تومان"><input name="amount" required inputMode="numeric" placeholder="بدون اعشار"/></Field><Field label="سررسید شهریه"><input name="dueDate" type="date" required defaultValue={today()}/></Field>{fiscalFields}
    </FormCard><FormCard title="ثبت دریافت شهریه" disabled={!yearId || !payable.length} onSave={async (values) => { await runOperation(user.id, '/finance/receipts', values); await refresh(); }}>
      <Field label="شهریهٔ دارای مانده"><select name="invoiceId" required defaultValue=""><option value="">طلب را انتخاب کنید…</option>{payable.map(i => <option key={i.id} value={i.id}>{i.student_name} · {money(i.amount - i.paid)} تومان · {i.title}</option>)}</select></Field><Field label="مبلغ دریافت به تومان"><input name="amount" required inputMode="numeric" placeholder="بدون اعشار"/></Field><Field label="شماره پیگیری یا مرجع"><input name="reference" maxLength={100}/></Field>{fiscalFields}<p className="muted">بیشتر از مانده پذیرفته نمی‌شود. درخواست نامشخص با همان شناسه پیگیری می‌شود و سند تکراری نمی‌سازد.</p>
    </FormCard></div>}</>;
}
