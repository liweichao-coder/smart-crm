# 2026-06-23 Auth Login Throttle

## Context

The authentication module already supported hashed passwords, bearer sessions, profile/password maintenance, team account governance, and audit exports. The remaining security gap was repeated password guessing: failed logins were audited, but the API did not temporarily block high-frequency failures.

## Changes

- Added a sliding-window login throttle in `backend/app/main.py`: the same account is blocked when it has 5 failed login attempts in 15 minutes.
- The blocked request returns HTTP 429 with a clear Chinese error message and writes a `login/blocked` `AuthAuditLog` entry.
- The lock is time-window based. Once the failed attempts fall outside the 15-minute window, the correct password can log in again.
- Added pytest coverage for 401 failures, 429 blocking, blocked audit details, and post-window recovery.

## Verification

- Targeted backend regression passed:

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests\test_api.py::test_auth_login_me_logout_and_audit backend\tests\test_api.py::test_auth_login_throttles_repeated_failures backend\tests\test_api.py::test_auth_profile_update_and_password_change
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

- Results: frontend tests 50 passed; backend tests 52 passed; production build succeeded; doctor reported demo data at target scale and consistency `ok / issues 0`.

## Report Sync

- Updated README implementation notes.
- Updated final-report drafts 03, 04, 05, 06, 07, and 08 to mention `blocked` audit status, 429 throttling behavior, demo steps, and test evidence.
- Regenerated formal DOCX drafts 03-08 and structurally checked them with `python-docx`; LibreOffice headless rendering still timed out, so final Word GUI visual review remains a manual checklist item.
