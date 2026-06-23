# 2026-06-23 Remove Client Resource Fallbacks

## 背景

客户、联系人、商品、团队成员和线索/商机已经逐步完成真实 payload 收口后，通用资源工具里仍保留 `buildClientRecord()`，会在没有后端创建处理时生成 `local-*` 本地记录；工单、任务、销售目标 payload 也仍会补“新工单”“新任务”“新销售目标”等演示文本。本轮继续清理这些兜底，避免页面把本地临时数据伪装成真实写库结果。

## 本次改动

- 移除 `src/resourceUtils.js` 中的文本占位表和 `buildClientRecord()`，通用表格/看板资源页缺少后端创建处理时直接显示错误。
- `createDraftFromColumns()` 对文本字段默认保持空值，只有显式 `defaultValue`、数字字段和业务枚举下拉会给默认。
- 新增工单、任务、销售目标 payload 构造，保留真实标题、客户、说明、到期时间、周期和目标值，不再自动补演示文本。
- 工单、任务和销售目标弹窗补充真实下拉和可空说明字段，目标值缺失时交由浏览器必填与后端 422 校验。
- 后端 `SupportCaseCreate/Update`、`TaskItemCreate/Update`、`SalesGoalCreate/Update` 增加去空后必填校验，空标题、空客户、空到期时间、空目标周期返回 422。

## 验证

- 已通过前端单元测试：`npm test -- --run`，47 passed
- 已通过后端字段级校验定向测试：`backend\.venv\Scripts\python.exe -m pytest backend\tests\test_api.py::test_field_level_validation_rejects_invalid_payloads`
- 已通过前端 lint：`npm run lint`
- 已通过前端生产构建：`npm run build`
- 已通过后端完整测试：`backend\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，演示数据规模达标，consistency `ok / issues 0`
- 已重新生成 `04/05/06/07/08/10` 正式 Word 文档，并完成 docx 结构文本 QA。
- LibreOffice headless 视觉渲染探测 `10_正式Word排版交付清单.docx` 超过 180 秒，已清理残留进程并移除 `_render_check`；最终分页和表格视觉检查需人工用 Word 打开确认。

## 报告同步

- 已同步 `04_后台接口设计文档.md`、`05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`、`10_正式Word排版交付清单.md`。
- 本轮可作为“通用资源页不再本地造数 + 工单/任务/目标主数据真实录入”的答辩证据。
