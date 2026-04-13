# Smart CRM

一个用于课程设计演示的智能销售管理系统，包含：
- React + TypeScript 前端管理台
- FastAPI + SQLite 后端 API
- 本地可运行的 AI 智能录单演示流程

## 功能概览
- 经营总览：查看订单额、AI 订单数、商机数、客户数
- 商机跟进：查看销售商机、负责人、阶段、下一动作
- 客户资产：查看客户公司、联系人、来源、分级
- 商品目录：查看商品、SKU、价格、库存
- 订单中心：查看订单列表和 AI/手工来源标记
- 智能录单：上传图片后生成订单草稿，人工确认后提交

## 环境要求
- Node.js 20+
- npm 10+
- Python 3.12

## 快速开始

### 1. 启动后端
```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端启动后，可访问：
```text
http://127.0.0.1:8000/health
```

### 2. 启动前端
新开一个 PowerShell 窗口：

```powershell
cd D:\LwcCode\personal-project\smart-crm\frontend
npm install
npm run dev
```

前端默认地址：
```text
http://127.0.0.1:5173
```

## 测试项目是否正常

### 后端测试
```powershell
cd D:\LwcCode\personal-project\smart-crm\backend
.\.venv\Scripts\python.exe -m pytest
```

### 前端构建测试
```powershell
cd D:\LwcCode\personal-project\smart-crm\frontend
npm run build
```

## 体验建议
1. 打开首页，查看仪表盘数据。
2. 切换到“订单中心”，确认已有演示数据。
3. 切换到“智能录单”。
4. 上传一张图片测试 AI 录单流程。
5. 检查草稿内容后点击“确认并创建订单”。
6. 返回订单中心查看新订单。

## 当前实现边界
- 后端 API、数据库、订单创建、库存扣减已经真实实现。
- 前后端联调已经打通。
- AI 录单流程已经打通，但当前视觉识别仍是本地模拟逻辑，不是真实大模型。
- 登录鉴权、完整 CRUD、复杂报表仍未完成。

## 目录结构
- `frontend/`: 前端项目
- `backend/`: 后端项目
- `_private/`: 本地内部资料目录，不参与本次代码仓库提交
