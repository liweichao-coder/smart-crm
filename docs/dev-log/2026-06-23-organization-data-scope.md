# 2026-06-23 Organization data scope

## Goal

Registered organizations should be real CRM workspaces, not just authentication labels. A new organization must not see demo customers, products, orders, reports, audit logs, notifications, or Copilot recommendations from the course demo organization.

## Changes

- Added `organization_id` to core business models: customers, products, inventory movements, contacts, customer activities, leads, support cases, tasks, sales goals, AI audit logs, Copilot recommendations, business audit logs, orders, and order approval requests.
- Extended lightweight SQLite migrations to add `organization_id INTEGER NOT NULL DEFAULT 1` to older local databases while preserving existing demo data.
- Added organization scope helpers and applied them before owner scope across customer, product, contact, lead, case, task, goal, order, approval, dashboard, notification, report, audit, AI Capture, and Copilot flows.
- Scoped SKU checks, report snapshots, order approvals, inventory movements, AI audit logs, business audit logs, notification aggregation, Copilot history, and customer 360 workspace data to the current authenticated organization.
- Added a regression test that registers a new organization, confirms the workspace starts empty, creates its own customer/product/order, and verifies the demo organization still keeps its 12 demo customers without seeing the new organization record.

## Verification

- `backend/.venv/Scripts/python.exe -m pytest`: 55 passed.
- `npm run lint`: passed.
- `npm test -- --run`: 48 passed.
- `npm run build`: passed.
- `backend/.venv/Scripts/python.exe -m app.manage doctor`: demo environment ready, consistency status ok, 0 issues.

## Report Impact

- Updated v2 database, API, implementation, user manual, iteration summary, and testing Markdown drafts with organization-level business isolation, migration behavior, acceptance route, and verification results.
- LibreOffice rendering remains unavailable on this machine because the local LibreOffice `bootstrap.ini` install configuration is damaged. DOCX generation can proceed with the existing Python/Word workflow and PDF QA can use Microsoft Word COM export as the fallback.
