# 2026-06-26 后端演示闭环与数据强化

## 背景

本轮迭代聚焦课堂演示稳定性，不新增复杂模块，不迁移技术栈，继续保留 FastAPI + SQLite。目标是让后端数据能支撑一条可讲述的 Smart CRM AI 销售副驾故事：高优先级商机、客户健康风险、智能录单生成订单、Copilot 推荐转任务、报表体现 AI/普通订单对比。

## 本次改动

- 在 `backend/app/seed.py` 增加幂等的演示故事补种：
  - 强化“云舟年度 CRM 升级”为 A 级高优先级商机，并预置一条可转任务的 Copilot 推荐。
  - 将“星海装备”标记为健康风险客户，补充安全审查阻塞工单、风险互动和逾期任务。
  - 为“南山科技”预置一条已提交的智能录单草稿，关联 AI 订单，保留 AI 审计和业务审计证据。
- 在 `backend/app/manage.py` 中把智能录单草稿、Copilot 推荐、AI 审计、业务审计纳入 doctor 演示数据目标。
- 在 `backend/app/database.py` 补齐智能录单、报表快照、通知状态等表的组织字段轻量迁移范围，便于旧演示库平滑补种。
- 更新后端测试，验证 reset 后确有“提交草稿 -> AI 订单”和“高优先级 Copilot 推荐”证据。

## 演示路径

1. `/api/customers/{id}/workspace` 查看“星海装备”的健康风险画像，风险来源包括安全审查工单、风险互动和逾期任务。
2. `/api/vision-extract/drafts?status=submitted` 查看“南山科技”已提交智能录单草稿，关联的 `/api/orders/{id}` 订单带 `created_by_ai=true`。
3. `/api/copilot/recommendations?source=summary` 查看“云舟年度 CRM 升级”A 级推荐，再调用 `/api/copilot/recommendations/{id}/task` 转真实任务并写业务审计。
4. `/api/reports/sales-performance` 查看 `ai_impact` 中 AI 订单数量、普通订单数量、AI 收入和普通收入对比。

## 验收口径

- `backend/.venv/Scripts/python.exe -m pytest`
- `python -m app.manage seed-db`
- `python -m app.manage doctor`
