# 2026-06-24 智能录单草稿人工复核修正

## 背景

前一轮已完成智能录单草稿历史、状态筛选、作废和提交锁定，但草稿内容仍主要来自抽取结果。为了让 AI Capture 更像真实 CRM 录单流程，本轮把“人工复核”从只读查看升级为可保存的业务动作。

## 代码更新

- 后端 `PATCH /api/vision-extract/drafts/{draft_id}` 支持更新 `customer_id`、`company`、`customer_name`、`confidence`、`summary`、`suggested_notes` 和 `items`。
- 后端校验商品归属、数量、单价和客户 owner 数据范围；已提交或已作废草稿继续修改内容会返回 422。
- 前端智能录单页支持编辑匹配客户、公司、联系人、置信度、摘要、商品、数量、单价和复核备注，并提供“添加条目”“保存草稿修正”操作。
- 订单 payload 优先使用人工复核后的 `suggested_notes`，保证提交订单能带上销售复核意见。
- 测试补充草稿内容 PATCH、复核备注进入订单、提交后禁止继续编辑和前端订单备注优先级。

## 验证

- `npm run lint`：通过。
- `npm test -- --run`：51 passed。
- `backend\.venv\Scripts\python.exe -m pytest`：56 passed。
- `npm run build`：通过。
- 后端目录执行 `.\.venv\Scripts\python.exe -m app.manage doctor`：演示数据规模达标，consistency ok / issues 0。

## 报告同步

- 已同步需求、功能设计、后台接口、实现说明、使用手册、迭代总结、测试文档和答辩脚本。
- 下一步截图时应新增“保存草稿修正”按钮、可编辑复核字段、已提交草稿锁定状态三张证据图。
