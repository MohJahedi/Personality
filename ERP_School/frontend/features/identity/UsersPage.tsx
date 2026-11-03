import { useState } from 'react';
import { post } from '../../shared/api';
import { useResource } from '../../shared/hooks';
import type { Catalog, ManagedUser, Role, Student, User } from '../../shared/types';
import { Field, FormCard, Panel, ResourceState, Table } from '../../shared/ui';
import { statuses } from '../../shared/format';
export default function UsersPage({ user, yearId, onAccessChanged }: {
    user: User;
    yearId: string;
    onAccessChanged: () => Promise<void>;
}) {
    const canUsers = user.permissions.includes('users.manage'), canRoles = user.permissions.includes('roles.manage');
    const roles = useResource<{
        roles: Role[];
        permissions: Record<string, string>;
    }>('/roles');
    const users = useResource<{
        users: ManagedUser[];
    }>(canUsers ? '/users' : null);
    const students = useResource<{
        students: Student[];
    }>(canUsers ? '/students?yearId=' + yearId : null);
    const catalog = useResource<Catalog>(canUsers ? '/academics?yearId=' + yearId : null);
    const [editing, setEditing] = useState<ManagedUser | null>(null), [selectedRoles, setSelectedRoles] = useState<string[]>([]);
    const [studentIds, setStudentIds] = useState<string[]>([]), [classes, setClasses] = useState<string[]>([]), [roleEditing, setRoleEditing] = useState<Role | null>(null), [permissions, setPermissions] = useState<string[]>([]);
    const toggle = (values: string[], value: string) => values.includes(value) ? values.filter(v => v !== value) : [...values, value];
    function edit(value: ManagedUser | null) { setEditing(value); setSelectedRoles(value?.roles || []); setStudentIds(value?.studentIds || []); setClasses(value?.classIds || []); }
    return <><ResourceState {...roles}/><ResourceState {...users}/>{canUsers && <><Panel title="کاربران مدرسه" subtitle="مجوزها از مجموع نقش‌های کاربر و محدودهٔ کلاس یا پرونده محاسبه می‌شوند.">
    <Table head={['نام', 'نام کاربری', 'نقش‌ها', 'وضعیت', 'عملیات']}>{users.data?.users.map(row => <tr key={row.id}><td>{row.display_name}</td><td dir="ltr">{row.username}</td><td>{row.roles.map(id => roles.data?.roles.find(r => r.id === id)?.name || id).join('، ')}</td><td>{statuses[row.status]}</td><td><button onClick={() => edit(row)}>ویرایش دسترسی</button></td></tr>)}</Table>
  </Panel><div className="two-columns"><FormCard key={editing?.id || 'new'} title={editing ? 'ویرایش دسترسی ' + editing.display_name : 'تعریف کاربر جدید'} reset={false} onSave={async (values) => {
                await post('/users', { ...values, ...(editing ? { id: editing.id } : {}), roles: selectedRoles, studentIds, classIds: classes });
                await users.refresh(); await onAccessChanged();
                edit(null);
            }}>
    {editing ? <button type="button" onClick={() => edit(null)}>انصراف از ویرایش؛ کاربر جدید</button> : <><Field label="نام نمایشی کاربر"><input name="name" required maxLength={100}/></Field><Field label="نام کاربری جدید"><input name="username" required minLength={3} maxLength={40} dir="ltr" autoComplete="off"/></Field><Field label="گذرواژهٔ موقت"><input name="password" type="password" required minLength={12} maxLength={128} autoComplete="new-password" dir="ltr"/></Field><p className="muted">کاربر پس از اولین ورود باید گذرواژهٔ موقت را تغییر دهد و می‌تواند مشخصات فردی خود را تکمیل کند.</p></>}
    <Field label="وضعیت کاربر"><select name="status" defaultValue={editing?.status || 'active'}><option value="active">فعال</option><option value="disabled">غیرفعال</option></select></Field>
    <fieldset className="checks"><legend>نقش‌های کاربر</legend>{roles.data?.roles.map(role => <label className="check" key={role.id}><input type="checkbox" checked={selectedRoles.includes(role.id)} onChange={() => setSelectedRoles(toggle(selectedRoles, role.id))}/>{role.name}</label>)}</fieldset>
    <Field label="پرونده‌های مرتبط؛ برای ولی چند فرزند و برای دانش‌آموز فقط خود او"><select multiple value={studentIds} onChange={e => setStudentIds(Array.from(e.target.selectedOptions, o => o.value))}>{students.data?.students.map(s => <option key={s.id} value={s.id}>{s.name} · {s.code}</option>)}</select></Field>
    <Field label="کلاس‌های تخصیص‌یافتهٔ معلم"><select multiple value={classes} onChange={e => setClasses(Array.from(e.target.selectedOptions, o => o.value))}>{catalog.data?.classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}{classes.filter(id => !catalog.data?.classes.some(c => c.id === id)).map(id => <option key={id} value={id}>کلاس تخصیص‌یافته در سال دیگر</option>)}</select></Field>
  </FormCard><FormCard title="بازنشانی گذرواژهٔ کاربر" note="نشست‌های این کاربر باطل می‌شوند؛ تغییر گذرواژهٔ موقت در ورود بعدی الزامی است." onSave={async (values) => { await post('/users/reset-password', values); }}>
    <Field label="کاربر برای بازنشانی"><select name="userId" required defaultValue=""><option value="">انتخاب کنید…</option>{users.data?.users.filter(u => u.id !== user.id).map(u => <option key={u.id} value={u.id}>{u.display_name} · {u.username}</option>)}</select></Field>
    <Field label="گذرواژهٔ موقت جدید"><input name="password" type="password" required minLength={12} maxLength={128} autoComplete="new-password" dir="ltr"/></Field>
  </FormCard></div></>}
  {canRoles && <div className="two-columns"><Panel title="نقش‌های اصلی و اختصاصی"><Table head={['نام نقش', 'نوع', 'مجوزها', 'عملیات']}>{roles.data?.roles.map(role => <tr key={role.id}><td>{role.name}</td><td>{role.built_in ? 'اصلی' : 'اختصاصی'}</td><td>{role.permissions.length}</td><td>{!role.built_in && <button onClick={() => { setRoleEditing(role); setPermissions(role.permissions); }}>ویرایش نقش</button>}</td></tr>)}</Table></Panel>
    <FormCard key={roleEditing?.id || 'new-role'} title={roleEditing ? 'ویرایش نقش اختصاصی' : 'تعریف نقش جدید'} reset={false} onSave={async (values) => { await post('/roles', { ...values, ...(roleEditing ? { id: roleEditing.id } : {}), permissions }); await roles.refresh(); await onAccessChanged(); setRoleEditing(null); setPermissions([]); }}>
      {roleEditing && <button type="button" onClick={() => { setRoleEditing(null); setPermissions([]); }}>نقش جدید</button>}<Field label="نام نقش"><input name="name" required maxLength={80} defaultValue={roleEditing?.name || ''}/></Field>
      <fieldset className="checks permissions"><legend>مجوزهای نقش</legend>{Object.entries(roles.data?.permissions || {}).map(([id, label]) => <label className="check" key={id}><input type="checkbox" checked={permissions.includes(id)} onChange={() => setPermissions(toggle(permissions, id))}/>{label}</label>)}</fieldset>
    </FormCard></div>}</>;
}
