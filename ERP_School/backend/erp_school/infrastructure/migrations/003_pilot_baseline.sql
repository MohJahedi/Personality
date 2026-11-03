CREATE TABLE `attendance` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`student_id` text NOT NULL,
	`day` text NOT NULL,
	`status` text NOT NULL,
	`updated_at` text NOT NULL,
	FOREIGN KEY (`student_id`) REFERENCES `students`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `attendance_student_day` ON `attendance` (`owner`,`student_id`,`day`);--> statement-breakpoint
CREATE TABLE `audit` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`role` text NOT NULL,
	`action` text NOT NULL,
	`target` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `audit_owner` ON `audit` (`owner`);--> statement-breakpoint
CREATE TABLE `invoices` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`student_id` text NOT NULL,
	`title` text NOT NULL,
	`amount` integer NOT NULL,
	`due_date` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`student_id`) REFERENCES `students`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `invoices_owner_student` ON `invoices` (`owner`,`student_id`);--> statement-breakpoint
CREATE TABLE `journals` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`student_id` text NOT NULL,
	`event_id` text NOT NULL,
	`event_type` text NOT NULL,
	`description` text NOT NULL,
	`debit_account` text NOT NULL,
	`credit_account` text NOT NULL,
	`amount` integer NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`student_id`) REFERENCES `students`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `journals_owner_event` ON `journals` (`owner`,`event_id`);--> statement-breakpoint
CREATE INDEX `journals_owner` ON `journals` (`owner`);--> statement-breakpoint
CREATE TABLE `receipts` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`invoice_id` text NOT NULL,
	`amount` integer NOT NULL,
	`method` text NOT NULL,
	`reference` text NOT NULL,
	`event_key` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `receipts_owner_event` ON `receipts` (`owner`,`event_key`);--> statement-breakpoint
CREATE INDEX `receipts_owner_invoice` ON `receipts` (`owner`,`invoice_id`);--> statement-breakpoint
CREATE TABLE `students` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`name` text NOT NULL,
	`code` text NOT NULL,
	`class_name` text NOT NULL,
	`guardian_name` text NOT NULL,
	`guardian_phone` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `students_owner_code` ON `students` (`owner`,`code`);--> statement-breakpoint
CREATE INDEX `students_owner` ON `students` (`owner`);--> statement-breakpoint
CREATE TABLE `workspaces` (
	`owner` text PRIMARY KEY NOT NULL,
	`title` text NOT NULL,
	`academic_year` text NOT NULL,
	`parent_student_id` text NOT NULL,
	`created_at` text NOT NULL
);

CREATE TABLE `invitations` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`token_hash` text NOT NULL,
	`role` text NOT NULL,
	`label` text NOT NULL,
	`class_name` text,
	`student_id` text,
	`expires_at` text NOT NULL,
	`revoked` integer DEFAULT 0 NOT NULL,
	`used_by` text,
	`created_at` text NOT NULL,
	FOREIGN KEY (`student_id`) REFERENCES `students`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `invitations_token_hash` ON `invitations` (`token_hash`);--> statement-breakpoint
CREATE INDEX `invitations_owner` ON `invitations` (`owner`);--> statement-breakpoint
CREATE TABLE `memberships` (
	`user_id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`role` text NOT NULL,
	`display_name` text NOT NULL,
	`email` text NOT NULL,
	`status` text NOT NULL,
	`class_name` text,
	`student_id` text,
	`invite_id` text,
	`created_at` text NOT NULL,
	FOREIGN KEY (`student_id`) REFERENCES `students`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `memberships_owner` ON `memberships` (`owner`);
CREATE TABLE local_users(id TEXT PRIMARY KEY,username TEXT NOT NULL UNIQUE,display_name TEXT NOT NULL,password_hash TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE local_sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES local_users(id),expires_at INTEGER NOT NULL);
CREATE INDEX local_sessions_user ON local_sessions(user_id);
CREATE TABLE login_limits(key TEXT PRIMARY KEY,failures INTEGER NOT NULL,until_at INTEGER NOT NULL);
PRAGMA user_version=3;
