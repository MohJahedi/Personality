export type Preferences = {
    font: string;
    size: string;
    theme: string;
    accent: string;
};
export type User = {
    id: string;
    username: string;
    display_name: string;
    roles: string[];
    permissions: string[];
    must_change_password: boolean;
};
export type Context = {
    setupRequired: boolean;
    setupProtected: boolean;
    user: User | null;
    preferences: Preferences;
};
export type Year = {
    id: string;
    title: string;
    starts_on: string;
    ends_on: string;
    status: 'draft' | 'active' | 'closed';
};
export type Years = {
    academicYears: Year[];
    fiscalYears: Year[];
};
export type Grade = {
    id: string;
    name: string;
    position: number;
};
export type Subject = {
    id: string;
    name: string;
};
export type Classroom = {
    id: string;
    academic_year_id: string;
    grade_id: string;
    name: string;
    capacity: number;
};
export type Teacher = {
    id: string;
    name: string;
};
export type Period = {
    id: string;
    academic_year_id: string;
    grade_id: string;
    weekday: number;
    number: number;
    starts_at: string;
    ends_at: string;
};
export type Catalog = {
    grades: Grade[];
    subjects: Subject[];
    gradeSubjects: {
        grade_id: string;
        subject_id: string;
    }[];
    classes: Classroom[];
    teachers: Teacher[];
    periods: Period[];
};
export type Student = {
    id: string;
    name: string;
    code: string;
    guardian_name: string;
    guardian_phone: string;
    class_id: string | null;
    grade_id: string | null;
    enrolled_class: string | null;
};
export type Balance = {
    id: string;
    name: string;
    code: string;
    invoice_id: string;
    title: string;
    amount: number;
    paid: number;
    remaining: number;
    opening_amount: number;
};
export type Balances = {
    balances: Balance[];
    total: number;
    openingSnapshot: number;
};
export type Invoice = {
    id: string;
    student_id: string;
    student_name: string;
    title: string;
    amount: number;
    paid: number;
    due_date: string;
    academic_year_id: string | null;
};
export type Receipt = {
    id: string;
    invoice_id: string;
    student_name: string;
    invoice_title: string;
    amount: number;
    reference: string;
    created_at: string;
};
export type Journal = {
    id: string;
    description: string;
    student_name: string;
    debit_account: string;
    credit_account: string;
    amount: number;
    fiscal_year_id: string | null;
    posted_on: string | null;
};
export type Finance = {
    students: Student[];
    invoices: Invoice[];
    receipts: Receipt[];
    journals: Journal[];
};
export type Timetable = {
    id: string;
    class_id: string;
    period_id: string;
    subject_id: string;
    teacher_id: string | null;
    weekday: number;
    number: number;
    starts_at: string;
    ends_at: string;
    class_name: string;
    subject_name: string;
    teacher_name: string;
};
export type Profile = {
    name: string;
    username: string;
    first_name: string;
    last_name: string;
    phone: string;
    email: string;
};
export type Role = {
    id: string;
    name: string;
    permissions: string[];
    built_in: number;
};
export type ManagedUser = {
    id: string;
    username: string;
    display_name: string;
    status: string;
    roles: string[];
    studentIds: string[];
    classIds: string[];
};
