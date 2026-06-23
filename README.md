# Smart CRM

一个用于课程设计演示的智能销售管理系统。目前仓库交付入口为：

- 根目录 React + Vite 前端管理台，已包装为深大 AI CRM 风格
- `backend/` FastAPI + SQLite 后端 API
- 可配置 OpenAI-compatible 多模态模型的 AI 智能录单流程

最终冲刺阶段已移除旧版 `frontend/` React + TypeScript 模板应用，避免把 4 月旧演示页面、旧截图或旧构建产物误当成正式交付。当前唯一前端源码位于根目录 `src/`，启动、构建和测试都在仓库根目录执行。

## 当前功能

- 组织选择页
- Team Members 团队成员页
- Dashboard 仪表盘
- Leads 线索页
- Contacts 联系人页
- Accounts 客户页
- Customer 360 客户工作台页
- Opportunities 商机页
- Cases 工单页
- Tasks 任务页
- Sales Goals 目标页
- Notification Center 通知中心
- AI Audit AI 审计页
- AI Copilot 推荐历史
- Business Audit 操作审计页（含跨表一致性巡检）
- Permission Matrix 权限矩阵页
- Sales Reports 销售报表页（含经营快照历史）
- AI Capture 智能录单页
- Orders 订单中心页
- 后端健康检查、部署 readiness、认证登录注册、团队成员、商品、客户、联系人、客户互动、商机、工单、任务、目标、订单、订单审批、跨表一致性巡检和 AI 订单草稿接口
- AI Sales Copilot：客户健康画像联动商机评分、预测金额、风险摘要、跟进话术、订单草稿建议、推荐历史留痕、推荐转任务

## 当前实现边界

