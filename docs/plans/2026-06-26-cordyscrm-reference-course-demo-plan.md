# 2026-06-26 CordysCRM Reference Course Demo Plan

## 1. Goal

Smart CRM is a Web-only Software Engineering Practice course project. The next iteration should make the product look and present like a mature AI CRM while keeping the actual scope small enough for classroom demonstration.

The main benchmark is `1Panel-dev/CordysCRM`. We will use it as a visual and product-structure reference: inspect screenshots and page organization first, and only read code when a layout or interaction is hard to understand from screenshots. Smart CRM must keep its own React + FastAPI + SQLite implementation, local course logo, demo data, and report wording.

## 2. Reference Boundary

Allowed:

- Refer to CordysCRM screenshots for page composition, density, table layout, dashboard grouping, side navigation, stage board, drawer, and AI entry organization.
- Refer to CordysCRM source only to understand a difficult interaction or component hierarchy.
- Recreate similar layouts in Smart CRM with self-written React components and CSS.
- Mention CordysCRM in the final acknowledgements as a product-structure and UI reference.

Not allowed:

- Do not copy CordysCRM source files, icons, logo, trademarks, image assets, iconfont, or exact brand expressions.
- Do not remove or hide CordysCRM attribution if any original Cordys material is ever shown in an internal reference note.
- Do not claim Smart CRM is CordysCRM or a commercial CRM suite.
- Do not let README or reports describe the project as "packaging", "shelling", or "copying".

## 3. CordysCRM Pages To Reference

| CordysCRM Area | What To Learn | Smart CRM Course Version |
| --- | --- | --- |
| Workbench | Information density, quick access, data overview, pending work aggregation | Course demo workbench with L2C path, KPI, quick actions, AI risk reminders, pending tasks |
| Customer | Mature table toolbar, filters, columns, customer detail drawer | Customer list plus customer 360 drawer/page, health profile, contacts, activities |
| Clue/Lead | Lead source, owner, status, list management | Simple lead list with source, AI score, next action, convert-to-opportunity story |
| Opportunity | Stage board and amount-focused cards | Main L2C board: stages, amount, probability, owner, AI next action |
| Order | List/detail/approval state | Order list, AI-created badge, approval flow, inventory deduction, audit evidence |
| AI Skills | AI capability entrance, scenario list, history | AI Sales Copilot with score reasons, follow-up draft, recommendation history, task conversion, feedback |
| Dashboard/BI | KPI cards, report modules, snapshot idea | Sales reports with filters, AI impact, approval efficiency, persisted report snapshots |

## 4. Demonstration Scope

### Main Route

The final classroom route should be:

```text
Login -> Workbench -> Customers -> Leads/Opportunities -> AI Copilot -> AI Capture -> Orders -> Sales Reports
```

### Keep As First-Class Pages

- Login and organization selection
- Workbench
- Customers and customer 360
- Leads
- Opportunities stage board
- AI Copilot
- AI Capture
- Orders and approvals
- Sales reports

### Fold Into More Features

- Team members
- Permission matrix
- Products
- Support cases
- Tasks
- Goals
- Auth audit
- AI audit
- Business audit

### De-emphasize

- Full enterprise CRM complexity
- Full BI platform
- Full workflow engine
- Mini program/mobile client
- Deep multi-tenant operations

## 5. Frontend Iteration Plan

### Step F1: Shell And Navigation

- Rebuild the app shell to look like a mature CRM: compact sidebar, topbar, content header, clear breadcrumbs/actions.
- Sidebar groups:
  - Demo Mainline: Workbench, Customers, Leads, Opportunities, Orders
  - AI Highlights: AI Copilot, AI Capture
  - Analytics: Sales Reports
  - More: team, permissions, products, cases, tasks, goals, audits
- Keep local Smart CRM logo and red SZU-inspired brand color.
- Avoid one-screen menu overload.

### Step F2: Workbench

- First screen must answer: what should the salesperson do today?
- Include:
  - L2C progress strip
  - KPI cards
  - Quick access actions
  - Today's pending work
  - AI risk/recommendation panel
  - Lightweight pipeline overview

### Step F3: Resource Lists

- Customers, leads, opportunities, and orders should share a mature CRM list pattern:
  - title and primary action
  - search/filter area
  - list/board view switch where useful
  - visible columns and sorting
  - selected-row actions where already supported by backend
- Use stable grid/flex layout, `min-width: 0`, responsive tracks, and controlled overflow.

### Step F4: Opportunity Board

