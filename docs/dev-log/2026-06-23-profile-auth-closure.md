# 2026-06-23 Profile Auth Closure

## 背景

继续清理“只展示、不真实维护”的页面时发现个人主页仍偏静态：资料来自登录态，但没有当前用户资料更新、密码修改和会话安全闭环。这个缺口会削弱认证模块的完整度，也不利于组员部署后维护自己的演示账号。

## 本次改动

- 新增 `PATCH /api/auth/profile`：当前用户可维护姓名、邮箱、手机号、岗位、部门和办公地点；后端校验邮箱唯一、手机号格式和姓名长度，成功后返回新的当前用户会话信息。
- 新增 `POST /api/auth/password`：校验当前密码和新密码确认，拒绝与旧密码相同的新密码，更新 PBKDF2 密码哈希，并撤销同账号除当前会话外的其他活跃会话。
- 个人资料修改和密码修改均写入 `AuthAuditLog`，便于审计页和测试证明账号操作真实发生。
- 前端个人主页从静态信息卡升级为真实资料表单和密码表单，保存资料后刷新全局 session 与 localStorage，侧边栏用户信息同步变化。
- 个人主页布局继续保持浅色、低阴影、8px 圆角的课程汇报风格。

## 验证

- 已通过目标后端测试：
  `.\.venv\Scripts\python.exe -m pytest tests/test_api.py -q -k "auth_profile_update_and_password_change or auth_login_me_logout_and_audit"`
- 已通过前端 lint：`npm run lint`
- 已通过前端单元测试：`npm test -- --run`，31 passed
- 已通过前端构建：`npm run build`
- 已通过完整后端测试：`.\.venv\Scripts\python.exe -m pytest`，51 passed

## 报告同步

- 已同步 `04_后台接口设计文档.md`、`05_软件实现说明.md`、`07_迭代规划记录及项目总结.md`、`08_黑盒白盒测试文档.md`。
