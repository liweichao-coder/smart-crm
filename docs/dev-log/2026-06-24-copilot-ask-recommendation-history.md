# 2026-06-24 CRM Skill 问答推荐历史闭环

## 背景

CRM Skill 经营问答已经可以基于真实客户、互动、商机、订单、任务、工单和推荐历史生成回答，但此前结果只进入 AI 审计。为了让它更接近可复盘、可执行的智能 CRM，本轮把问答结果沉淀为 Copilot 推荐历史。

## 代码更新

- `POST /api/copilot/ask` 响应新增 `recommendation_id`。
- 经营问答结果写入 `CopilotRecommendation(source=ask)`，保留问题、回答、证据片段、下一步动作、LLM/兜底状态和模型名称。
- 经营问答推荐复用已有推荐反馈和推荐转任务接口，可进入 AI 质量报表的推荐转任务率、人工好评率等指标。
- 前端问答结果显示“推荐历史 #ID”，问答成功后自动刷新推荐历史，历史卡片把 `ask` 显示为“经营问答”。
- pytest 扩展经营问答用例，覆盖问答历史、人工反馈、转任务、AI 审计和业务审计。

## 验证

- `npm run lint`：通过。
- `npm test -- --run`：51 passed。
- `backend\.venv\Scripts\python.exe -m pytest`：56 passed。
- `npm run build`：通过。
- 后端目录执行 `.\.venv\Scripts\python.exe -m app.manage doctor`：演示数据规模达标，consistency ok / issues 0。

## 报告同步

- 已同步 README、需求、产品设计、接口、实现说明、使用手册、迭代总结、测试文档和答辩脚本。
- 后续截图建议补一张“CRM Skill 经营问答显示推荐历史编号”和一张“推荐历史中经营问答记录可反馈/转任务”。
