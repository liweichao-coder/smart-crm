# 花和暖 CRM React Frontend

基于 React + Vite 搭建的前端项目骨架，当前目标是实现花和暖 CRM 的页面视觉和基础交互。

## 当前范围

- 组织选择页
- Dashboard 仪表盘
- Leads 线索页
- Contacts 联系人页
- Accounts 客户页
- Opportunities 商机页
- Cases 工单页
- Tasks 任务页
- Sales Goals 目标页

所有页面当前使用前端假数据驱动，未接入后端接口。

## 启动方式

```bash
npm install
npm run dev
```

默认开发地址： http://localhost:5173

## 构建

```bash
npm run build
```

## 项目说明

- 路由基于 react-router-dom
- 图标基于 lucide-react
- 参考项目的共享 CSS 和图片资源位于 src/assets/vendor
- 自定义页面结构和假数据逻辑分别集中在 src/App.jsx 和 src/data/mockData.js

## 下一步建议

- 接入真实 API 和鉴权
- 将通用卡片、表格、看板拆为独立组件
- 把筛选、分页、列显示等状态同步到 URL 参数
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
