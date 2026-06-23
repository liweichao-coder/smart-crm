# 2026-06-23 Audit Filter Workbench

## 背景

认证审计已经具备筛选、分页和筛选导出，但 AI 审计和业务操作审计页面仍主要展示最近记录。后端列表与导出接口已经支持筛选参数，本轮将前端补齐为真实审计工作台，避免“有接口、页面不可操作”的半闭环。

## 本次改动

- AI 审计页新增关键词、操作、关联对象、运行模式筛选。
- 业务操作审计页新增关键词、动作、对象、操作人、状态筛选。
- AI 审计和业务操作审计列表改为后端分页读取，页面显示总数、页码、上一页和下一页。
- AI 审计和业务操作审计导出按钮改为复用当前筛选条件，导出的 CSV 与页面筛选口径一致。
- 业务审计标签补全 `convert`、`feedback`、`customer_activity`、`copilot_recommendation`、`report_snapshot` 等真实动作和对象，减少英文内部枚举直接暴露。
- 筛选栏 CSS 从固定 4 列改为自适应列，兼容认证审计、销售报表、AI 审计和业务审计多字段筛选。

## 验证

- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，35 passed
- 已通过前端生产构建：`npm run build`
- 已通过后端完整测试：`.\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，演示数据规模达标，consistency `ok / issues 0`
- 新增 `src/api.test.js` 覆盖 AI/业务审计列表筛选参数和筛选导出 URL。

## 报告同步

- 已同步 `05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`。
- 已重新生成正式 Word 文档：`05_软件实现说明.docx` 至 `08_黑盒白盒测试文档.docx`。
- 已完成 docx 结构 QA，确认筛选工作台、35 passed 和三类审计列表/导出测试等关键文本进入正式文档。
- 自动视觉渲染 QA 未完成：LibreOffice headless 渲染 `08_黑盒白盒测试文档.docx` 超过 120 秒；已改用 ASCII 临时路径重试仍超时，并清理残留 `soffice` 进程和临时目录。最终提交前建议用 Word 人工打开检查分页和表格。
