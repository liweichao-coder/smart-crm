# 2026-06-23 Real Order Update Payload

## 背景

订单中心已经具备真实订单列表、订单审批、明细重算和库存审计能力，但订单编辑 payload 仍会在交付日期或备注缺失时补今天日期和“订单状态已更新。”。这类兜底适合早期演示，却容易让最终答辩被认为是前端自动造数。本轮把订单编辑进一步收口为真实业务录入。

## 本次改动

- 将订单编辑 payload 构造迁入 `src/payloadUtils.js`，由单元测试约束输入输出。
- 订单编辑弹窗保留真实负责人、区域、状态、交付日期、备注和商品明细；缺失文本保持空值，不再自动补今天日期或固定备注。
- 后端 `SalesOrderCreate/Update` 对负责人和区域执行去空后必填校验，备注只做去空清洗且允许为空。
- `PATCH /api/orders/{order_id}` 对交付日期增加服务端校验，禁止为空或早于原订单下单日期。
- 后端字段级校验测试补充订单负责人、区域和交付日期异常场景。

## 验证

- 已通过前端单元测试：`npm test -- --run`，49 passed
- 已通过后端字段级校验定向测试：`backend\.venv\Scripts\python.exe -m pytest backend\tests\test_api.py::test_field_level_validation_rejects_invalid_payloads`
- 已通过前端 lint：`npm run lint`
- 已通过前端生产构建：`npm run build`
- 已通过后端完整测试：`backend\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，演示数据规模达标，consistency `ok / issues 0`
- 已重新生成 `04/05/06/07/08/10` 正式 Word 文档，并完成 docx 结构文本 QA。
- LibreOffice headless 视觉渲染探测 `10_正式Word排版交付清单.docx` 超过 180 秒，已清理残留进程并移除 `_render_check`；最终分页和表格视觉检查需人工用 Word 打开确认。

## 报告同步

- 已同步 `04_后台接口设计文档.md`、`05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`、`10_正式Word排版交付清单.md`。
- 本轮可作为“订单编辑不再静默补演示日期和备注、后端校验真实业务字段”的答辩证据。
