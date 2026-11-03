import { useState } from 'react';
import { post } from '../../shared/api';
import type { Preferences, Profile } from '../../shared/types';
import { Field, FormCard, Panel, ResourceState } from '../../shared/ui';
import { useResource } from '../../shared/hooks';
import { applyAppearance, fontNames, themeNames, themeColors } from './appearance';
export default function SettingsPage({ preferences, onChange }: {
    preferences: Preferences;
    onChange: () => Promise<void>;
}) {
    const [draft, setDraft] = useState(preferences);
    const profile = useResource<Profile>('/profile');
    function preview(value: Partial<Preferences>) { const next = { ...draft, ...value }; setDraft(next); applyAppearance(next); }
    return <><Panel title="ظاهر دلخواه شما" subtitle="پیش‌نمایش فوری است؛ برای نگهداری در حساب، ذخیره را بزنید.">
    <div className="form-grid"><Field label="فونت"><select value={draft.font} onChange={e => preview({ font: e.target.value })}>{Object.entries(fontNames).map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></Field>
    <Field label="اندازهٔ نمایش"><select value={draft.size} onChange={e => preview({ size: e.target.value })}><option value="small">کوچک</option><option value="normal">معمولی</option><option value="large">درشت</option></select></Field></div>
    <fieldset className="theme-options"><legend>تم رنگی</legend>{Object.entries(themeNames).map(([id, name]) => <label className="theme-choice" key={id}><input type="radio" name="theme" checked={draft.theme === id} onChange={() => preview({ theme: id, accent: '' })}/><span className="swatch" style={{ background: themeColors[id] }}/>{name}</label>)}</fieldset>
    <div className="inline-fields"><Field label="رنگ دلخواه"><input type="color" aria-label="رنگ دلخواه" value={/^#[0-9a-fA-F]{6}$/.test(draft.accent) ? draft.accent : themeColors[draft.theme]} onInput={e => preview({ accent: e.currentTarget.value })} onChange={e => preview({ accent: e.target.value })}/></Field><Field label="کد رنگ دلخواه"><input value={draft.accent} dir="ltr" maxLength={7} placeholder={themeColors[draft.theme]} onChange={e => preview({ accent: e.target.value })}/></Field><button type="button" onClick={() => preview({ accent: '' })}>رنگ اصلی تم</button><button type="button" onClick={() => { setDraft(preferences); applyAppearance(preferences); }}>لغو پیش‌نمایش</button></div>
    <p className="appearance-sample">آموزش باکیفیت، مدیریت روشن و حساب‌های دقیق. ۱۲۳۴۵۶۷۸۹۰</p>
    <FormCard title="ذخیرهٔ تنظیمات ظاهر" onSave={async () => { await post('/preferences', draft); await onChange(); }}><p>این تنظیمات برای حساب شما ذخیره می‌شود و روی حساب سایر کاربران اثر ندارد.</p></FormCard>
  </Panel>
  <ResourceState {...profile}/>{profile.data && <div className="two-columns"><FormCard title="مشخصات فردی من" reset={false} onSave={async (values) => { await post('/profile', values); await profile.refresh(); await onChange(); }}>
    <Field label="نام نمایشی"><input name="name" required maxLength={100} defaultValue={profile.data.name}/></Field><div className="form-grid"><Field label="نام"><input name="first_name" maxLength={80} defaultValue={profile.data.first_name}/></Field><Field label="نام خانوادگی"><input name="last_name" maxLength={80} defaultValue={profile.data.last_name}/></Field></div>
    <Field label="تلفن"><input name="phone" type="tel" maxLength={25} dir="ltr" defaultValue={profile.data.phone}/></Field><Field label="رایانامه"><input name="email" type="email" maxLength={160} dir="ltr" defaultValue={profile.data.email}/></Field>
  </FormCard><FormCard title="تغییر گذرواژه" note="پس از تغییر، تمام نشست‌های قبلی باطل می‌شوند و همین نشست جایگزین می‌شود." onSave={async (values) => {
                if (values.newPassword !== values.confirmPassword)
                    throw new Error('تکرار گذرواژه یکسان نیست.');
                await post('/password', values);
                await onChange();
            }}>
    <Field label="گذرواژهٔ فعلی"><input name="currentPassword" type="password" required autoComplete="current-password" dir="ltr"/></Field>
    <Field label="گذرواژهٔ جدید"><input name="newPassword" type="password" required minLength={12} maxLength={128} autoComplete="new-password" dir="ltr"/></Field>
    <Field label="تکرار گذرواژهٔ جدید"><input name="confirmPassword" type="password" required minLength={12} maxLength={128} autoComplete="new-password" dir="ltr"/></Field>
  </FormCard></div>}</>;
}
