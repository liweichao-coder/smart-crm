# 2026-06-23 Real Team Account Payload

## 背景

团队成员管理已经接入真实后端账号、RBAC、密码哈希、账号启停和认证审计。但前端成员 payload 构造仍保留 `member@demo.smart-crm.local` 兜底邮箱，容易让账号创建看起来像演示脚手架。本轮清理该兜底，让表单和后端校验共同保证真实账号输入。

## 本次改动

- 将团队成员 payload 构造迁移到 `src/payloadUtils.js`，与客户/联系人主数据 payload 统一管理。
- 新增团队成员创建和编辑 payload 测试，覆盖姓名、邮箱、手机、角色、岗位、部门、地点、状态和密码确认字段。
- 创建成员时不再静默写入固定 demo 邮箱；空姓名、空邮箱、空密码会进入表单必填或后端校验，不生成伪数据。
- 编辑成员时如果未填写新密码，不提交密码字段，避免误触发密码重置。

## 验证

- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，41 passed
- 已通过前端生产构建：`npm run build`
- 已通过后端完整测试：`backend\.venv\Scripts\python.exe -m pytest`，51 passed
- 已通过环境自检：`.\.venv\Scripts\python.exe -m app.manage doctor`，演示数据规模达标，consistency `ok / issues 0`
- 已确认源码中不再出现 `member@demo.smart-crm.local` 兜底逻辑。
- 已重新生成 `05/06/07/08/10` 正式 Word 文档，并完成 docx 结构文本 QA。
- LibreOffice headless 视觉渲染探测 `10_正式Word排版交付清单.docx` 超过 180 秒，已清理残留进程；最终分页和表格视觉检查仍需人工用 Word 打开确认。

## 报告同步

- 已同步 `05_软件实现说明.md`、`06_软件使用手册.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`、`10_正式Word排版交付清单.md`。
- 本轮未改数据库字段或后端接口，`01/02/03/04/09` 的需求、数据库、接口和答辩脚本描述仍适用。
