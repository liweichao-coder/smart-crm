# 2026-06-23 Notification State Closure

## 背景

通知中心已经能从任务、库存、审批 SLA、商机、Copilot 推荐和 AI 审计聚合真实业务提醒，但用户只能查看和跳转，已读/忽略状态仍停留在前端临时交互层。为让顶部铃铛更接近真实 CRM 工作台，本轮补齐通知状态持久化。

## 本次改动

- 新增 `NotificationState` 模型，按 user、organization 和 notification_id 保存 unread/read/dismissed 状态。
- `GET /api/notifications` 继续实时聚合业务提醒，并叠加当前用户已读/忽略状态；支持 `include_dismissed` 和 `unread_only` 查询。
- 新增 `PATCH /api/notifications/{notification_id}`，支持单条 read/unread/dismiss，且会校验通知属于当前用户可见范围。
- 新增 `POST /api/notifications/read-all`，可把当前用户可见且未忽略的通知批量标记已读。
- 前端铃铛角标改为未读重点提醒数；点击通知会标记已读并跳转；面板提供“全部已读”和单条“忽略”。

## 验证

- 已通过通知目标测试：
  `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -k "notifications_are_data_driven"`
- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，31 passed
- 已通过前端构建：`npm run build`
- 已通过完整后端测试：`.\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过本地演示库迁移和环境自检：`.\.venv\Scripts\python.exe -m app.manage migrate`、`.\.venv\Scripts\python.exe -m app.manage doctor`，doctor 显示 consistency issues 0。

## 报告同步

- 已同步 `03_数据库设计文档.md`、`04_后台接口设计文档.md`、`05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`。
