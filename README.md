# Smart CRM

一个用于课程设计演示的智能销售管理系统。目前仓库同时包含：

- 根目录 React + Vite 前端管理台，已包装为深大 AI CRM 风格
- `backend/` FastAPI + SQLite 后端 API
- 可配置 OpenAI-compatible 多模态模型的 AI 智能录单流程

## 当前功能

- 组织选择页
- Dashboard 仪表盘
- Leads 线索页
- Contacts 联系人页
- Accounts 客户页
- Opportunities 商机页
- Cases 工单页
- Tasks 任务页
- Sales Goals 目标页
- Notification Center 通知中心
- AI Audit AI 审计页
- AI Copilot 推荐历史
- Business Audit 操作审计页
- Permission Matrix 权限矩阵页
- Sales Reports 销售报表页
- AI Capture 智能录单页
- Orders 订单中心页
- 后端健康检查、认证登录注册、商品、客户、联系人、商机、工单、任务、目标、订单、订单审批和 AI 订单草稿接口
- AI Sales Copilot：商机评分、预测金额、风险摘要、跟进话术、订单草稿建议、推荐历史留痕、推荐转任务

## 当前实现边界

- 客户、联系人、线索、商机、工单、任务、目标页面已接入真实 FastAPI 资源接口，并支持新建、编辑、删除后写入 SQLite。
- 登录/注册已接入 FastAPI + SQLite，支持组织创建、账号密码校验、PBKDF2 密码哈希、Bearer 会话 token、当前用户查询、退出登录和认证审计日志。
- 商品目录页已接入真实 `/api/products`，支持商品新增、编辑、删除，SKU 唯一校验和历史商品删除保护。
- 仪表盘已接入 `/api/dashboard`、`/api/leads`、`/api/tasks`、`/api/goals`，首页指标、焦点、销售阶段、任务、目标和近期活动均由后端数据驱动。
- 销售报表已接入 `/api/reports/sales-performance`，按真实订单和商机聚合收入趋势、负责人/区域绩效、销售漏斗、AI 收入影响和库存风险，支持负责人、区域和日期范围筛选。
- `backend/` 已实现 FastAPI API、SQLite 数据库、资源创建/编辑/删除、订单创建、订单生命周期编辑、订单明细重算、库存差额调整、订单审批流、订单库存审计、库存补货建议、库存流水、通知中心、销售 BI 报表、资源列表分页/搜索/筛选、服务端 RBAC、客户/业务 owner 数据范围、SQLite 轻量迁移、Copilot 摘要、推荐历史、推荐转任务和测试。
- 客户、商品、联系人、线索/商机、工单、任务、目标、订单、AI 审计和业务审计列表支持 `page`、`per_page`、`q` 以及常用业务字段筛选；未传分页参数时保持旧版数组响应，方便前端渐进迁移。
- AI 录单已支持上传图片或文本，配置视觉模型时走 OpenAI-compatible 多模态抽取；无视觉模型时使用本地文本解析兜底。
- 智能录单草稿可在前端复核后提交到 `/api/orders`，生成真实订单并触发库存扣减。
- AI 副驾、智能录单和订单草稿接口会写入 `AIInteractionLog` 审计表，可在 AI 审计页查看模型、状态、耗时和摘要。
- Copilot 摘要和跟进话术会写入 `CopilotRecommendation` 推荐历史表，可在 AI 副驾页查看客户、商机、评分、下一步动作、话术草稿和 LLM/兜底状态。
- Copilot 推荐历史可一键转为真实任务，系统会同步更新关联商机的下一步动作，并写入业务操作审计。
- 客户、联系人、线索/商机、工单、任务、目标、商品、订单和补货等写库动作会写入 `BusinessAuditLog` 审计表，可在操作审计页查看操作人、对象、状态、摘要和细节。
- 订单中心已接入 `/api/orders`、`/api/order-approvals`、`/api/products` 和 `/api/inventory/*`，可查看订单筛选、订单明细、AI 标记、置信度、审批记录、低库存预警、建议补货量、库存流水和本订单库存审计，并支持订单生命周期编辑、订单审批提交/通过/驳回、订单商品明细编辑、订单金额重算和订单明细 CSV 导出。
- 顶部通知中心已接入 `/api/notifications`，从逾期/今日任务、库存风险、待审批订单、重点商机、Copilot 待执行建议和 AI 兜底调用聚合真实业务提醒。
- 权限矩阵已接入 `/api/admin/permission-matrix`，从后端 RBAC 策略读取角色、权限目录、数据范围和前端模块访问关系。
- 服务端 RBAC 已覆盖主要业务 API：未登录请求返回 401，销售角色可维护本人客户但不能维护商品目录、经营报表或读取审计；客户、联系人、线索/商机、工单、任务、订单、AI 推荐历史、通知中心和仪表盘已按销售负责人执行 owner 数据范围过滤，跨负责人创建或更新返回 403。订单审批使用独立 `approval:manage` 权限，销售可提交本人订单审批，销售经理/管理员可审批或驳回。

## 环境要求

- Node.js 20+
- npm 10+
- Python 3.12

## 快速开始

### 1. 启动前端

```powershell
cd D:\LwcCode\personal-project\smart-crm
npm install
npm run dev
```

默认开发地址：

```text
http://127.0.0.1:5173
```

### 2. 启动后端

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.manage reset-db
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端启动后，可访问：

```text
http://127.0.0.1:8000/health
```

默认演示账号：

```text
账号：demo@smart-crm.local
密码：SmartCRM@2026
```

## 测试项目是否正常

### 前端构建测试

```powershell
cd D:\LwcCode\personal-project\smart-crm
npm run build
```

### 后端测试

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m pytest
```

## 下一步建议

- 继续补字段级校验、端到端冒烟测试和更细粒度权限审计。
- 将通用卡片、表格、看板拆为独立组件。
- 把筛选、分页、列显示等状态同步到 URL 参数。
- 继续补 URL 同步筛选状态和更完整的端到端冒烟测试。
- 详见 `docs/deployment.md` 和 `docs/dev-log/`。

## 目录结构

- `src/`: 根目录 React 前端源码
- `public/`: 前端静态资源
- `backend/`: FastAPI 后端项目
- `frontend/`: 旧版 React + TypeScript 前端，暂时保留用于参考和迁移
- `_private/`: 本地内部资料目录，不参与代码仓库提交
