export class ApiError extends Error {
    constructor(message: string, readonly status: number) { super(message); }
}
async function request<T>(path: string, body?: object, signal?: AbortSignal): Promise<T> {
    const response = await fetch('/api/v1' + path, {
        method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', cache: 'no-store', signal,
        headers: body === undefined ? {} : { 'content-type': 'application/json', 'x-school-erp': '1' },
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data: unknown = await response.json();
    if (!response.ok) {
        const message = typeof data === 'object' && data && 'error' in data ? String(data.error) : 'عملیات انجام نشد.';
        throw new ApiError(message, response.status);
    }
    return data as T;
}
export const get = <T>(path: string, signal?: AbortSignal) => request<T>(path, undefined, signal);
export const post = <T = {
    ok: boolean;
}>(path: string, payload: object) => request<T>(path, payload);
export type PendingOperation = {
    path: string;
    payload: Record<string, unknown>;
};
const allowedOperations = new Set(['/finance/invoices', '/finance/receipts', '/years/copy', '/years/carry']);
const operationFields: Record<string, string[]> = {
    '/finance/invoices': ['studentId', 'title', 'amount', 'dueDate', 'yearId', 'fiscalYearId', 'postedOn'],
    '/finance/receipts': ['invoiceId', 'amount', 'reference', 'fiscalYearId', 'postedOn'],
    '/years/copy': ['sourceId', 'targetId', 'options', 'version'],
    '/years/carry': ['sourceId', 'targetId', 'studentIds', 'version'],
};
const pendingKey = (userId: string) => 'erp-school:pending:' + userId;
const notify = () => window.dispatchEvent(new Event('erp-pending'));
export function readPending(userId: string): PendingOperation | null {
    try {
        const value = JSON.parse(sessionStorage.getItem(pendingKey(userId)) || 'null') as PendingOperation | null;
        return value && allowedOperations.has(value.path) && value.payload && typeof value.payload.eventKey === 'string' ? value : null;
    }
    catch {
        return null;
    }
}
export function clearPending(userId: string) { sessionStorage.removeItem(pendingKey(userId)); notify(); }
/** Only non-secret financial/year commands are stored, scoped to this signed-in account. */
export async function runOperation(userId: string, path: string, values: Record<string, unknown>) {
    if (!allowedOperations.has(path))
        throw new Error('مسیر عملیات پشتیبانی نمی‌شود.');
    if (Object.keys(values).some(key => !operationFields[path].includes(key)))
        throw new Error('فیلد نامعتبر در عملیات قابل پیگیری است.');
    const pending = readPending(userId);
    if (pending)
        throw new Error('ابتدا نتیجهٔ عملیات نامشخص قبلی را از نوار بالای صفحه پیگیری کنید.');
    const operation = { path, payload: { ...values, eventKey: crypto.randomUUID() } };
    sessionStorage.setItem(pendingKey(userId), JSON.stringify(operation));
    notify();
    return resumeOperation(userId);
}
export async function resumeOperation(userId: string) {
    const pending = readPending(userId);
    if (!pending)
        return;
    try {
        const result = await post(pending.path, pending.payload);
        clearPending(userId);
        return result;
    }
    catch (error) {
        if (error instanceof ApiError && error.status < 500) {
            clearPending(userId);
            throw error;
        }
        throw new Error('پاسخ قطعی نرسید. برای جلوگیری از ثبت تکراری، فقط «پیگیری همان درخواست» را بزنید.');
    }
}
