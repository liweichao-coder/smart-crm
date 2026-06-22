# 2026-06-22 AI Copilot and Report Upgrade

## Context

The course exam requires a full software engineering process package, not only code. The project is being upgraded from a basic Smart CRM with AI order draft support into an AI Sales Copilot CRM benchmarked against CordysCRM concepts.

## Code Changes

- Added `src/aiScoring.js` for explainable opportunity scoring.
- Added `src/aiScoring.test.js` and included it in `npm test`.
- Added an AI Copilot navigation entry and page in `src/App.jsx`.
- Added AI Copilot UI styles in `src/index.css`.
- Added backend `/api/copilot/summary`, `/api/copilot/follow-up`, and `/api/copilot/order-draft`.
- Added OpenAI-compatible LLM configuration and verified DeepSeek responses with `fallback_used=false`.
- Added `python -m app.manage reset-db` for repeatable demo database initialization.
- Added real backend models and list APIs for contacts, support cases, task items, and sales goals.
- Expanded demo data to 12 customers, 10 products, 12 contacts, 15 leads/opportunities, 8 cases, 8 tasks, 4 goals, 12 seeded orders, and 22 persisted order items with stock deduction.
- Connected frontend customer, contact, lead, opportunity, case, task, and goal pages to real REST APIs instead of static mock records.
- Connected dashboard summary widgets to `/api/dashboard`, `/api/leads`, `/api/tasks`, and `/api/goals`, replacing the remaining static dashboard mock data.
- Replaced deterministic AI capture samples with `/api/vision-extract` real upload parsing: image inputs use OpenAI-compatible multimodal messages when configured; text uploads use local extraction against the CRM customer/product catalog.
- Added the frontend AI Capture page for uploading order images or text and reviewing extracted draft items.
- Connected AI Capture draft review to `/api/orders`, so accepted drafts create real orders and trigger backend inventory deduction.
- Added a dedicated Orders page backed by `/api/orders` and `/api/products`, including order filters, selected order details, AI/manual source badges, and low-stock inventory cards.
- Added `src/orderUtils.js` and tests for order summary, filtering, and inventory severity logic.
- Refreshed the UI toward a cleaner light CRM workspace and replaced the original mark with a Shenzhen University-style `深` emblem for course presentation packaging.

## Report Changes

- Created `报告文档/v2-最终高分版/`.
- Added final report drafts for requirements, product design, database, API, implementation, user manual, iteration summary, testing, and presentation.
- Added root `AGENTS.md` for future AI agents.

## Verification To Run

- `npm run lint`
- `npm test`
- `npm run build`
- `backend/.venv/Scripts/python.exe -m pytest`
- Manual Copilot smoke: `/api/copilot/summary` and `/api/copilot/follow-up`

## Verification Completed

- `backend/.venv/Scripts/python.exe -m pytest`: 7 passed.
- After AI capture upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 9 passed.
- `npm run lint`: passed.
- `npm test`: 16 passed.
- `npm run build`: passed.
- Demo database reset succeeded with 12 customers, 10 products, 12 contacts, 15 leads/opportunities, 8 cases, 8 tasks, 4 goals, 12 seeded orders, and 22 order items.
- DeepSeek OpenAI-compatible smoke succeeded: summary and follow-up returned `fallback_used=false`.
- Browser smoke succeeded at `/copilot`: backend leads loaded and follow-up generation updated the UI.
- Browser DOM smoke succeeded for real resource pages:
  - `/accounts`: 12 rows, brand mark `深`.
  - `/contacts`: 12 rows.
  - `/leads`: 15 rows.
  - `/cases`: 8 rows.
  - `/tasks`: 8 cards.
  - `/goals`: 4 cards.
  - `/dashboard`: metrics, focus strip, stage cards, tasks, opportunities, goals, and activities render from backend payloads.
  - `/capture`: upload UI calls `/api/vision-extract` and displays extracted customer, confidence, source, and order items.
  - `/orders`: title `Orders | 深大 AI CRM`, 12 backend orders, 4 metrics, and 6 low-stock inventory cards render without console errors.
- End-to-end AI Capture smoke succeeded: text upload returned `source=llm_text`, then `/api/orders` created order `#13`, total `37800`, with 2 items; demo DB was reset afterward.

## Next Steps

- Add order editing/export and inventory restock reminders.
- Capture screenshots and export Word/PPT final materials.