- 客户、联系人、线索、商机、工单、任务、目标页面已接入真实 FastAPI 资源接口，并支持新建、编辑、删除后写入 SQLite；通用资源页可聚焦筛选并按当前可见记录导出 CSV。
- 客户、联系人、商品、团队成员、线索、商机、工单、任务和订单中心支持 URL 同步筛选状态；`q`、`tab`、`view`、`order` 参数可用于分享搜索、分组、看板视图和指定订单明细。
- 服务端字段级校验已覆盖邮箱、手机号、商品分类、客户等级/状态、互动类型/情绪、工单/任务优先级与状态、目标值、订单明细非空和交付日期先后关系；无效 payload 会在 FastAPI/Pydantic 层返回 422。
- 登录/注册已接入 FastAPI + SQLite，支持组织创建、账号密码校验、PBKDF2 密码哈希、Bearer 会话 token、当前用户查询、退出登录、认证审计日志、登录失败限流和会话管理；同一账号 15 分钟内连续 5 次失败后会返回 429 并写入 `blocked` 审计记录，个人主页可读取 `/api/auth/sessions` 查看当前账号会话，支持撤销单个其他活跃会话，也支持通过 `/api/auth/sessions/revoke-others` 一键撤销全部其他活跃会话。组织选择页和侧边栏工作区均读取认证会话返回的真实组织，不再使用本地 mock 组织列表。团队成员页接入 `/api/admin/users`，管理员/销售经理可创建成员、调整角色和停用账号，销售经理不能授予或维护管理员账号，停用账号登录会被后端拒绝。
- 商品目录页已接入真实 `/api/products`，支持商品新增、编辑、删除，SKU 唯一校验和历史商品删除保护。
- 仪表盘已接入 `/api/dashboard`、`/api/leads`、`/api/tasks`、`/api/goals`，首页指标、焦点、销售阶段、任务、目标和近期活动均由后端数据驱动；面板头部动作已接入真实路由跳转。
- 销售报表已接入 `/api/reports/sales-performance`、`/api/reports/approval-performance` 和 `/api/reports/snapshots`，按真实订单、商机和审批记录聚合收入趋势、负责人/区域绩效、销售漏斗、AI 收入影响、库存风险、审批 SLA、风险等级和审批人工作量，支持负责人、区域和日期范围筛选，并可把当前销售/审批报表保存为后端重新计算的经营快照。
- `backend/` 已实现 FastAPI API、SQLite 数据库、团队成员管理、用户视图偏好保存、资源创建/编辑/删除、客户 360 工作台、客户健康画像、客户互动记录、客户互动转任务、AI 订单草稿闭环、智能录单草稿历史、订单创建、订单生命周期编辑、订单明细重算、库存差额调整、订单审批流、审批风险分级与 SLA、审批催办/转派、订单审批策略拦截、订单库存审计、库存补货建议、库存流水、通知中心、销售 BI 报表、报表快照、跨表一致性巡检、资源列表分页/搜索/筛选、服务端 RBAC、客户/业务 owner 数据范围、SQLite 轻量迁移、Copilot 健康画像联动摘要、CRM Skill 经营问答、推荐历史、推荐转任务和测试。
- 客户、商品、联系人、客户互动、线索/商机、工单、任务、目标、订单、AI 审计和业务审计列表支持 `page`、`per_page`、`q` 以及常用业务字段筛选；未传分页参数时保持旧版数组响应，方便前端渐进迁移。
- 资源列表的搜索词、筛选标签、列表/看板视图、表格列显示和排序状态会通过 `/api/preferences/{namespace}` 保存到后端 `UserPreference`，同一账号重新登录后可恢复个人视图偏好，不再只依赖当前 URL 或本地缓存。
- 表格资源页支持勾选多行、导出选中 CSV、批量编辑和批量删除；批量编辑会逐条调用对应资源的真实后端 PATCH 接口，批量删除会逐条调用真实 DELETE 接口，成功项从列表移除，失败项保留并提示原因。
- 仓库新增可复跑浏览器 UI 冒烟脚本 `npm run smoke:ui`，会通过真实登录表单进入后端组织，检查仪表盘、客户资源页、订单、报表、应用内删除确认弹窗、深大徽标、8px 圆角、无原生浏览器弹窗和无横向溢出，便于答辩前确认前端不是静态截图。
- AI 录单已支持上传图片或文本，配置视觉模型时走 OpenAI-compatible 多模态抽取；无视觉模型时使用本地文本解析兜底。
- 智能录单草稿可在前端复核后提交到 `/api/orders`，生成真实订单并触发库存扣减；`/api/vision-extract` 会在后端根据客户/商品目录返回 `customer_id` 和条目级 `product_id`，并写入 `CaptureDraft` 草稿历史。前端可在提交前人工修正匹配客户、公司/联系人、置信度、摘要、备注、商品、数量和单价，并通过草稿 PATCH 接口持久化复核结果；提交订单时优先使用后端匹配和人工修正后的 ID/备注，提交成功后把草稿标记为 `submitted`，也支持按草稿/已提交/已作废筛选和人工作废草稿，避免只靠名称二次模糊匹配、丢失未提交草稿或重复提交已关闭草稿。
- AI 副驾、智能录单和订单草稿接口会写入 `AIInteractionLog` 审计表，可在 AI 审计页查看模型、状态、耗时和摘要；AI 审计页同时接入 `/api/reports/ai-quality`，按真实日志展示 LLM 成功率、兜底率、场景覆盖、模型耗时、推荐转任务率和人工好评率。
- Copilot 商机评分、客户健康画像联动评分、推荐历史和 AI 审计均以 FastAPI 后端为唯一权威来源；早期前端本地 `aiScoring` 规则模块已移除，避免前端静态规则与后端可审计评分口径并存。
- AI 副驾页新增 CRM Skill 经营问答，前端调用 `/api/copilot/ask`，后端按当前用户数据范围聚合客户、互动、商机、订单、任务、工单和 Copilot 推荐，再调用 OpenAI-compatible LLM 生成回答；响应同时返回证据片段和下一步动作，并写入 AI 审计。
- Copilot 摘要和跟进话术会写入 `CopilotRecommendation` 推荐历史表，可在 AI 副驾页查看客户、商机、评分、下一步动作、话术草稿和 LLM/兜底状态；摘要评分会把客户健康分、流失概率、服务/关系/AI 执行因子和健康画像建议纳入可解释评分理由，并可在页面内展开查看。
- Copilot 推荐历史可一键转为真实任务，也可提交“已采纳 / 有帮助 / 不匹配”人工反馈；系统会同步更新关联商机的下一步动作，并把转任务与反馈都写入业务操作审计，形成推荐质量闭环。
- 客户列表可打开 `/accounts/{customer_id}` 客户 360 工作台；后端 `/api/customers/{customer_id}/workspace` 会聚合该客户的联系人、互动记录、商机、订单、工单、任务、Copilot 推荐和时间线，并调用 OpenAI-compatible LLM 生成客户经营计划。工作台还会实时计算客户健康画像，输出健康分、增长趋势、流失概率、收入/管道/关系/服务/跟进/AI 落地因子、风险旗标和建议动作。客户 360 页面可调用 `/api/copilot/order-draft` 基于经营目标生成订单草稿，后端会按目标、行业、库存和品类智能选择可用商品，前端可一键提交到 `/api/orders` 形成真实订单、库存和审计闭环。无 Key 或模型异常时返回确定性兜底建议，同时写入 AI 调用审计。工作台内的新增互动会调用 `/api/customers/{customer_id}/activities` 真实落库，互动记录可通过 `/api/customer-activities/{activity_id}/task` 转成真实跟进任务；商机阶段发生真实变化时，`PATCH /api/leads/{id}` 也会自动生成一条客户互动并进入客户时间线、健康画像和业务操作审计。
- 客户、联系人、线索/商机、工单、任务、目标、商品、订单和补货等写库动作会写入 `BusinessAuditLog` 审计表，可在操作审计页查看操作人、对象、状态、摘要和细节；同页还会调用 `/api/system/consistency-checks` 展示订单金额、订单明细、库存流水、审批记录等跨表一致性巡检结果。
- 订单中心已接入 `/api/orders`、`/api/order-approvals`、`/api/products` 和 `/api/inventory/*`，可查看订单筛选、订单明细、AI 标记、置信度、审批记录、审批风险等级、SLA 截止状态、低库存预警、建议补货量、库存流水和本订单库存审计，并支持订单生命周期编辑、订单审批提交/催办/转派/通过/驳回、订单商品明细编辑、订单金额重算和订单明细 CSV 导出。
- 订单状态推进已接入真实审批策略：高金额、AI 低置信度、急交付、多明细或直接履约会触发经理复核；提交审批时按金额、AI 置信度、交付窗口、明细数量和目标状态计算 `low/medium/high/critical` 风险等级，并映射 48/24/12/4 小时 SLA；普通销售不能绕过审批直接确认高风险订单，经理/管理员通过审批后订单状态才会推进。
- 顶部通知中心已接入 `/api/notifications`，从逾期/今日任务、库存风险、待审批订单 SLA、重点商机、客户互动下一步动作、Copilot 待执行建议和 AI 兜底调用聚合真实业务提醒；客户互动一旦转为真实任务，对应提醒会自动消失，避免重复催办。
- 权限矩阵已接入 `/api/admin/permission-matrix`，从后端 RBAC 策略读取角色、权限目录、数据范围和前端模块访问关系。
- 服务端 RBAC 已覆盖主要业务 API：未登录请求返回 401，销售角色可维护本人客户但不能维护商品目录、经营报表或读取审计；客户、联系人、客户互动、线索/商机、工单、任务、订单、客户工作台、AI 推荐历史、通知中心和仪表盘已按销售负责人执行 owner 数据范围过滤，跨负责人创建或更新返回 403。订单审批使用独立 `approval:manage` 权限，销售可提交并催办本人订单审批，销售经理/管理员可转派、通过或驳回，触发审批策略的订单必须审批后才能确认或履约。
- 前端新建客户、线索、商机、工单、任务、智能录单订单和订单编辑时，会默认使用当前登录用户作为负责人；后端同时把空负责人、未分配、待分配、新负责人归一为当前认证用户，保证销售角色演示时创建的数据真实可用且符合 owner 数据范围。

