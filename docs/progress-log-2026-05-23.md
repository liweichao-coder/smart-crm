# 2026-05-23 Progress Log

## GitHub 进度

- `origin/main` 暂无新提交，本地 `main` 原本领先 1 个提交：`289d7a0 chore: rename private docs directory`。
- 新发现远端分支：`origin/yanda`。
- `origin/yanda` 带来根目录 React + Vite 前端重构，包含登录、组织选择、仪表盘、线索、联系人、客户、商机、工单、任务、销售目标等页面。
- 合并时远端分支被 Git 判定为 unrelated history，因此使用合并提交引入；冲突仅在 `.gitignore` 与 `README.md`。

## 功能审阅

- 新前端视觉和基础导航较完整，但仍以 mock 数据为主。
- 原有 `backend/` FastAPI API、SQLite 数据库、AI 订单草稿和后端测试已保留。
- 前后端尚未统一到新根目录前端，下一步重点应是把 mock 数据逐步接入真实 API。
- 新前端原本的 `新建...` 主按钮只展示按钮，不会产生业务数据。
- ESLint 原配置会扫描旧前端构建产物 `frontend/dist`，导致 lint 失败。

## 本次完善

- 合并 `origin/yanda` 的根目录 React 前端，同时保留本地 FastAPI 后端。
- 整理 README，说明当前根目录前端、旧 `frontend/` 参考目录和 `backend/` 后端的关系。
- 修复 ESLint 忽略规则，避免扫描构建产物。
- 给客户、联系人、线索、商机、工单等资源页补充“快速创建”弹窗。
- 新建记录会进入当前页面列表；看板资源会保留阶段字段并可选择阶段。
- 抽出 `src/resourceUtils.js`，并增加 `src/resourceUtils.test.js` 覆盖表单默认值和金额归一化。

## 验证记录

- `npm run lint`: 通过
- `npm test`: 通过，3 个前端工具函数测试
- `npm run build`: 通过
- `backend/.venv/Scripts/python.exe -m pytest`: 通过，3 个后端 API 测试
- 浏览器冒烟：登录、选择组织、进入商机页、创建“南山续约增长包”，列表成功新增且弹窗关闭

## 后续建议

- 先接入 `GET /api/dashboard`、`GET /api/customers`、`GET /api/leads`、`GET /api/orders`。
- 再把“快速创建”从前端临时状态改为调用真实 POST API。
- 补充 Playwright 或 React Testing Library 的页面级测试，覆盖登录、组织选择、资源新建和搜索。
