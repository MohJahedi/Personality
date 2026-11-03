import { useCallback, useEffect, useState, type ComponentType } from 'react';
import { BookOpen, CalendarDays, ChevronLeft, GraduationCap, LayoutDashboard, LogOut, Menu, Palette, ReceiptText, ShieldCheck, Users, X, RefreshCw, ClipboardCheck } from 'lucide-react';
import { get, post, readPending, resumeOperation, clearPending, type PendingOperation } from '../shared/api';
import type { Context, Years, Catalog, Student, Balances, User } from '../shared/types';
import { useResource } from '../shared/hooks';
import { Alert, Empty, Panel, ResourceState } from '../shared/ui';
import { money, number } from '../shared/format';
import Login from '../features/identity/Login';
import UsersPage from '../features/identity/UsersPage';
import SettingsPage from '../features/preferences/SettingsPage';
import { applyAppearance, cachedAppearance } from '../features/preferences/appearance';
import YearsPage from '../features/years/YearsPage';
import AcademicsPage from '../features/academics/AcademicsPage';
import SchedulePage from '../features/academics/SchedulePage';
import StudentsPage from '../features/students/StudentsPage';
import FinancePage from '../features/finance/FinancePage';
import AttendancePage from '../features/attendance/AttendancePage';
type View = 'home' | 'years' | 'academics' | 'students' | 'schedule' | 'finance' | 'attendance' | 'users' | 'settings';
const nav: {
    id: View;
    name: string;
    Icon: ComponentType<{
        size?: number;
    }>;
    allowed?: string[];
}[] = [
    { id: 'home', name: 'نمای کلی', Icon: LayoutDashboard },
    { id: 'years', name: 'سال‌ها و انتقال', Icon: CalendarDays },
    { id: 'academics', name: 'پایه، درس و کلاس', Icon: BookOpen, allowed: ['academics.read', 'academics.manage'] },
    { id: 'students', name: 'دانش‌آموزان و اولیا', Icon: Users, allowed: ['students.read.all', 'students.read.assigned', 'students.read.linked', 'students.read.self'] },
    { id: 'schedule', name: 'برنامهٔ هفتگی', Icon: CalendarDays, allowed: ['academics.read', 'academics.manage'] },
    { id: 'finance', name: 'شهریه و حسابداری', Icon: ReceiptText, allowed: ['finance.read.all', 'finance.read.linked', 'finance.read.self', 'finance.write'] },
    { id: 'attendance', name: 'حضور و غیاب', Icon: ClipboardCheck, allowed: ['attendance.read.all', 'attendance.read.assigned', 'attendance.read.linked', 'attendance.read.self'] },
    { id: 'users', name: 'کاربران و نقش‌ها', Icon: ShieldCheck, allowed: ['users.manage', 'roles.manage'] },
    { id: 'settings', name: 'ظاهر و حساب من', Icon: Palette },
];
const emptyYears: Years = { academicYears: [], fiscalYears: [] };
export default function App() {
    const [context, setContext] = useState<Context>(), [error, setError] = useState('');
    const [view, setView] = useState<View>(() => nav.some(n => n.id === location.hash.slice(1)) ? location.hash.slice(1) as View : 'home'), [drawer, setDrawer] = useState(false), [yearId, setYearId] = useState(''), [revision, setRevision] = useState(0);
    const [pending, setPending] = useState<PendingOperation | null>(null), [retrying, setRetrying] = useState(false);
    const user = context?.user;
    const years = useResource<Years>(user && !user.must_change_password ? '/years' : null);
    useEffect(() => { const sync = () => { const value = location.hash.slice(1); setView(nav.some(n => n.id === value) ? value as View : 'home'); }; window.addEventListener('hashchange', sync); return () => window.removeEventListener('hashchange', sync); }, []);
    const refreshContext = useCallback(async () => { const next = await get<Context>('/context'); setContext(next); applyAppearance(next.user ? next.preferences : cachedAppearance()); }, []);
    useEffect(() => { applyAppearance(cachedAppearance()); refreshContext().catch(e => setError(e instanceof Error ? e.message : 'ارتباط با سامانه برقرار نشد.')); }, [refreshContext]);
    useEffect(() => {
        if (!user) {
            setPending(null);
            return;
        }
        const update = () => setPending(readPending(user.id));
        update();
        window.addEventListener('erp-pending', update);
        return () => window.removeEventListener('erp-pending', update);
    }, [user?.id]);
    useEffect(() => { if (years.data && !years.data.academicYears.some(y => y.id === yearId))
        setYearId(years.data.academicYears.find(y => y.status === 'active')?.id || years.data.academicYears[0]?.id || ''); }, [years.data, yearId]);
    if (!context)
        return <main className="startup">{error ? <><Alert>{error}</Alert><button onClick={() => window.location.reload()}>تلاش دوباره</button></> : <p role="status">در حال اتصال به مدرسه…</p>}</main>;
    if (!user)
        return <Login setup={context.setupRequired} protectedSetup={context.setupProtected} onLogin={async () => { setView('home'); await refreshContext(); }}/>;
    const visible = nav.filter(n => (!user.must_change_password || n.id === 'settings') && (!n.allowed || n.allowed.some(p => user.permissions.includes(p))));
    const current = visible.find(n => n.id === view) || visible[0];
    const currentView = current.id;
    async function refreshAll() { await refreshContext(); await years.refresh(); setRevision(value => value + 1); }
    function navigate(next: View) { setView(next); window.location.hash = next; setDrawer(false); }
    return <div className="shell"><a className="skip-link" href="#main">رفتن به محتوای اصلی</a>
    {drawer && <button className="nav-overlay" aria-label="بستن منو" onClick={() => setDrawer(false)}/>}
    <aside className={'sidebar' + (drawer ? ' open' : '')}><div className="brand"><GraduationCap size={33}/><div>مدرسه<small>ERP_School · نسخهٔ ۰٫۴</small></div><button className="mobile-only" aria-label="بستن منوی اصلی" onClick={() => setDrawer(false)}><X /></button></div>
      <div className="school-label"><span className="avatar">م</span><div><strong>میز کار مدرسه</strong><small>نصب و پایگاه دادهٔ مستقل</small></div></div>
      <nav aria-label="منوی اصلی">{visible.map(({ id, name, Icon }) => <button key={id} className={id === currentView ? 'active' : ''} aria-current={id === currentView ? 'page' : undefined} onClick={() => navigate(id)}><Icon size={20}/><span>{name}</span><ChevronLeft size={15}/></button>)}</nav>
      <div className="sidebar-bottom"><ShieldCheck size={18}/><span>دسترسی متناسب با حساب شما</span><small>نسخهٔ توسعه · دادهٔ ساختگی</small></div>
    </aside><div className="workspace"><header className="topbar"><div className="breadcrumb"><button className="mobile-only" aria-label="بازکردن منوی اصلی" onClick={() => setDrawer(true)}><Menu /></button><span>میز کار</span><ChevronLeft size={16}/><strong>{current.name}</strong></div><div className="top-actions">
      {!user.must_change_password && <label className="year-selector"><span>سال تحصیلی</span><select aria-label="سال تحصیلی جاری نما" value={yearId} onChange={e => setYearId(e.target.value)}><option value="">هنوز سالی انتخاب نشده</option>{years.data?.academicYears.map(y => <option key={y.id} value={y.id}>{y.title}</option>)}</select></label>}
      <button aria-label="بازخوانی اطلاعات" onClick={() => refreshAll().catch(e => setError(String(e)))}><RefreshCw size={19}/></button>
      <button className="logout" aria-label="خروج از حساب" onClick={async () => { setError(''); if (pending) {
        setError('ابتدا نتیجهٔ عملیات نامشخص را پیگیری کنید تا ثبت تکراری ایجاد نشود.');
        return;
    } try {
        await post('/auth', { action: 'logout' });
        clearPending(user.id);
        await refreshContext();
        setYearId('');
    }
    catch (e) {
        setError(e instanceof Error ? e.message : 'خروج انجام نشد.');
    } }}><LogOut size={18}/><span>خروج</span></button>
    </div></header><main id="main" className="content"><div className="development-note"><ShieldCheck size={18}/><span>محیط توسعهٔ رسمی؛ آزمون با دادهٔ ساختگی. پذیرش امنیت، عملیات و دستگاه واقعی پیش از بهره‌برداری لازم است.</span><span className="badge">۰٫۴</span></div>
      {error && <Alert>{error}</Alert>}<ResourceState {...years}/>
      {user.must_change_password && <Alert>گذرواژهٔ موقت دارید. ابتدا در بخش «تغییر گذرواژه» گذرواژهٔ شخصی خود را تنظیم کنید؛ سپس سایر بخش‌ها فعال می‌شوند.</Alert>}
      {pending && <Panel title="یک عملیات هنوز پاسخ قطعی ندارد"><p>برای جلوگیری از شهریه، دریافت یا انتقال تکراری، همان درخواست ذخیره‌شده را پیگیری کنید.</p><button disabled={retrying} onClick={async () => { setRetrying(true); setError(''); try {
        await resumeOperation(user.id);
        await refreshAll();
    }
    catch (e) {
        setError(e instanceof Error ? e.message : 'پیگیری انجام نشد.');
    }
    finally {
        setRetrying(false);
    } }}>{retrying ? 'در حال پیگیری…' : 'پیگیری همان درخواست'}</button></Panel>}
      <header className="page-heading"><div><p className="eyebrow">یک مسیر روشن برای کارهای مدرسه</p><h1>{currentView === 'home' ? 'مدرسه، در یک نگاه' : current.name}</h1></div><div className="identity"><span className="avatar">{user.display_name.slice(0, 1)}</span><div><strong>{user.display_name}</strong><small>{user.username}</small></div></div></header>
      <div key={user.id + ':' + currentView + ':' + revision}>
        {currentView === 'home' && <Dashboard user={user} yearId={yearId} years={years.data || emptyYears} navigate={navigate}/>}
        {currentView === 'years' && <YearsPage user={user} years={years.data || emptyYears} refresh={years.refresh}/>}
        {currentView === 'academics' && <AcademicsPage user={user} yearId={yearId}/>}
        {currentView === 'students' && <StudentsPage user={user} yearId={yearId}/>}
        {currentView === 'schedule' && <SchedulePage user={user} yearId={yearId}/>}
        {currentView === 'finance' && <FinancePage user={user} yearId={yearId} years={years.data || emptyYears}/>}
        {currentView === 'attendance' && <AttendancePage user={user} yearId={yearId}/>}
        {currentView === 'users' && <UsersPage user={user} yearId={yearId} onAccessChanged={refreshContext}/>}
        {currentView === 'settings' && <SettingsPage preferences={context.preferences} onChange={refreshContext}/>}
      </div><footer>ERP_School · فارسی و واکنش‌گرا · وب، پایهٔ API برای ادامهٔ اندروید</footer>
    </main></div></div>;
}
function Dashboard({ user, yearId, years, navigate }: {
    user: User;
    yearId: string;
    years: Years;
    navigate: (view: View) => void;
}) {
    const students = useResource<{
        students: Student[];
    }>('/students?yearId=' + yearId), catalog = useResource<Catalog>(user.permissions.includes('academics.read') || user.permissions.includes('academics.manage') ? '/academics?yearId=' + yearId : null), balances = useResource<Balances>('/balances?yearId=' + yearId);
    return <><div className="metrics"><article><span>پرونده‌های در دسترس</span><strong>{number(students.data?.students.length || 0)} <small>نفر</small></strong></article><article><span>کلاس‌های تعریف‌شدهٔ سال</span><strong>{number(catalog.data?.classes.length || 0)} <small>کلاس</small></strong></article><article><span>ماندهٔ قابل مشاهدهٔ سال</span><strong>{money(balances.data?.total || 0)} <small>تومان</small></strong></article></div>
    <ResourceState {...students}/><ResourceState {...catalog}/><ResourceState {...balances}/>
    <Panel title="شروع منظم، توسعهٔ مرحله‌به‌مرحله" subtitle="سال تحصیلی و سال مالی مستقل‌اند؛ هر عملیات در محدودهٔ نقش شما انجام می‌شود."><div className="workflow-cards">{[['years', '۱', 'سال‌ها را تعریف کنید', 'بازهٔ سال تحصیلی و سال مالی را جدا مشخص کنید.'], ['academics', '۲', 'ساختار آموزشی را بسازید', 'پایه، درس، معلم و کلاس را تعریف کنید.'], ['students', '۳', 'پرونده‌ها را ثبت کنید', 'هر دانش‌آموز را در کلاس همان سال ثبت‌نام کنید.'], ['schedule', '۴', 'برنامه را بچینید', 'تعداد زنگ هر روز و درس و معلم آن را مشخص کنید.']].filter(([id]) => nav.find(n => n.id === id)?.allowed?.some(p => user.permissions.includes(p)) || id === 'years').map(([id, step, title, note]) => <button key={id} onClick={() => navigate(id as View)}><span className="step">{step}</span><strong>{title}</strong><p>{note}</p><ChevronLeft size={17}/></button>)}</div></Panel>
    {!years.academicYears.length && <Empty>راه‌اندازی حساب انجام شد. برای شروع، اولین سال تحصیلی را تعریف کنید.</Empty>}
    {user.permissions.includes('backup.export') && <Panel title="پشتیبان داده‌های همین مدرسه" subtitle="فایل شامل حساب‌ها و داده‌های مدرسه است؛ آن را در محل امن نگه دارید. بازیابی باید ابتدا در محیط جدا آزمایش شود."><a className="button-link" href="/api/backup">دریافت پشتیبان SQLite</a></Panel>}
  </>;
}
