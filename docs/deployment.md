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

## 2. Install Dependencies

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```powershell
cd D:\LwcCode\personal-project\smart-crm
npm install
```

## 3. Reset Demo Database

Use this command whenever the local database needs to be rebuilt:

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m app.manage reset-db
```

Current demo dataset scale:

- 12 customers
- 10 products
- 12 contacts
- 15 leads/opportunities
- 8 support cases
- 8 task items
- 4 sales goals
- 12 seeded orders
- 22 order items, with product stock deducted

This scale is intentionally larger than a toy example but still small enough for stable classroom demos.

Default demo login:

```text
Account: demo@smart-crm.local
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

Open:

```text
http://127.0.0.1:5173
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
```

Manual API smoke:

```powershell
Invoke-WebRequest -UseBasicParsing -Headers @{ Authorization = "Bearer $($login.token)" } `
  http://127.0.0.1:8000/api/copilot/summary

Invoke-RestMethod -Headers @{ Authorization = "Bearer $($login.token)" } `
  "http://127.0.0.1:8000/api/copilot/recommendations?source=summary&page=1&per_page=5"
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
```

The report response is aggregated from real orders, opportunities, AI order markers, and inventory risk rules. It includes `metrics`, `revenue_trend`, `owner_performance`, `region_performance`, `funnel`, `ai_impact`, and `inventory_risks`.

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
