# 2026-06-23 UI Smoke Runner

## Context

The backend already had pytest, `doctor`, `/api/health`, and a repeatable API smoke script. The remaining handoff gap was browser-level verification: teammates still needed to manually prove login, organization selection, dashboard rendering, resource pages, and the custom delete confirmation before classroom demos.

## Changes

- Added `scripts/smoke_ui.mjs`, a Playwright-based browser smoke runner.
- Added `npm run smoke:ui`.
- The smoke runner checks `/api/health`, logs in through the real form, selects the backend-provided organization, verifies dashboard metrics, account rows, report and order pages, no horizontal overflow, no native browser dialogs, and the 8px in-app delete confirmation dialog.
- The delete check clicks cancel, so the default smoke does not mutate demo data.
- Added an optional `--include-ai-page` flag for teams that want to include the AI Copilot page and accept possible LLM/recommendation writes.

## Verification

- `npm run smoke:ui -- --frontend-url http://127.0.0.1:5184 --api-url http://127.0.0.1:8041 --timeout 20000` passed against temporary local backend/frontend services.
- The smoke confirmed readiness, login style, real login plus organization selection, dashboard metrics, account table rows, the custom delete confirmation cancel flow, sales reports, orders, no native dialogs/page errors/console errors, and UI logout.
- The normal regression gate is run before commit: `npm run lint`, `npm test -- --run`, `npm run build`, backend `pytest`, and `python -m app.manage doctor`.
