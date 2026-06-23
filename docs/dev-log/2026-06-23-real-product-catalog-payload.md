# 2026-06-23 Real Product Catalog Payload

## 背景

商品目录是 AI 录单、订单明细、库存扣减和补货建议共用的主数据。此前前端在商品创建时会为缺失商品名或 SKU 生成“新商品”和时间戳 SKU，容易让商品目录看起来像演示脚手架。本轮清理该兜底，让商品名、SKU、分类、单价和库存都来自表单输入。

## 本次改动

- 将商品 payload 构造迁移到 `src/payloadUtils.js`，与客户、联系人和团队账号 payload 统一测试。
- 商品名称和 SKU 不再自动生成；缺失必填字段会保持空值并交由后端 `ProductCreate`/`ProductUpdate` 校验。
- 商品分类改为前端下拉选择，避免手输非法分类导致不可控错误。
- 库存使用数字输入并归一为非负整数，保留 0 库存作为合法主数据状态。
- 新增商品目录 payload 测试，覆盖真实 SKU、分类、价格、库存和缺失必填字段场景。

## 验证

- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，43 passed
- 已通过前端生产构建：`npm run build`
- 已通过后端完整测试：`backend\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，演示数据规模达标，consistency `ok / issues 0`
- 已确认源码中不再出现 `SKU-${Date.now()}` 或“新商品”商品创建兜底逻辑。
- 已重新生成 `05/06/07/08/10` 正式 Word 文档，并完成 docx 结构文本 QA。
- LibreOffice headless 视觉渲染探测 `10_正式Word排版交付清单.docx` 超过 180 秒，已清理残留进程；最终分页和表格视觉检查仍需人工用 Word 打开确认。

## 报告同步

- 已同步 `05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`、`10_正式Word排版交付清单.md`。
- 本轮未改数据库字段或后端接口，后端已有 SKU 唯一性、商品分类、价格和库存校验。
