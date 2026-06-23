# 2026-06-23 Real Lead Opportunity Payload

## 背景

线索和商机是 L2C 闭环的入口。此前前端在创建或编辑线索/商机时会为缺失名称、客户或下一步动作补“新线索”“新商机”“未关联客户”等演示占位，虽然能快速保存，但不利于课程答辩展示真实主数据治理。本轮将线索/商机 payload 真实化，并把必填字段交给后端统一校验。

## 本次改动

- 将线索/商机 payload 构造迁移到 `src/payloadUtils.js`，与客户、联系人、商品和团队成员 payload 统一测试。
- 前端保留真实商机标题、客户、负责人、金额、预计成交日期和下一步动作，不再静默补占位客户或占位标题。
- 中文阶段标签会映射为后端阶段编码，例如“已联系”映射为 `contacted`。
- 后端 `SalesLeadCreate` / `SalesLeadUpdate` 对标题、客户、负责人和区域执行去空后必填校验，空值返回 422。
- 新增前端 payload 单元测试和后端字段级校验测试，覆盖缺失标题/客户时由服务端拦截的场景。

## 验证

- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，45 passed
- 已通过前端生产构建：`npm run build`
- 已通过后端完整测试：`backend\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，演示数据规模达标，consistency `ok / issues 0`
- 已重新生成 `04/05/06/07/08/10` 正式 Word 文档，并完成 docx 结构文本 QA。
- LibreOffice headless 视觉渲染探测 `10_正式Word排版交付清单.docx` 超过 180 秒，已清理残留进程；最终分页和表格视觉检查需人工用 Word 打开确认。

## 报告同步

- 已同步 `04_后台接口设计文档.md`、`05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`、`10_正式Word排版交付清单.md`。
- 本轮新增内容会在答辩中作为“线索/商机主数据真实录入 + 后端校验”的证据点。
