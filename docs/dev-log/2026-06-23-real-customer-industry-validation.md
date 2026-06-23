# 2026-06-23 Real Customer Industry Validation

## 背景

客户和联系人表单已经补齐真实录入字段，但后端 `CustomerCreate` 仍保留 `industry = "待补充"`、`phone = "13800000000"`、`email = "customer@example.com"` 和 `source = "课程演示"` 等早期演示默认值。直接调用 API 时，这些默认值可能绕过真实主数据治理。

## 本次改动

- `POST /api/customers` 要求 `company` 和 `industry` 为必填字段，缺失或去空后为空返回 422。
- 客户电话、邮箱和来源缺失时保持空值，不再由后端自动生成演示手机号、演示邮箱或课程演示来源。
- 客户电话和邮箱仍支持为空；一旦填写，继续执行格式校验。
- `PATCH /api/customers/{id}` 对显式提交的空客户名称或空行业返回 422。
- 前端 payload 测试补充“客户行业缺失时保持空值交由后端校验”。

## 验证

- 已通过前端单元测试：`npm test -- --run`，50 passed
- 已通过后端字段级校验定向测试：`backend\.venv\Scripts\python.exe -m pytest backend\tests\test_api.py::test_field_level_validation_rejects_invalid_payloads`
- 已通过前端 lint：`npm run lint`
- 已通过前端生产构建：`npm run build`
- 已通过后端完整测试：`backend\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，演示数据规模达标，consistency `ok / issues 0`
- 已重新生成 `04/05/06/07/08/10` 正式 Word 文档，并完成 docx 结构文本 QA。
- LibreOffice headless 视觉渲染探测 `10_正式Word排版交付清单.docx` 超过 180 秒，已清理残留进程并移除 `_render_check`；最终分页和表格视觉检查需人工用 Word 打开确认。

## 报告同步

- 已同步 `04_后台接口设计文档.md`、`05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`、`10_正式Word排版交付清单.md`。
- 本轮可作为“客户主数据后端也不再补演示行业和联系方式”的答辩证据。
