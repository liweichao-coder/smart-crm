# Smart CRM Deployment and Demo Data Guide

## 1. Backend Environment

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
Copy-Item .env.example .env
```

Edit `.env`:

```env
SMART_CRM_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
SMART_CRM_DATABASE_URL=sqlite:///./smart_crm.db
SMART_CRM_LLM_BASE_URL=https://api.deepseek.com
SMART_CRM_LLM_API_KEY=
SMART_CRM_LLM_MODEL=deepseek-v4-flash
SMART_CRM_LLM_VISION_MODEL=
SMART_CRM_LLM_TIMEOUT_SECONDS=20
```

Do not commit `.env`; it is ignored by Git.

If the frontend port changes, add the new origin here before starting the backend. For example, a frontend running at `http://127.0.0.1:5277` needs:

```env
SMART_CRM_CORS_ORIGINS=["http://localhost:5277","http://127.0.0.1:5277"]
```

## 2. Install Dependencies

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```powershell
cd D:\LwcCode\personal-project\smart-crm
npm install
Copy-Item .env.example .env
```

Root `.env` is used by Vite. Keep it aligned with the backend port:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 3. Migrate, Reset, and Snapshot Demo Data

When pulling a teammate's code update, run the migration command first if you want to keep the current local data:

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m app.manage migrate
.\.venv\Scripts\python.exe -m app.manage doctor
```

`migrate` creates missing tables and runs the lightweight SQLite migrations used by the app, without dropping existing records.

Use this command whenever the local database needs to be rebuilt:

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m app.manage reset-db
```

Run the environment doctor after resetting or receiving a teammate's checkout:

```powershell
.\.venv\Scripts\python.exe -m app.manage doctor
```

The doctor checks database tables, demo-data scale, LLM configuration state, and cross-table consistency. It exits with a non-zero code when the database is empty, below the classroom-demo target, or has order-total, inventory-movement, order-item, product-stock, or approval-reference consistency issues, so teammates can quickly know when to run `reset-db` or inspect Operation Audit.

Before handing the demo database to another teammate, create a SQLite snapshot:

```powershell
.\.venv\Scripts\python.exe -m app.manage backup-db .\backups
```

Restore a received snapshot, then re-run the doctor:

```powershell
.\.venv\Scripts\python.exe -m app.manage restore-db .\backups\smart_crm_backup_YYYYMMDD-HHMMSS.db
.\.venv\Scripts\python.exe -m app.manage doctor
```

`backend/backups/` is ignored by Git, so local snapshots are not pushed by accident.

Current demo dataset scale:

- 12 customers
- 10 products
- 12 contacts
- 16 customer activities
- 15 leads/opportunities
- 8 support cases
- 8 task items
- 4 sales goals
- 12 seeded orders
- 22 order items, with product stock deducted
- 22 inventory movements and 2 order approval records
- 1 demo organization and 5 role-based users

This scale is intentionally larger than a toy example but still small enough for stable classroom demos.

Default demo logins:

```text
Account: demo@smart-crm.local
Password: SmartCRM@2026

Account: manager@smart-crm.local
Password: SmartCRM@2026

Account: sales@smart-crm.local
Password: SmartCRM@2026

Account: support@smart-crm.local
Password: SmartCRM@2026

Account: audit@smart-crm.local
Password: SmartCRM@2026
```

## 4. Start Services

Backend:

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
cd D:\LwcCode\personal-project\smart-crm
npm run dev -- --host 127.0.0.1 --port 5173
```

If login fails with `Failed to fetch`, verify these two values first:

- `VITE_API_BASE_URL` in the root `.env` points to the actual backend port.
- `SMART_CRM_CORS_ORIGINS` in `backend/.env` includes the exact frontend origin.

Open:

```text
http://127.0.0.1:5173
```

Shareable demo URLs:

```text
http://127.0.0.1:5173/leads?view=board&q=医疗
http://127.0.0.1:5173/team?tab=manager
http://127.0.0.1:5173/orders?tab=ai&order=12
```

## 5. Verify Auth and Copilot

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m pytest
```

Auth smoke:

```powershell
$login = Invoke-RestMethod -Method Post -ContentType "application/json" `
  -Body '{"account":"demo@smart-crm.local","password":"SmartCRM@2026"}' `
  http://127.0.0.1:8000/api/auth/login

Invoke-RestMethod -Headers @{ Authorization = "Bearer $($login.token)" } `
  http://127.0.0.1:8000/api/auth/me

Invoke-RestMethod -Headers @{ Authorization = "Bearer $($login.token)" } `
  "http://127.0.0.1:8000/api/notifications?limit=10"
```

Manual API smoke:

```powershell
Invoke-WebRequest -UseBasicParsing -Headers @{ Authorization = "Bearer $($login.token)" } `
  http://127.0.0.1:8000/api/copilot/summary

