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
- Added real create endpoints for customers, contacts, leads/opportunities, cases, tasks, and goals; frontend create modals now POST to FastAPI and insert the persisted response instead of using `local-*` records.
- Added backend regression coverage for resource creation across six business modules.
- Added PATCH/DELETE endpoints for customers, contacts, leads/opportunities, cases, tasks, and goals, including protected customer deletion when orders exist.
- Connected resource tables, boards, task cards, and goal cards to real edit/delete actions.
- Improved frontend API error parsing so backend `detail` messages are shown directly in the UI.
- Added `InventoryMovement` to persist order deductions and manual restock actions.
- Added `/api/inventory/restock-alerts`, `/api/inventory/movements`, and `/api/products/{product_id}/restock` for real inventory restock planning.
- Connected the Orders page to restock alerts, one-click restock actions, and recent inventory movement records.
- Added `/api/orders/export.csv` and an Orders page CSV export button for order-detail reporting.
- Added product catalog create/update/delete APIs with SKU uniqueness and delete protection for products referenced by orders or inventory movements.
- Added a real Products page backed by `/api/products`, so AI capture and order catalog data can be maintained in the app.
- Added persisted AI interaction audit logs for Copilot summary, follow-up generation, Copilot order drafts, and vision extraction.
- Added `/api/ai-audit-logs` and an AI Audit frontend page showing operation, LLM/fallback status, model, latency, request summary, and response summary.
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
- After resource create upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 10 passed.
- After AI audit upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 11 passed.
- After resource update/delete upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 12 passed.
- After inventory restock upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 14 passed, including insufficient-stock order protection.
- After order export upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 15 passed.
- After product catalog CRUD upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 16 passed.
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
  - `/ai-audit`: title `AI Audit | 深大 AI CRM`, 2 real LLM audit rows, 4 metrics, and no console errors.
- End-to-end AI Capture smoke succeeded: text upload returned `source=llm_text`, then `/api/orders` created order `#13`, total `37800`, with 2 items; demo DB was reset afterward.
- Real resource create smoke succeeded: POST create for customer, contact, lead, case, task, and goal returned server IDs/statuses; frontend customer modal created a persisted customer and updated the table to 13 rows; demo DB was reset afterward to 12/12/15/8/8/4/12 baseline.
- Real resource update/delete smoke succeeded on temporary port 8010: POST created customer `#13`, PATCH updated contact person and annual revenue, DELETE returned `deleted=true`; temporary records were removed afterward.
- Inventory restock smoke succeeded on temporary port 8011: `/api/inventory/restock-alerts` returned 5 alerts, `/api/products/{id}/restock` wrote a `manual_restock` movement, and the demo DB was reset afterward to 10 products and 22 seed movement records.
- Order export smoke succeeded on temporary port 8012: `/api/orders/export.csv` returned a CSV attachment with 23 lines, including the Chinese header and 22 order item rows.
- Product catalog smoke succeeded on temporary port 8013: product create, update, and delete succeeded for a temporary SKU, while deleting a seeded product returned 400 due to existing order or inventory records.
- AI audit smoke succeeded: Copilot summary and follow-up returned `fallback_used=false`, `/api/ai-audit-logs` returned 2 `llm` records, and the AI Audit page rendered the persisted rows.

## Next Steps

- Add order editing and stricter cross-module validation.
- Add table pagination, resource operation audit, and stricter field-level validation for larger demo datasets.
- Capture screenshots and export Word/PPT final materials.
