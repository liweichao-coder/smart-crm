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
- Added `PATCH /api/orders/{order_id}` for order lifecycle fields: owner, region, status, due date, and notes.
- Added an Orders page edit modal so the selected order can be maintained from the frontend without leaving the order detail panel.
- Extended order PATCH to accept order items, recalculate order totals, and write `order_adjustment` inventory movements for stock deltas.
- Added an order item editor in the Orders modal with product selection, quantity, price, line totals, and recalculated order total.
- Added `GET /api/orders/{order_id}/inventory-movements` and a selected-order inventory audit panel in the Orders page.
- Added `BusinessAuditLog`, `/api/business-audit-logs`, and a Business Audit frontend page for customer, product, order, and restock write actions.
- Expanded `BusinessAuditLog` coverage to contacts, leads/opportunities, support cases, tasks, and sales goals.
- Added backward-compatible pagination, search, and business filters for resource, order, inventory movement, AI audit, and business audit list APIs.
- Updated the frontend API layer and remote-record hook so current pages keep using array responses while future pages can consume paginated `{ items, total, page }` responses.
- Added real authentication tables and APIs: organization registration, PBKDF2 password hashing, login, Bearer token sessions, `/api/auth/me`, logout, and auth audit logs.
- Connected frontend login/register routes to the backend auth APIs, persisted the session token, attached `Authorization` headers to API requests, and protected workspace routes client-side.
- Added server-side RBAC permission policies for business APIs, including 401 for unauthenticated access and 403 for roles without catalog or audit permissions.
- Added permission-aware frontend navigation so users only see modules allowed by the permission list returned from `/api/auth/me`.
- Added root `pytest.ini` so backend tests can be run from the repository root with `backend/.venv/Scripts/python.exe -m pytest`.
- Added real sales BI reporting with `/api/reports/sales-performance`, `reports:read` permission, and a frontend Reports page for revenue trend, owner/region performance, sales funnel, AI revenue impact, and inventory risks.
- Added real permission matrix governance with `/api/admin/permission-matrix`, `permissions:read` permission, and a frontend Permissions page backed by backend RBAC policy constants.
- Added persisted Copilot recommendation history with `CopilotRecommendation`, `/api/copilot/recommendations`, and a Copilot page history panel showing summary suggestions, follow-up drafts, scores, model mode, and fallback status.
- Added Copilot recommendation-to-task conversion with `/api/copilot/recommendations/{id}/task`; it creates a real task, updates the linked lead's next action, and writes business audit logs.
- Added a data-driven notification center with `/api/notifications` and a real topbar bell panel for overdue/today tasks, inventory risk, key opportunities, Copilot actions, and AI fallback calls.
- Added owner data-scope enforcement for sales users across contacts, leads/opportunities, cases, tasks, orders, dashboard metrics, notifications, and Copilot recommendation flows. `/api/auth/me` and `/api/admin/permission-matrix` now expose `data_scope` so the frontend can explain all-data vs own-data access.
- Added a real order approval workflow with `OrderApprovalRequest`, `/api/order-approvals`, `/api/orders/{id}/approval-requests`, `/api/order-approvals/{id}/decision`, seeded pending/approved approval records, order-center approval actions, `approval:manage` permission, notification-center approval reminders, and business audit logs.
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
- After order lifecycle edit upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 17 passed.
- After order item edit and inventory adjustment upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 19 passed.
- After selected-order inventory audit upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 20 passed.
- After business operation audit upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 21 passed.
- After paginated list query upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 22 passed.
- After real authentication upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 24 passed.
- After RBAC upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 26 passed.
- After sales BI report upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 27 passed.
- After permission matrix upgrade, `backend/.venv/Scripts/python.exe -m pytest`: 28 passed.
- After Copilot recommendation history upgrade, `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_api.py -q`: 28 passed.
- After Copilot recommendation-to-task upgrade, `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_api.py -q`: 29 passed.
- After notification center upgrade, `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_api.py -q`: 30 passed.
- After owner data-scope upgrade, `backend/.venv/Scripts/python.exe -m pytest -q`: 30 passed.
- After order approval workflow upgrade, `backend/.venv/Scripts/python.exe -m pytest -q`: 31 passed.
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
- Order lifecycle edit smoke succeeded: PATCH updated owner, region, status, due date, and notes for a real order; the returned order still included persisted item details.
- Order item edit regression succeeded: PATCH replaced item rows, recalculated `total_amount`, deducted new product stock, restored removed product stock, and wrote `order_adjustment` movements.
- Order inventory audit regression succeeded: selected-order endpoint returned only movements containing `订单 #{id}` and included both seed deductions and later order adjustments.
- Business audit regression succeeded: customer create, product create, product restock, order create, and order update wrote `success` logs visible through `/api/business-audit-logs`.
- Secondary resource audit regression succeeded: contacts, leads/opportunities, cases, tasks, and goals now write create/update/delete logs.
- Paginated query regression succeeded: customers, products, leads, orders, and business audit logs return correct `items`, `total`, `page`, and filter-constrained rows when pagination parameters are supplied.
- Authentication regression succeeded: demo login returns a Bearer token, `/api/auth/me` returns the current user and organization, logout revokes the token, registration creates a new organization, and duplicate emails are rejected.
- RBAC regression succeeded: unauthenticated business API calls return 401, while a sales role can read/write customers but cannot manage products or read audit logs.
- Sales BI report regression succeeded: `/api/reports/sales-performance` returns real metrics, revenue trend, owner/region breakdowns, funnel, AI impact, inventory risks, filter echoing, invalid date-range rejection, and sales-role 403.
- Permission matrix regression succeeded: `/api/admin/permission-matrix` returns the backend permission catalog, role matrix, module access matrix, and sales-role 403.
- Owner data-scope regression succeeded: a sales role sees only `李伟超` owner records for leads, tasks, orders, and Copilot recommendations; cross-owner lead/order/task updates and Copilot task conversion return 403.
- Order approval workflow regression succeeded: a draft order can be submitted for approval, duplicate pending approvals are rejected, sales users cannot approve, approval managers can approve, the order status advances to `confirmed`, and `order_approval` business audit logs are written.
- DeepSeek Copilot smoke succeeded with the local API key: `/api/copilot/summary` returned `fallback_used=false`, 15 insights, and a non-empty `llm_summary`.

## Next Steps

- Add stricter field-level validation, fuller end-to-end browser smoke coverage, richer approval policies, and URL-synced table filter state.
- Capture screenshots and export Word/PPT final materials.
