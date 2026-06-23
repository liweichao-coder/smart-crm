# 2026-06-23 Audit Export Suite

## 背景

认证审计已经支持 CSV 导出，但 AI 审计和业务操作审计仍只能在页面查看。为了让系统更接近真实 CRM 的治理能力，本轮补齐“三类审计均可查看、可导出、可归档”的闭环。

## 本次改动

- 新增 `GET /api/ai-audit-logs/export.csv`，支持 `q/operation/status/entity_type/fallback_used` 筛选，由后端导出 UTF-8 BOM CSV。
- 新增 `GET /api/business-audit-logs/export.csv`，支持 `q/action/entity_type/operator/status` 筛选，由后端导出 UTF-8 BOM CSV。
- AI 审计 CSV 只包含模型、状态、兜底、耗时、关联对象、请求摘要和响应摘要，不导出完整 prompt 或密钥。
- AI 审计页和业务操作审计页新增“导出 CSV”按钮。
- 前端新增 `exportAiAuditLogsCsv()`、`exportBusinessAuditLogsCsv()`，并扩展 `src/api.test.js` 覆盖下载 URL。
- 后端 pytest 覆盖 AI 审计筛选导出、业务审计筛选导出和销售角色导出 403。

## 验证

- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，34 passed
- 已通过前端生产构建：`npm run build`
- 已通过后端目标测试：
  - `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -k "ai_audit_logs_record_runtime_actions or rbac_sales_role_permissions"`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -k "create_business_resources"`
- 已通过后端完整测试：`.\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，演示数据规模达标，consistency `ok / issues 0`

## 报告同步

- 已同步 `04_后台接口设计文档.md`、`05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`。
- 已重新生成正式 Word 文档：`04_后台接口设计文档.docx` 至 `08_黑盒白盒测试文档.docx`。
- 已完成 docx 结构 QA，确认新增导出接口、导出按钮、34 passed 和三类审计前端 API 等关键文本进入正式文档。
- 自动视觉渲染 QA 未完成：LibreOffice 渲染 `04_后台接口设计文档.docx` 超过 120 秒，已清理残留 `soffice` 进程和临时目录；后续最终提交前建议用 Word 人工打开检查分页和表格。
