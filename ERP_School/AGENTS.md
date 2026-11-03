# ERP_School engineering rules

This is the formal, modular successor to the real v0.3 pilot. The personal
homepage, existing preview, default branch and Pages configuration are outside
this project's editing scope. Do not merge or deploy this work automatically.

## Product decisions

- One independent installation and SQLite database per school. Never silently
  convert this edition into a shared multi-school database.
- Receivables belong to each student; a guardian may view multiple explicitly
  linked children. Student accounts see only their own linked record.
- Academic and fiscal years have independent dates and state. Academic carry-over
  references an existing claim and never duplicates an invoice or journal.
- A grade has a variable number of periods for each weekday. Timetable writes
  must reject teacher overlap, invalid subject/grade and wrong year/class links.
- Real web-font assets and their licenses must accompany all font choices.
  Five fonts, three sizes, five themes and a custom accent are the current minimum.

## Code boundaries

- Keep HTTP/cookie handling in `backend/erp_school/http`; business modules do not
  import transport or application composition code.
- Keep accounting domain rules independent of students, the UI and database.
  The current persistence adapter still stores two-sided pairs; do not claim
  full independent accounting has been completed.
- Use one transaction for each business command. Modules do not commit their
  own side effects. A failed journal, copy, schedule or transfer rolls back all
  related writes.
- Browser views use `frontend/shared/api.ts`. Permission checks in the UI are
  presentation only; server permissions and row scopes remain authoritative.
- Keep components and services focused. Use strict TypeScript, named helpers,
  descriptive fields and explicit error states. Avoid adding framework or
  infrastructure layers without a concrete need.

## Quality gates for every feature

Use `docs/QUALITY-GATES.fa.md` and the feature template before marking a feature
done. Record UI, UX, DBA, DevOps, CTO and QA evidence separately. Review roles are
not proof that human specialists have approved the work. Unrun checks remain open.

- Run `pnpm check` after relevant changes. Preserve API regression tests and add
  meaningful negative, permission, rollback, replay and concurrency coverage.
- Check responsive UI at 320, 390, 820 and 1440 CSS pixels and all three sizes.
  Tables scroll locally; controls remain usable by touch and keyboard.
- Use immutable, ordered migrations after a schema version is published. Test
  migration, a private pre-migration backup and restore. Do not rewrite user data.
- Keep money in integer rial. Display toman explicitly. Never use floats for
  stored financial values or add carry-over snapshots to the original debt total.
- Do not store or log passwords, session tokens, cookies or invitation codes.
- A lost mutation response is unknown, not failed. Retry the exact same financial
  or year command with its original idempotency key.

## Release boundary

`pnpm build` produces the real client. `scripts/ui-stories.py --synthetic-api`
creates visibly labeled UI stories only in ignored build output. These stories
do not authenticate against the backend and must never ship in a release.
Before packaging, run a normal build to remove them. Do not create real school
accounts, use actual child data or claim production readiness during development.
