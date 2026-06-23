# 2026-06-24 Capture draft lifecycle

## Goal

AI Capture already created persisted `CaptureDraft` records and could mark submitted drafts after order creation. This iteration closes the operator workflow so draft history is not just a read-only evidence list.

## Changes

- Added status tabs on the AI Capture page for draft, submitted, discarded, and all records.
- Added a real discard action for draft records, backed by `PATCH /api/vision-extract/drafts/{draft_id}` with `status=discarded`.
- Loading a submitted or discarded draft now locks the order-submit action and explains why it cannot be submitted again.
- Uploading a new file returns the page to the draft filter so the newly persisted draft is visible.
- Submitted drafts are removed from the draft filter after a successful order submission.

## Verification

- Targeted frontend API helper test passed: `npm test -- --run src/api.test.js`.
- Targeted backend pytest passed: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_api.py -k capture_draft_history_marks_submitted_order`.
- Full verification passed:
  - `npm run lint`
  - `npm test -- --run` (50 tests)
  - `backend/.venv/Scripts/python.exe -m pytest` (56 tests)
  - `npm run build`
  - `backend/.venv/Scripts/python.exe -m app.manage doctor` from the `backend/` directory
- Report DOCX verification passed:
  - Rebuilt the affected DOCX drafts with `scripts/build_report_docx.py`.
  - Confirmed draft lifecycle keywords inside the rebuilt DOCX files.
  - Exported the affected DOCX files to PDF with Microsoft Word and rendered contact sheets under `报告文档/v2-最终高分版/正式文档/验收证据/docx-render-word-2026-06-24-capture-lifecycle/`.

## Report Impact

- Update Smart CRM reports and user manual to describe AI Capture draft lifecycle management: draft review, status filters, submitted linkage, discarded records, and duplicate-submit prevention.
