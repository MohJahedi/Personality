import { useState, type ReactNode, type FormEvent } from 'react';
import { AlertCircle, CheckCircle2, LoaderCircle } from 'lucide-react';
export function Alert({ children }: {
    children: ReactNode;
}) { return <div className="alert" role="alert"><AlertCircle size={20}/><div>{children}</div></div>; }
export function Success({ children }: {
    children: ReactNode;
}) { return <div className="success" role="status"><CheckCircle2 size={20}/>{children}</div>; }
export function Empty({ children }: {
    children: ReactNode;
}) { return <div className="empty">{children}</div>; }
export function Panel({ title, subtitle, children }: {
    title: string;
    subtitle?: string;
    children: ReactNode;
}) { return <section className="panel"><header className="panel-head"><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</header><div className="panel-body">{children}</div></section>; }
export function Field({ label, children }: {
    label: string;
    children: ReactNode;
}) { return <label className="field"><span>{label}</span>{children}</label>; }
export function Table({ head, children }: {
    head: string[];
    children: ReactNode;
}) { return <div className="table-scroll" tabIndex={0} aria-label="جدول؛ در صفحهٔ کوچک به صورت افقی پیمایش کنید"><table><thead><tr>{head.map(h => <th key={h} scope="col">{h}</th>)}</tr></thead><tbody>{children}</tbody></table></div>; }
export function ResourceState({ loading, error }: {
    loading: boolean;
    error: string;
}) { return error ? <Alert>{error}</Alert> : loading ? <p className="loading" role="status"><LoaderCircle className="spin" size={18}/>در حال دریافت اطلاعات…</p> : null; }
export function FormCard({ title, note, onSave, children, button = 'ذخیره', reset = true, disabled = false }: {
    title: string;
    note?: string;
    onSave: (values: Record<string, string>) => Promise<unknown>;
    children: ReactNode;
    button?: string;
    reset?: boolean;
    disabled?: boolean;
}) {
    const [busy, setBusy] = useState(false), [error, setError] = useState(''), [saved, setSaved] = useState(false);
    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (busy)
            return;
        const form = event.currentTarget;
        const values = Object.fromEntries(new FormData(form)) as Record<string, string>;
        setBusy(true);
        setError('');
        setSaved(false);
        try {
            await onSave(values);
            setSaved(true);
            if (reset)
                form.reset();
        }
        catch (e) {
            setError(e instanceof Error ? e.message : 'ثبت انجام نشد.');
        }
        finally {
            setBusy(false);
        }
    }
    return <section className="panel form-card"><header className="panel-head"><h2>{title}</h2>{note && <p>{note}</p>}</header><form onSubmit={submit} className="panel-body" aria-label={title}>
    <fieldset disabled={busy || disabled}>{children}</fieldset>
    {error && <Alert>{error}</Alert>}{saved && <Success>با موفقیت ذخیره شد.</Success>}
    <button className="primary" disabled={busy || disabled} type="submit">{busy ? <LoaderCircle className="spin" size={18}/> : <CheckCircle2 size={18}/>} {busy ? 'در حال ذخیره…' : button}</button>
  </form></section>;
}
