# 2026-06-26 本地 CORS 与登录页优化

## 背景

本地验收时，Vite 在 `5173` 被占用后自动切换到 `127.0.0.1:5174`，而后端 CORS 只允许 `5173`，导致登录接口预检请求被拦截。

## 更新内容

- 后端新增 `SMART_CRM_CORS_ORIGIN_REGEX` 配置，默认允许 `localhost` 和 `127.0.0.1` 的本地开发端口。
- `CORSMiddleware` 同步启用 `allow_origin_regex`，避免 Vite 自动换端口后登录失败。
- 更新 README、英文 README、部署文档和 `.env.example` 的 CORS 配置示例。
- 登录页左侧增加小猪品牌展示、销售状态条和演示态指标卡，减少大屏空白，让左右区域更匹配。
- 使用 Modern Web Guidance 的 `forms` / `css` 指南复核登录表单，补充显式 label/input 绑定、表单字段 `name`、错误提示 `role="alert"`、移动端输入提示和 `focus-visible` 焦点轮廓。

## 验证

- `http://127.0.0.1:5174` 到 `/api/auth/login` 的 CORS 预检返回 200。
- 从 `http://127.0.0.1:5174` 发送登录请求返回 200。
- 新增后端测试覆盖本地动态 Vite 端口 CORS。
- `npm test`、`npm run build`、后端 CORS/health 定向测试通过。