Invoke-RestMethod -Headers @{ Authorization = "Bearer $($login.token)" } `
  "http://127.0.0.1:8000/api/copilot/recommendations?source=summary&page=1&per_page=5"

$recommendation = Invoke-RestMethod -Headers @{ Authorization = "Bearer $($login.token)" } `
  "http://127.0.0.1:8000/api/copilot/recommendations?source=summary&limit=1"

Invoke-RestMethod -Method Post -Headers @{ Authorization = "Bearer $($login.token)" } `
  "http://127.0.0.1:8000/api/copilot/recommendations/$($recommendation[0].id)/task"
```

If `SMART_CRM_LLM_API_KEY` is configured and valid, Copilot responses should report `fallback_used: false`. Without a key, the system still returns explainable rule-based recommendations with `fallback_used: true`.

Vision extraction smoke:

```powershell
$text = "客户：云川医疗 联系人：陈敏`n智能巡检终端 x2`n客户数据接入服务 x1"
$bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
$file = Join-Path $env:TEMP "smart-crm-order.txt"
[System.IO.File]::WriteAllBytes($file, $bytes)
curl.exe -H "Authorization: Bearer $($login.token)" `
  -F "file=@$file;type=text/plain" `
  http://127.0.0.1:8000/api/vision-extract
```

Set `SMART_CRM_LLM_VISION_MODEL` to a vision-capable OpenAI-compatible model when the configured provider supports image inputs. If it is empty, Smart CRM reuses `SMART_CRM_LLM_MODEL`; when the provider rejects image messages, the API falls back to local text parsing or catalog fallback and marks `fallback_used: true`.

Resource API smoke:

```powershell
$auth = @{ Authorization = "Bearer $($login.token)" }
Invoke-WebRequest -UseBasicParsing -Headers $auth http://127.0.0.1:8000/api/customers
Invoke-WebRequest -UseBasicParsing -Headers $auth http://127.0.0.1:8000/api/contacts
Invoke-WebRequest -UseBasicParsing -Headers $auth http://127.0.0.1:8000/api/leads
Invoke-WebRequest -UseBasicParsing -Headers $auth http://127.0.0.1:8000/api/cases
Invoke-WebRequest -UseBasicParsing -Headers $auth http://127.0.0.1:8000/api/tasks
Invoke-WebRequest -UseBasicParsing -Headers $auth http://127.0.0.1:8000/api/goals
```

Sales report smoke:

```powershell
Invoke-RestMethod -Headers $auth http://127.0.0.1:8000/api/reports/sales-performance
Invoke-RestMethod -Headers $auth "http://127.0.0.1:8000/api/reports/sales-performance?owner=李伟超&region=华南"
Invoke-RestMethod -Headers $auth http://127.0.0.1:8000/api/reports/approval-performance

$snapshot = Invoke-RestMethod -Method Post -Headers $auth -ContentType "application/json" `
  -Body '{"report_type":"sales_performance","title":"华南销售复盘快照","filters":{"owner":"李伟超","region":"华南"}}' `
  http://127.0.0.1:8000/api/reports/snapshots

Invoke-RestMethod -Headers $auth "http://127.0.0.1:8000/api/reports/snapshots?report_type=sales_performance&limit=5"
Invoke-RestMethod -Method Delete -Headers $auth "http://127.0.0.1:8000/api/reports/snapshots/$($snapshot.id)"
```

The sales report response is aggregated from real orders, opportunities, AI order markers, and inventory risk rules. It includes `metrics`, `revenue_trend`, `owner_performance`, `region_performance`, `funnel`, `ai_impact`, and `inventory_risks`. Report snapshots are recomputed on the backend from the submitted filters, then persisted in SQLite and audited through `BusinessAuditLog`.

Permission matrix smoke:

```powershell
Invoke-RestMethod -Headers $auth http://127.0.0.1:8000/api/admin/permission-matrix
```

The permission matrix response is generated from backend RBAC policy constants and includes `permission_catalog`, `roles`, and `modules`.

RBAC smoke:

```powershell
try {
  Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/customers
} catch {
  $_.Exception.Response.StatusCode.value__
}
# Expected: 401 without Authorization.

# The default demo admin has all permissions. Pytest also covers a sales-role account:
# customer read/write succeeds, while product create, sales report, permission matrix, and audit-log read return 403.
```

Paginated search/filter smoke:

```powershell
Invoke-WebRequest -UseBasicParsing -Headers $auth "http://127.0.0.1:8000/api/customers?page=1&per_page=3&q=深圳"
Invoke-WebRequest -UseBasicParsing -Headers $auth "http://127.0.0.1:8000/api/products?page=1&per_page=2&category=软件"
Invoke-WebRequest -UseBasicParsing -Headers $auth "http://127.0.0.1:8000/api/leads?page=1&per_page=5&stage=proposal&ai_assisted=true"
Invoke-WebRequest -UseBasicParsing -Headers $auth "http://127.0.0.1:8000/api/orders?page=1&per_page=2&status=draft&created_by_ai=true"
```

When `page` or `per_page` is provided, list APIs return `{ items, total, page, per_page, pages, has_next, has_previous }`. Without pagination parameters they keep returning the original array shape, so the existing frontend remains compatible.
