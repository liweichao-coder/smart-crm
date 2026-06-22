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

## 5. Verify Copilot

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m pytest
```

Manual API smoke:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/copilot/summary
```

If `SMART_CRM_LLM_API_KEY` is configured and valid, Copilot responses should report `fallback_used: false`. Without a key, the system still returns explainable rule-based recommendations with `fallback_used: true`.

Resource API smoke:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/customers
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/contacts
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/leads
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/cases
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/tasks
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/goals
```
