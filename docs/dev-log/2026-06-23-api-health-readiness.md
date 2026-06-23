# 2026-06-23 API Health Readiness

## Context

The deployment workflow had `python -m app.manage doctor` for local checks, but browser smoke automation and teammate handoff still needed a lightweight HTTP readiness endpoint under the API prefix. The legacy `/health` route only returned `{"status":"ok"}`, which could not prove database connectivity, demo data scale, consistency, or LLM configuration.

## Changes

- Kept `/health` as a minimal compatibility endpoint.
- Added `GET /api/health` with a structured readiness payload:
  - database connection state and database driver
  - LLM base URL, model, and whether an API key is configured
  - demo data counts compared with target classroom demo scale
  - cross-table consistency status and issue counts
- The payload intentionally does not expose the SQLite file path or any API key value.
- Added backend regression coverage for unauthenticated `/api/health`, demo data targets, consistency `issue_count`, and secret redaction.

## Verification

- Targeted backend regression:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -k "health_check"
```

- Full verification passed:

```powershell
npm run lint
npm test -- --run
npm run build
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m app.manage doctor
```

- Results: frontend tests 51 passed; backend tests 53 passed; production build succeeded; doctor reported target demo data scale and consistency `ok / issues 0`.

## Report Sync

- Updated README plus final-report drafts 04, 05, 07, and 08 for `/api/health` readiness.
- Regenerated the corresponding formal DOCX drafts and ran structural QA for `/api/health`, `api_key_configured`, `HTTP readiness`, `API readiness`, and `sk-*` redaction evidence.
