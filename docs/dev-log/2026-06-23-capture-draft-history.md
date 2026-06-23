# 2026-06-23 Capture draft history

## Goal

AI Capture should not lose extracted drafts when the user leaves the page or delays order submission. The extraction result now becomes a persisted CRM review artifact before it becomes a real order.

## Changes

- Added `CaptureDraft` with organization, creator, source, confidence, matched customer/product IDs, item JSON, status, and submitted order linkage.
- `/api/vision-extract` now persists a draft and returns `capture_draft_id`.
- Added `GET /api/vision-extract/drafts` for paginated draft history.
- Added `PATCH /api/vision-extract/drafts/{id}` to mark drafts as `submitted` or `discarded`; submitted drafts must reference a real order.
- The AI Capture page now displays recent drafts, can reload a draft for review, and marks the draft submitted after order creation.

## Verification

- `npm run lint`: passed.
- `npm test -- --run`: 48 passed.
- `npm run build`: passed.
- `backend/.venv/Scripts/python.exe -m pytest`: 54 passed.
- `backend/.venv/Scripts/python.exe -m app.manage doctor`: demo environment ready, consistency status ok, 0 issues.
- Rebuilt DOCX reports 03-08 from the updated Markdown drafts.
- LibreOffice headless rendering was skipped because the local LibreOffice `bootstrap.ini` is damaged. Used Microsoft Word COM export plus `pypdfium2` overview rendering instead: reports 03-08 exported to PDF, 121 pages total, no likely blank pages in the rendered overview sheets.

## Report Impact

- Updated README and v2 database/API/implementation/manual/iteration/testing documents. Rebuilt 03-08 DOCX after full verification.
