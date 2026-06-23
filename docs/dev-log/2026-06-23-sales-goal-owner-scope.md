# 2026-06-23 Sales Goal Owner Scope

## 背景

高分版报告要求销售角色的 owner 数据范围覆盖客户、线索、工单、任务、订单、通知和 Copilot 推荐。检查后发现销售目标页虽已接入真实 API，但 `SalesGoal` 缺少负责人字段，销售角色无法证明“目标也按本人范围隔离”。

## 本次改动

- 后端 `SalesGoal` 增加 `owner` 字段，SQLite 轻量迁移会为旧库补列并回填默认演示负责人。
- `/api/goals` 列表支持 owner 数据范围过滤和 owner 查询参数。
- `POST/PATCH/DELETE /api/goals` 执行负责人归一和跨负责人 403 校验，并把负责人写入业务操作审计。
- 种子数据将 4 个销售目标分配给不同负责人，便于演示销售角色只能看到本人目标。
- 前端销售目标创建/编辑表单增加负责人字段，默认使用当前登录用户；目标卡片展示周期和负责人。
- 测试补充销售目标 owner 轻量迁移，以及销售角色 RBAC 用例中的目标列表、默认负责人、越权创建、越权编辑和越权删除断言。

## 验证

- 已通过窄范围后端测试：
  `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -k "sales_goal_owner_lightweight_migration or rbac_sales_role_permissions or resource_collection_payloads or create_business_resources or update_and_delete_business_resources"`
- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，31 passed
- 已通过前端构建：`npm run build`
- 已通过完整后端测试：`.\.venv\Scripts\python.exe -m pytest`，50 passed
- 已通过本地演示库迁移和环境自检：`.\.venv\Scripts\python.exe -m app.manage migrate`、`.\.venv\Scripts\python.exe -m app.manage doctor`，doctor 显示 4 个销售目标、12 个订单、跨表一致性 issues 0。

## 报告同步

- 已同步 `03_数据库设计文档.md`、`04_后台接口设计文档.md`、`05_软件实现说明.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`。
