# 2026-06-23 Auth Audit Page Closure

## 背景

后端已经具备真实认证审计能力，会记录登录、注册、退出、个人资料修改、密码修改、团队成员创建和团队成员更新等事件；但前端没有独立入口，答辩时只能通过接口或测试说明，证据展示不够直观。本轮把认证审计补成可筛选、可分页、可截图的前端页面。

## 本次改动

- 新增 `fetchAuthAuditLogs()` 前端 API 调用函数，请求 `/api/auth/audit-logs` 并支持 `page/per_page/q/event/status`。
- 侧边栏新增“认证审计”，受 `audit:read` 权限控制，与 AI 审计、操作审计组成三类审计入口。
- 新增认证审计页面，展示审计总数、本页成功、本页失败、账号治理记录，并提供关键词、事件、状态筛选和上一页/下一页分页。
- 认证事件标签来自后端真实写入事件：`login`、`register`、`profile_update`、`password_change`、`logout`、`team_create`、`team_update`。
- 新增 `src/api.test.js`，覆盖认证审计 API 查询参数拼接，确保分页和筛选参数传到后端。

## 验证

- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，32 passed
- 已通过前端构建：`npm run build`
- 已通过完整后端测试：`.\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过本地演示库环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，doctor 显示 consistency issues 0。
- 已重新生成 04-08 正式 Word 文档，并通过 python-docx 结构检查；LibreOffice 渲染 PNG QA 10 分钟超时，未计为视觉验收通过，需最终人工用 Word 打开复核版式。

## 报告同步

- 已同步 `04_后台接口设计文档.md`、`05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`。
