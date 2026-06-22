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
- AI Audit AI 审计页
- AI Capture 智能录单页
- Orders 订单中心页
- 后端健康检查、商品、客户、联系人、商机、工单、任务、目标、订单和 AI 订单草稿接口
- AI Sales Copilot：商机评分、预测金额、风险摘要、跟进话术、订单草稿建议

## 当前实现边界

- 客户、联系人、线索、商机、工单、任务、目标页面已接入真实 FastAPI 资源接口，并支持新建、编辑、删除后写入 SQLite。
- 商品目录页已接入真实 `/api/products`，支持商品新增、编辑、删除，SKU 唯一校验和历史商品删除保护。
- 仪表盘已接入 `/api/dashboard`、`/api/leads`、`/api/tasks`、`/api/goals`，首页指标、焦点、销售阶段、任务、目标和近期活动均由后端数据驱动。
- `backend/` 已实现 FastAPI API、SQLite 数据库、资源创建/编辑/删除、订单创建、订单生命周期编辑、库存扣减、库存补货建议、库存流水、资源列表、Copilot 摘要和测试。
- AI 录单已支持上传图片或文本，配置视觉模型时走 OpenAI-compatible 多模态抽取；无视觉模型时使用本地文本解析兜底。
- 智能录单草稿可在前端复核后提交到 `/api/orders`，生成真实订单并触发库存扣减。
- AI 副驾、智能录单和订单草稿接口会写入 `AIInteractionLog` 审计表，可在 AI 审计页查看模型、状态、耗时和摘要。
- 订单中心已接入 `/api/orders`、`/api/products` 和 `/api/inventory/*`，可查看订单筛选、订单明细、AI 标记、置信度、低库存预警、建议补货量、库存流水，并支持订单生命周期编辑和订单明细 CSV 导出。
- 登录鉴权、订单明细编辑、复杂报表、前后端统一鉴权仍未完成。

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

- 继续补分页、字段级校验和资源操作审计。
- 继续补订单明细编辑、重新计价和库存重算。
- 将通用卡片、表格、看板拆为独立组件。
- 把筛选、分页、列显示等状态同步到 URL 参数。
- 补齐登录鉴权、客户/商机/订单 CRUD 和更完整的端到端冒烟测试。
- 详见 `docs/deployment.md` 和 `docs/dev-log/`。

## 目录结构

- `src/`: 根目录 React 前端源码
- `public/`: 前端静态资源
- `backend/`: FastAPI 后端项目
- `frontend/`: 旧版 React + TypeScript 前端，暂时保留用于参考和迁移
- `_private/`: 本地内部资料目录，不参与代码仓库提交
