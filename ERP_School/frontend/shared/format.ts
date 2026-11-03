export const number = (value: number) => value.toLocaleString('fa-IR');
export const money = (rial: number) => number(rial / 10);
export const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Tehran', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
export const date = (value: string) => new Intl.DateTimeFormat('fa-IR', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'Asia/Tehran' }).format(new Date(value.length === 10 ? value + 'T12:00:00Z' : value));
export const weekdays = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه'];
export const statuses: Record<string, string> = { draft: 'پیش‌نویس', active: 'فعال', closed: 'بسته', disabled: 'غیرفعال' };
export function exportCsv(name: string, rows: (string | number)[][]) {
    const csv = '\uFEFF' + rows.map(row => row.map(value => '"' + String(value).replace(/^[=+@-]/, "'$&").replace(/"/g, '""') + '"').join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = name + '.csv';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}
