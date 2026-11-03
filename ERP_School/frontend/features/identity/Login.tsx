import { useState } from 'react';
import { GraduationCap, ShieldCheck, CalendarDays, Wallet } from 'lucide-react';
import { post } from '../../shared/api';
import { Field, FormCard } from '../../shared/ui';
export default function Login({ setup, protectedSetup, onLogin }: {
    setup: boolean;
    protectedSetup: boolean;
    onLogin: () => Promise<void>;
}) {
    const [show, setShow] = useState(false);
    return <main className="login-layout"><section className="login-branding">
    <div className="brand"><GraduationCap size={36}/><div>مدرسه<small>ERP_School · مدیریت یکپارچه</small></div></div>
    <div><span className="eyebrow">آموزش، مدیریت و حسابداری</span><h1>کارهای مدرسه،<br />در یک جای روشن.</h1><p>یک مسیر منظم برای سال تحصیلی، کلاس‌ها، پرونده‌ها و حساب‌های مدرسه.</p>
    <div className="login-highlights"><span><CalendarDays />سال و برنامهٔ آموزشی</span><span><Wallet />شهریه و ماندهٔ هر دانش‌آموز</span><span><ShieldCheck />دسترسی متناسب با نقش</span></div></div>
    <small>نسخهٔ توسعهٔ رسمی ۰٫۴ · پایگاه دادهٔ مستقل برای هر مدرسه</small>
  </section><section className="login-form"><FormCard title={setup ? 'ساخت ادمین اولیهٔ مدرسه' : 'ورود به مدرسه'} note={setup ? 'این حساب فقط در نخستین راه‌اندازی ساخته می‌شود و مدیریت کاربران و نقش‌ها را در اختیار دارد.' : 'نام کاربری و گذرواژه‌ای را وارد کنید که ادمین مدرسه برایتان ساخته است.'} button={setup ? 'ساخت حساب ادمین' : 'ورود'} reset={false} onSave={async (values) => {
            if (setup && values.password !== values.confirmPassword)
                throw new Error('تکرار گذرواژه یکسان نیست.');
            await post('/auth', { action: setup ? 'setup' : 'login', ...values });
            await onLogin();
        }}>
    {setup && <Field label="نام نمایشی ادمین"><input name="name" required maxLength={100} autoComplete="name"/></Field>}
    <Field label="نام کاربری"><input name="username" required minLength={3} maxLength={40} pattern="[a-zA-Z][a-zA-Z0-9_.-]{2,39}" autoComplete="username" dir="ltr" autoCapitalize="none"/></Field>
    <Field label="گذرواژه"><input name="password" type={show ? 'text' : 'password'} required minLength={12} maxLength={128} autoComplete={setup ? 'new-password' : 'current-password'} dir="ltr"/></Field>
    {setup && <Field label="تکرار گذرواژه"><input name="confirmPassword" type="password" required minLength={12} maxLength={128} autoComplete="new-password" dir="ltr"/></Field>}
    <label className="check"><input type="checkbox" checked={show} onChange={e => setShow(e.target.checked)}/>نمایش گذرواژه</label>
    {setup && protectedSetup && <Field label="کد راه‌اندازی سرور"><input name="setupToken" type="password" required autoComplete="off" dir="ltr"/></Field>}
  </FormCard><p className="muted">این نسخه برای آزمون با اطلاعات ساختگی است؛ پذیرش عملیاتی و استقرار نهایی هنوز لازم است.</p></section></main>;
}
