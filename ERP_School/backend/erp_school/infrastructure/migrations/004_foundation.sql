BEGIN IMMEDIATE;
CREATE TABLE roles(id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, permissions TEXT NOT NULL, built_in INTEGER NOT NULL DEFAULT 0 CHECK(built_in IN (0,1)));
CREATE TABLE user_roles(user_id TEXT NOT NULL REFERENCES local_users(id), role_id TEXT NOT NULL REFERENCES roles(id), PRIMARY KEY(user_id,role_id));
CREATE TABLE user_profiles(user_id TEXT PRIMARY KEY REFERENCES local_users(id), first_name TEXT NOT NULL DEFAULT '', last_name TEXT NOT NULL DEFAULT '', phone TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '');
CREATE TABLE user_security(user_id TEXT PRIMARY KEY REFERENCES local_users(id), must_change_password INTEGER NOT NULL DEFAULT 0 CHECK(must_change_password IN (0,1)));
CREATE TABLE user_student_scopes(user_id TEXT NOT NULL REFERENCES local_users(id), student_id TEXT NOT NULL REFERENCES students(id), PRIMARY KEY(user_id,student_id));
CREATE TABLE user_class_scopes(user_id TEXT NOT NULL REFERENCES local_users(id), class_name TEXT NOT NULL, PRIMARY KEY(user_id,class_name));
CREATE TABLE user_preferences(user_id TEXT PRIMARY KEY REFERENCES local_users(id), font TEXT NOT NULL, size TEXT NOT NULL, theme TEXT NOT NULL, accent TEXT NOT NULL);
CREATE TABLE academic_years(id TEXT PRIMARY KEY, title TEXT NOT NULL UNIQUE, starts_on TEXT NOT NULL, ends_on TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','active','closed')), CHECK(starts_on<=ends_on));
CREATE UNIQUE INDEX one_active_academic_year ON academic_years(status) WHERE status='active';
CREATE TABLE fiscal_years(id TEXT PRIMARY KEY, title TEXT NOT NULL UNIQUE, starts_on TEXT NOT NULL, ends_on TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','active','closed')), CHECK(starts_on<=ends_on));
CREATE UNIQUE INDEX one_active_fiscal_year ON fiscal_years(status) WHERE status='active';
CREATE TABLE grades(id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, position INTEGER NOT NULL DEFAULT 1 CHECK(position>0));
CREATE TABLE subjects(id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE grade_subjects(grade_id TEXT NOT NULL REFERENCES grades(id), subject_id TEXT NOT NULL REFERENCES subjects(id), PRIMARY KEY(grade_id,subject_id));
CREATE TABLE classes(id TEXT PRIMARY KEY, academic_year_id TEXT NOT NULL REFERENCES academic_years(id), grade_id TEXT NOT NULL REFERENCES grades(id), name TEXT NOT NULL, capacity INTEGER NOT NULL DEFAULT 30 CHECK(capacity BETWEEN 1 AND 100), UNIQUE(academic_year_id,name), UNIQUE(id,academic_year_id,grade_id));
CREATE TABLE user_class_assignments(user_id TEXT NOT NULL REFERENCES local_users(id), class_id TEXT NOT NULL REFERENCES classes(id), PRIMARY KEY(user_id,class_id));
CREATE TABLE teachers(id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '');
CREATE TABLE guardians(id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '');
CREATE TABLE student_guardians(student_id TEXT NOT NULL REFERENCES students(id), guardian_id TEXT NOT NULL REFERENCES guardians(id), PRIMARY KEY(student_id,guardian_id));
INSERT INTO guardians(id,name,phone) SELECT 'legacy-guardian:'||id,guardian_name,guardian_phone FROM students;
INSERT INTO student_guardians(student_id,guardian_id) SELECT id,'legacy-guardian:'||id FROM students;
CREATE TABLE year_teachers(academic_year_id TEXT NOT NULL REFERENCES academic_years(id), teacher_id TEXT NOT NULL REFERENCES teachers(id), PRIMARY KEY(academic_year_id,teacher_id));
CREATE TABLE year_guardians(academic_year_id TEXT NOT NULL REFERENCES academic_years(id), guardian_id TEXT NOT NULL REFERENCES guardians(id), PRIMARY KEY(academic_year_id,guardian_id));
CREATE TABLE enrollments(academic_year_id TEXT NOT NULL REFERENCES academic_years(id), student_id TEXT NOT NULL REFERENCES students(id), grade_id TEXT NOT NULL REFERENCES grades(id), class_id TEXT REFERENCES classes(id), PRIMARY KEY(academic_year_id,student_id), FOREIGN KEY(class_id,academic_year_id,grade_id) REFERENCES classes(id,academic_year_id,grade_id));
CREATE INDEX enrollments_class ON enrollments(class_id,student_id);
CREATE TABLE day_periods(id TEXT PRIMARY KEY, academic_year_id TEXT NOT NULL REFERENCES academic_years(id), grade_id TEXT NOT NULL REFERENCES grades(id), weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6), number INTEGER NOT NULL CHECK(number BETWEEN 1 AND 12), starts_at TEXT NOT NULL, ends_at TEXT NOT NULL, UNIQUE(academic_year_id,grade_id,weekday,number), UNIQUE(id,academic_year_id,grade_id), CHECK(starts_at<ends_at));
CREATE TABLE timetable(id TEXT PRIMARY KEY, academic_year_id TEXT NOT NULL, grade_id TEXT NOT NULL, class_id TEXT NOT NULL, period_id TEXT NOT NULL, subject_id TEXT NOT NULL, teacher_id TEXT, UNIQUE(class_id,period_id), FOREIGN KEY(class_id,academic_year_id,grade_id) REFERENCES classes(id,academic_year_id,grade_id), FOREIGN KEY(period_id,academic_year_id,grade_id) REFERENCES day_periods(id,academic_year_id,grade_id), FOREIGN KEY(grade_id,subject_id) REFERENCES grade_subjects(grade_id,subject_id), FOREIGN KEY(academic_year_id,teacher_id) REFERENCES year_teachers(academic_year_id,teacher_id));
CREATE INDEX timetable_teacher ON timetable(teacher_id,period_id);
CREATE TABLE invoice_years(invoice_id TEXT PRIMARY KEY REFERENCES invoices(id), academic_year_id TEXT NOT NULL REFERENCES academic_years(id));
CREATE TABLE journal_periods(journal_id TEXT PRIMARY KEY REFERENCES journals(id), fiscal_year_id TEXT NOT NULL REFERENCES fiscal_years(id), posted_on TEXT NOT NULL);
CREATE INDEX journal_period_lookup ON journal_periods(fiscal_year_id,posted_on);
CREATE INDEX invoice_year_lookup ON invoice_years(academic_year_id,invoice_id);
CREATE TABLE carried_claims(source_year_id TEXT NOT NULL REFERENCES academic_years(id), target_year_id TEXT NOT NULL REFERENCES academic_years(id), invoice_id TEXT NOT NULL REFERENCES invoices(id), opening_amount INTEGER NOT NULL CHECK(opening_amount>0), created_at TEXT NOT NULL, PRIMARY KEY(target_year_id,invoice_id), CHECK(source_year_id<>target_year_id));
CREATE TABLE completed_operations(event_key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TRIGGER invoice_amount_guard BEFORE INSERT ON invoices
WHEN typeof(NEW.amount)<>'integer' OR NEW.amount<=0
BEGIN SELECT RAISE(ABORT,'invalid invoice amount'); END;
CREATE TRIGGER invoice_amount_update_guard BEFORE UPDATE OF amount ON invoices
WHEN typeof(NEW.amount)<>'integer' OR NEW.amount<=0 OR NEW.amount<COALESCE((SELECT SUM(amount) FROM receipts WHERE invoice_id=NEW.id AND owner=NEW.owner),0)
BEGIN SELECT RAISE(ABORT,'invalid invoice amount'); END;
CREATE TRIGGER receipt_balance_guard BEFORE INSERT ON receipts
WHEN typeof(NEW.amount)<>'integer' OR NEW.amount<=0 OR NOT EXISTS(SELECT 1 FROM invoices WHERE id=NEW.invoice_id AND owner=NEW.owner)
OR NEW.amount+COALESCE((SELECT SUM(amount) FROM receipts WHERE invoice_id=NEW.invoice_id AND owner=NEW.owner),0)>(SELECT amount FROM invoices WHERE id=NEW.invoice_id AND owner=NEW.owner)
BEGIN SELECT RAISE(ABORT,'invalid receipt balance'); END;
CREATE TRIGGER receipt_balance_update_guard BEFORE UPDATE OF amount,invoice_id,owner ON receipts
WHEN typeof(NEW.amount)<>'integer' OR NEW.amount<=0 OR NOT EXISTS(SELECT 1 FROM invoices WHERE id=NEW.invoice_id AND owner=NEW.owner)
OR NEW.amount+COALESCE((SELECT SUM(amount) FROM receipts WHERE invoice_id=NEW.invoice_id AND owner=NEW.owner AND id<>NEW.id),0)>(SELECT amount FROM invoices WHERE id=NEW.invoice_id AND owner=NEW.owner)
BEGIN SELECT RAISE(ABORT,'invalid receipt balance'); END;
CREATE TRIGGER journal_amount_guard BEFORE INSERT ON journals
WHEN typeof(NEW.amount)<>'integer' OR NEW.amount<=0 OR NEW.debit_account=NEW.credit_account
BEGIN SELECT RAISE(ABORT,'invalid journal amount'); END;
PRAGMA user_version=4;
COMMIT;
