# 2026-06-23 API Smoke Script

## Context

The project already had unit tests, backend pytest, `doctor`, and many manual smoke commands in deployment notes. The remaining handoff gap was repeatability: teammates still had to copy several requests manually to prove a running backend was ready for the classroom demo.

## Changes

- Added `scripts/smoke_api.py`, a Python standard-library smoke runner.
- The script accepts `--base-url`, `--account`, `--password`, and `--timeout`, with environment-variable overrides.
- Default smoke coverage:
  - `GET /api/health`
  - login, current user, auth sessions, logout cleanup
  - dashboard, customers, products, contacts, leads, cases, tasks, goals, orders
  - notifications, sales report, approval report
  - team members, permission matrix
  - consistency checks, Copilot recommendation/audit list shapes, customer workspace health profile
- Optional `--include-ai-write` calls Copilot summary and follow-up, which may write AI audit and recommendation records.
- Updated README and deployment notes so teammates can run the smoke after starting the backend.

## Verification

```powershell
.\backend\.venv\Scripts\python.exe -m py_compile scripts\smoke_api.py
.\backend\.venv\Scripts\python.exe scripts\smoke_api.py --base-url http://127.0.0.1:8034
```

Result: the smoke passed on a temporary local backend and reported readiness, login, current-user, sessions, dashboard, core resources, notifications, reports, admin, consistency, audit/Copilot history, and customer-workspace checks.

Full regression also passed:

```powershell
npm run lint
npm test -- --run
npm run build
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m app.manage doctor
```

Results: frontend tests 51 passed; backend tests 53 passed; production build succeeded; doctor reported target demo data scale and consistency `ok / issues 0`.

## Report Sync

- Updated README and `docs/deployment.md` with the smoke command and `--include-ai-write` note.
- Updated final-report drafts 05, 07, and 08.
- Regenerated formal DOCX drafts 05, 07, and 08; structural QA confirmed `scripts/smoke_api.py`, `--include-ai-write`, `BB-32B`, `WB-29B`, and `audit-and-copilot-history` evidence.
