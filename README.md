# Smart CRM

一个用于课程设计演示的智能销售管理系统。目前仓库同时包含：

- 根目录 React + Vite 前端管理台，已包装为深大 AI CRM 风格
- `backend/` FastAPI + SQLite 后端 API
- 本地可运行的 AI 智能录单演示流程

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
- 后端健康检查、商品、客户、联系人、商机、工单、任务、目标、订单和 AI 订单草稿接口
- AI Sales Copilot：商机评分、预测金额、风险摘要、跟进话术、订单草稿建议

## 当前实现边界

- 客户、联系人、线索、商机、工单、任务、目标页面已接入真实 FastAPI 资源接口。
- 仪表盘仍保留部分演示型摘要组件，后续可继续完全接入 `/api/dashboard`。
- `backend/` 已实现 FastAPI API、SQLite 数据库、订单创建、库存扣减、资源列表、Copilot 摘要和测试。
- AI 录单流程在后端已打通，视觉识别当前仍是本地模拟逻辑；AI 副驾已支持 OpenAI 兼容 LLM，未配置 Key 时自动规则兜底。
- 登录鉴权、完整 CRUD、复杂报表、前后端统一鉴权仍未完成。

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

- 将仪表盘摘要组件继续替换为真实 `/api/dashboard` 数据。
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