- Make stage board the main opportunity view.
- Cards show customer, amount, probability, owner, due date, AI score or next action.
- Columns show count and amount total.
- Use containment or simple isolated columns to keep interactions responsive.

### Step F5: AI Pages

- AI Copilot first screen must show:
  - current top recommendation
  - score reasons
  - follow-up draft
  - recommendation history
  - convert-to-task action
  - feedback status
- AI Capture must show:
  - upload/input
  - extraction result
  - human review
  - generated order and draft history

### Step F6: Reports

- Sales report page should be visual but simple:
  - filters
  - sales KPI
  - AI order impact
  - approval efficiency
  - report snapshot history

## 6. Backend Iteration Plan

### Step B1: Keep Real Demo Flow

Every visible demo action should read from or write to FastAPI + SQLite:

- login uses real bearer sessions
- customer/lead/order data comes from SQLite
- AI recommendations are persisted
- AI Capture drafts are persisted
- order creation writes order items and inventory movements
- approval decisions write approval and audit records
- reports are computed by backend APIs and snapshots are persisted

### Step B2: Demo Dataset

Seed data should support four storylines:

1. High-priority opportunity: AI score -> recommendation -> task conversion.
2. Risk customer: health profile -> risk reason -> follow-up action.
3. AI capture: quote text/image -> draft -> order -> inventory/approval/audit.
4. Sales report: normal orders vs AI-created orders, approval efficiency, snapshot evidence.

### Step B3: Simplify Exposed Backend Surface

Keep the implemented APIs, but report and UI should focus on:

- `/api/auth/*`
- `/api/dashboard`
- `/api/customers`
- `/api/customers/{id}/workspace`
- `/api/leads`
- `/api/orders`
- `/api/order-approvals`
- `/api/copilot/*`
- `/api/vision-extract/*`
- `/api/reports/*`
- `/api/audit/*` only as evidence pages

### Step B4: LLM And Key Handling

- DeepSeek/OpenAI-compatible key stays in local `.env` or shell environment.
- No real key in git, README, reports, screenshots, or exported packages.
- Fallback scoring must work without a key.

## 7. Report Synchronization Plan

After each visible feature update, sync:

- `01_软件需求说明报告.md`: user roles, L2C flow, AI Copilot requirements, acceptance criteria.
- `02_产品功能设计与原型报告.md`: CordysCRM reference, final UI choices, page flow.
- `03_数据库设计文档.md`: actual tables used by demo stories.
- `04_后台接口设计文档.md`: only emphasize APIs used in the demo route.
- `05_软件实现说明.md`: React + FastAPI + SQLite + OpenAI-compatible LLM + tests.
- `06_软件使用手册.md`: rewrite around the final 8-step demonstration.
- `07_迭代规划记录及项目总结.md`: April initial version -> frontend integration -> AI and backend closure -> CordysCRM reference UI iteration.
- `08_黑盒白盒测试文档.md`: UI smoke, API tests, backend pytest, manual GUI checklist.
- `09_答辩PPT大纲与演示脚本.md`: one route, fewer pages, clearer AI highlights.
- `11_最终GUI验收与人工Review清单.md`: screenshots and Word/PPT review.

## 8. Execution Order Without Subagents

Because subagent quota is limited, this work will be done sequentially in the main Codex session:

1. Freeze and review current uncommitted changes.
2. Capture or inspect CordysCRM reference pages only as needed.
3. Refactor shell/navigation/workbench.
4. Refactor customer/lead/opportunity/order UI.
5. Refactor AI Copilot and AI Capture first-screen presentation.
6. Verify backend demo dataset and API flow.
7. Sync README, deployment docs, dev log, and final report drafts.
8. Run validation:
   - `npm run lint`
   - `npm test`
   - `npm run build`
   - `backend/.venv/Scripts/python.exe -m app.manage doctor`
   - `backend/.venv/Scripts/python.exe -m pytest`
   - UI smoke test when frontend/backend are running
9. Scan for secrets and local absolute paths before commit.
10. Commit focused changes and merge/push `main` when verification passes.

## 9. Acceptance Standard

The project is considered classroom-ready when:

- A teacher can understand the system from the left navigation in 5 seconds.
- The demo route can be completed in 8-10 minutes without explaining unused modules.
- AI features are visible in the first screen of AI pages.
- Every demo action has backend evidence.
- README and reports do not contain internal wording such as "packaging", "copying", "agent", or local private paths.
- Final docs clearly acknowledge CordysCRM as a UI/product reference while presenting Smart CRM as a course project implemented by the team.
