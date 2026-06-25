# Smart CRM

Smart CRM 是一个面向课程设计演示的 **Web 端智能销售管理系统**。系统使用 React + FastAPI + SQLite 实现销售管理闭环，并加入 AI Sales Copilot、智能录单、客户健康画像、销售报表、权限控制和审计留痕。

> 当前交付范围：Web 管理端 + FastAPI 后端。小组成员只需要按本文档启动前后端即可完成演示。

## Highlights

| 模块 | 已实现能力 |
|---|---|
| 销售管理 | 客户、联系人、线索/商机、商品、订单、工单、任务、销售目标 |
| AI Copilot | 商机评分、客户健康画像、跟进建议、经营问答、推荐转任务、人工反馈 |
| 智能录单 | 文本/图片抽取订单草稿、人工复核、提交真实订单、库存扣减 |
| 报表分析 | 仪表盘、销售绩效、审批 SLA、经营快照、AI 质量统计 |
| 权限审计 | 登录会话、RBAC、销售 owner 数据范围、AI 审计、业务审计、认证审计 |
| 交付验证 | 演示数据 seed、环境 doctor、API smoke、UI smoke、前后端自动测试 |

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | React 19, Vite, lucide-react |
| Backend | FastAPI, SQLModel, SQLite |
| AI | OpenAI-compatible API, DeepSeek-compatible config, deterministic fallback |
| Test | node:test, pytest, Playwright smoke |

```mermaid
flowchart LR
  Browser[React Web App] --> API[FastAPI REST API]
  API --> DB[(SQLite)]
  API --> LLM[OpenAI-compatible LLM]
  API --> Audit[AI / Business / Auth Audit]
  DB --> Reports[Dashboard & Reports]
```

## Quick Start

### 1. Requirements

- Node.js 20+
- npm 10+
- Python 3.12
- Chrome, only required for `npm run smoke:ui`

### 2. Backend

```powershell
cd <SMART_CRM_ROOT>\backend

py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m app.manage reset-db
.\.venv\Scripts\python.exe -m app.manage doctor
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend health check:

```text
http://127.0.0.1:8000/api/health
```

### 3. Frontend

Open another terminal:

```powershell
cd <SMART_CRM_ROOT>

npm install
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

## Demo Accounts

All seed accounts use the same password: `SmartCRM@2026`.

| Role | Account |
|---|---|
| Admin | `demo@smart-crm.local` |
| Sales Manager | `manager@smart-crm.local` |
| Sales | `sales@smart-crm.local` |
| Support | `support@smart-crm.local` |
| Auditor | `audit@smart-crm.local` |

Recommended demo route:

1. Login as Admin.
2. Open Dashboard and Notification Center.
3. Open Accounts, Customer 360, Orders, Sales Reports.
4. Open AI Copilot and ask a sales question.
5. Convert a Copilot recommendation to a task.
6. Open AI Audit, Business Audit, Permission Matrix.
7. Login as Sales to show owner-scoped data.

## Environment

Root `.env` is used by Vite:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Backend `.env` is used by FastAPI:

```env
SMART_CRM_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
SMART_CRM_DATABASE_URL=sqlite:///./smart_crm.db
SMART_CRM_LLM_BASE_URL=https://api.deepseek.com
SMART_CRM_LLM_API_KEY=
SMART_CRM_LLM_MODEL=deepseek-v4-flash
SMART_CRM_LLM_VISION_MODEL=
SMART_CRM_LLM_TIMEOUT_SECONDS=20
```

LLM key is optional. Without a key, Copilot and intelligent capture keep working with deterministic fallback results. Do not commit `.env`.

## Verification

Run these before a classroom demo:

```powershell
cd <SMART_CRM_ROOT>
npm run lint
npm test -- --run
npm run build
```

```powershell
cd <SMART_CRM_ROOT>\backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m app.manage doctor
```

After both services are running:

```powershell
cd <SMART_CRM_ROOT>
.\backend\.venv\Scripts\python.exe .\scripts\smoke_api.py --base-url http://127.0.0.1:8000
npm run smoke:ui -- --frontend-url http://127.0.0.1:5173 --api-url http://127.0.0.1:8000
```

To include the AI Copilot page in browser smoke:

```powershell
npm run smoke:ui -- --frontend-url http://127.0.0.1:5173 --api-url http://127.0.0.1:8000 --include-ai-page
```

## Demo Data

Reset the standard classroom database:

```powershell
cd <SMART_CRM_ROOT>\backend
.\.venv\Scripts\python.exe -m app.manage reset-db
.\.venv\Scripts\python.exe -m app.manage doctor
```

`doctor` checks table structure, seed data scale, LLM config, and cross-table consistency. A healthy demo database includes 12 customers, 10 products, 15 leads/opportunities, 12 orders, 22 order items, and 0 consistency issues.

Backup or restore a local SQLite demo snapshot:

```powershell
.\.venv\Scripts\python.exe -m app.manage backup-db .\backups
.\.venv\Scripts\python.exe -m app.manage restore-db .\backups\smart_crm_backup_YYYYMMDD-HHMMSS.db
.\.venv\Scripts\python.exe -m app.manage doctor
```

`backend/backups/` is ignored by Git.

## Project Structure

```text
smart-crm/
├─ src/                 React + Vite frontend
├─ public/              frontend static assets
├─ backend/             FastAPI backend and SQLite tooling
├─ scripts/             API smoke, UI smoke, screenshot helpers
├─ docs/                deployment guide and dev logs
└─ README.md
```

## More Docs

- Detailed deployment: `docs/deployment.md`
- Engineering logs: `docs/dev-log/`
- Report package: `<REPORT_ROOT>`
