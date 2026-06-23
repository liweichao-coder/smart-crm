# 2026-06-23 Auth Audit CSV Export

## 背景

认证审计页面已经可以查看登录、注册、个人资料、密码和团队成员维护记录，但课堂验收或安全复盘时还需要把当前筛选范围导出成文件，便于放入报告附件、答辩材料或交给组员检查。

## 本次改动

- 新增 `GET /api/auth/audit-logs/export.csv`，复用认证审计的 `q/event/status` 筛选条件，由后端生成 UTF-8 BOM CSV。
- CSV 字段包含日志 ID、时间、事件、状态、账号、用户 ID、组织 ID 和详情。
- 前端 `AuthAuditPage` 新增“导出 CSV”按钮，导出当前已应用筛选条件下的全部认证审计记录。
- 新增 `exportAuthAuditLogsCsv()` 前端 API 包装，并扩展 `src/api.test.js` 覆盖下载 URL 和 blob 返回。
- 后端 pytest 覆盖导出内容、筛选结果和销售角色 403，避免只有菜单隐藏而接口可下载。

## 验证

- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，33 passed
- 已通过后端目标测试：`.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -k "auth_login_me_logout_and_audit or rbac_sales_role_permissions"`
- 已通过前端构建：`npm run build`
- 已通过完整后端测试：`.\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过本地演示库环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，doctor 显示 consistency issues 0。
- 已重新生成 04-08 正式 Word 文档，并通过 python-docx 结构检查；LibreOffice 渲染 PNG QA 5 分钟超时且无 PNG/PDF 输出，已清理残留 `soffice` 进程和中间目录，最终提交前仍需人工打开 Word 复核版式。

## 报告同步

- 已同步 `04_后台接口设计文档.md`、`05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`。
