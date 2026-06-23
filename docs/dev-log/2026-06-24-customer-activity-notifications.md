# 2026-06-24 Customer activity notifications

## Goal

Customer activities and pipeline stage movement already persist into the customer 360 workspace. This iteration makes their next actions operational by surfacing unconverted customer activities in the notification center.

## Changes

- `/api/notifications` now aggregates `CustomerActivity` records with a non-empty `next_action`.
- Activities are organization- and owner-scoped through the existing backend filters.
- Activities already converted to tasks are skipped, so the notification center does not duplicate work after a real task exists.
- The notification loop filters empty or converted activities before applying the eight-item cap, so older actionable activities are not hidden behind non-actionable records.
- Risk or negative activities are shown as warning notifications; neutral and positive activities are informational.
- Notifications link back to the customer workspace and use `entity_type=customer_activity`.

## Verification

- Targeted pytest passed: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_api.py -k notifications_are_data_driven`.
- Full frontend and backend verification passed:
  - `npm run lint`
  - `npm test -- --run` (50 tests)
  - `backend/.venv/Scripts/python.exe -m pytest` (56 tests)
  - `npm run build`
  - `backend/.venv/Scripts/python.exe -m app.manage doctor` from the `backend/` directory
- Report DOCX verification passed:
  - Rebuilt 01-09 DOCX drafts with `scripts/build_report_docx.py`.
  - Confirmed key terms in `word/document.xml` for every rebuilt DOCX.
  - Exported 01-09 DOCX to PDF with Microsoft Word and rendered contact sheets with Poppler under `报告文档/v2-最终高分版/正式文档/验收证据/docx-render-word-2026-06-24-activity-notifications/`.
  - LibreOffice was not used because the local `bootstrap.ini` is currently damaged.

## Report Impact

- Updated notification center descriptions, database/interface/implementation docs, user manual, iteration summary, testing document, PPT script, and final DOCX drafts to include customer-activity next-action reminders.
