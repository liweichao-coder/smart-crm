# 2026-06-23 Pipeline stage board actions

## Goal

The lead and opportunity board should behave like a real CRM pipeline. Moving a card between stages should update the backend lead stage, pass organization and owner permission checks, and write the normal business audit trail through the existing PATCH endpoint.

## Changes

- Added `updateLeadStage()` so the frontend can PATCH only `{ stage }` instead of resubmitting a full lead form payload.
- Upgraded `BoardResourcePage` with complete pipeline columns, drag-and-drop card movement, and explicit previous/next stage buttons.
- Connected the Leads and Opportunities pages to real stage updates through `/api/leads/{id}`.
- Added the missing backend `contacted` stage so frontend display labels, payload normalization, backend enum validation, sales reports, and Copilot scoring use the same pipeline model.
- Added board display label normalization tests to prevent `New/Qualified/Proposal/...` from drifting away from backend enum values.

## Verification

- `npm run lint`: passed.
- `npm test -- --run`: 50 passed.
- `npm run build`: passed.
- `backend/.venv/Scripts/python.exe -m pytest`: 55 passed.
- `backend/.venv/Scripts/python.exe -m app.manage doctor`: environment ready, consistency ok / issues 0.
- Rebuilt affected formal report DOCX files: 02, 04, 05, 06, 07, 08.
- Exported the rebuilt DOCX files to PDF with Microsoft Word COM and generated contact-sheet visual evidence under `报告文档/v2-最终高分版/正式文档/验收证据/docx-render-word-2026-06-23-pipeline/`.

LibreOffice 26.2 is currently blocked on this machine by a damaged `C:\Program Files\LibreOffice\program\bootstrap.ini` startup configuration, so this round used Microsoft Word export for visual QA instead of LibreOffice.

## Report Impact

- Updated v2 API, implementation, user manual, iteration summary, and testing documents with real pipeline stage movement and the `contacted` stage closure.