## 环境要求

- Node.js 20+
- npm 10+
- Python 3.12

## 快速开始

### 1. 启动后端

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.manage reset-db
.\.venv\Scripts\python.exe -m app.manage doctor
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端启动后，可访问：

```text
http://127.0.0.1:8000/health
```

### 2. 启动前端

```powershell
cd D:\LwcCode\personal-project\smart-crm
Copy-Item .env.example .env
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

默认开发地址：

```text
http://127.0.0.1:5173
```

前端 `.env` 的 `VITE_API_BASE_URL` 必须指向正在运行的后端，例如 `http://127.0.0.1:8000`。如果临时更换前端端口，也要把 `backend/.env` 里的 `SMART_CRM_CORS_ORIGINS` 同步加入该前端地址，否则浏览器登录会被 CORS 拦截。

默认演示账号：

```text
管理员：demo@smart-crm.local / SmartCRM@2026
销售经理：manager@smart-crm.local / SmartCRM@2026
销售：sales@smart-crm.local / SmartCRM@2026
支持：support@smart-crm.local / SmartCRM@2026
审计员：audit@smart-crm.local / SmartCRM@2026
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
.\.venv\Scripts\python.exe -m app.manage doctor
```

`doctor` 会同时检查数据库表、演示数据规模、LLM 配置和跨表一致性；发现订单金额、库存流水或审批记录异常时会返回非零状态，便于答辩前快速排查。

