# 2026-06-24 Pipeline stage activity timeline

## Goal

The pipeline board already persists lead stage movement through the backend. This iteration makes the movement visible in customer operations: when a lead or opportunity changes stage, the backend creates a real customer activity so the customer 360 workspace, timeline, health profile, and business audit all reflect the sales touchpoint.

## Changes

- Added backend helpers to match a lead to a customer within the same organization by customer aliases.
- Added automatic `CustomerActivity` creation when `PATCH /api/leads/{id}` changes `stage`.
- The generated activity records the previous stage, next stage, opportunity amount, next action, owner, sentiment, and organization.
- Non-stage lead edits still update the lead without creating extra timeline activity.
- Business audit now records the generated customer activity as a real create action.

## Verification

- Targeted pytest passed: `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_api.py -k "lead_stage_update_creates_customer_activity_timeline or update_and_delete_business_resources"`.
- `npm run lint`: passed.
- `npm test -- --run`: 50 passed.
- `npm run build`: passed.
- `backend/.venv/Scripts/python.exe -m pytest`: 56 passed.
- `backend/.venv/Scripts/python.exe -m app.manage doctor`: environment ready, consistency ok / issues 0.
- Rebuilt affected formal report DOCX files: 02, 03, 04, 05, 06, 07, 08, 09.
- Exported the rebuilt DOCX files to PDF with Microsoft Word COM and generated contact-sheet evidence under `报告文档/v2-最终高分版/正式文档/验收证据/docx-render-word-2026-06-24-pipeline-timeline/`.

## Report Impact

- Update product design, backend API, implementation, user manual, iteration summary, and testing documents to explain that pipeline stage movement feeds the customer 360 timeline.