启动后端后也可以访问 `GET /api/health` 做部署 readiness 检查。该接口会返回数据库驱动、LLM 是否已配置、演示数据数量/目标值和一致性状态，不返回数据库文件路径或 API Key。

### API 冒烟测试

后端运行后，可以从仓库根目录执行标准库脚本，自动验证 readiness、登录、会话、仪表盘、资源列表、通知、报表、权限矩阵、跨表一致性、审计和客户工作台：

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\smoke_api.py --base-url http://127.0.0.1:8000
```

如需把 Copilot 摘要和跟进话术也纳入冒烟，可追加 `--include-ai-write`。该选项会写入 AI 审计和推荐历史，适合答辩前验证 LLM 链路。

### 浏览器 UI 冒烟测试

后端和前端都启动后，可以运行 Playwright 浏览器冒烟脚本，验证真实登录、组织选择、仪表盘、客户列表、应用内删除确认、订单中心、销售报表和基础视觉约束：

```powershell
cd D:\LwcCode\personal-project\smart-crm
npm run smoke:ui -- --frontend-url http://127.0.0.1:5173 --api-url http://127.0.0.1:8000
```

默认使用本机 Chrome 通道。若机器没有可用 Chrome，可先执行 `npx playwright install chromium`，再用 `--channel ""` 走 Playwright 自带 Chromium。追加 `--include-ai-page` 会访问 AI 副驾页，可能触发 LLM 摘要和推荐历史写入。

### 生成报告截图

前后端启动后，可以自动生成 Word/PPT 使用的演示截图：

```powershell
cd D:\LwcCode\personal-project\smart-crm
npm run screenshots:demo -- --frontend-url http://127.0.0.1:5173 --api-url http://127.0.0.1:8000 --clear-output --include-ai
```

默认输出到 `D:\LwcCode\personal-project\报告文档\v2-最终高分版\正式文档\截图`，并生成 `00_screenshot_index.md`。`--include-ai` 会截图 AI 副驾和 AI 审计页，可能触发 LLM 摘要或推荐历史写入；如需保持演示库完全不变，可省略该参数。

### 数据库迁移与快照

保留现有数据升级表结构时，使用显式迁移命令：

```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m app.manage migrate
.\.venv\Scripts\python.exe -m app.manage doctor
```

交接演示数据前可导出 SQLite 快照，恢复后再运行 `doctor` 检查：

```powershell
.\.venv\Scripts\python.exe -m app.manage backup-db .\backups
.\.venv\Scripts\python.exe -m app.manage restore-db .\backups\smart_crm_backup_YYYYMMDD-HHMMSS.db
.\.venv\Scripts\python.exe -m app.manage doctor
```

## 后续增强

- 继续补更细粒度权限审计、更多经营 BI 维度和更完整的 Playwright 业务写入流。
- 将通用卡片、表格、看板拆为独立组件。
- 继续补更多细分经营 BI 维度、长期效果追踪和批量编辑审计摘要。
- 详见 `docs/deployment.md` 和 `docs/dev-log/`。

## 目录结构

- `src/`: 根目录 React 前端源码
- `public/`: 前端静态资源
- `backend/`: FastAPI 后端项目
- `docs/`: 开发日志、部署说明和工程记录
- `_private/`: 本地内部资料目录，不参与代码仓库提交
