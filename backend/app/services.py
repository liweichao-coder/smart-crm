from __future__ import annotations

from datetime import date

from fastapi import UploadFile
import httpx

from .config import settings
from .models import Customer, LeadStage, Product, SalesLead
from .schemas import (
    CopilotFollowUpRequest,
    CopilotFollowUpResponse,
    CopilotOpportunityInsight,
    CopilotOrderDraftItem,
    CopilotOrderDraftResponse,
    CopilotSummaryResponse,
    VisionExtractItem,
    VisionExtractResponse,
)


class VisionExtractionService:
    """Local demo extractor with deterministic sample output."""

    async def extract(self, file: UploadFile) -> VisionExtractResponse:
        raw_name = (file.filename or "sample").lower()
        name_hint = "陈敏" if "income" in raw_name else "李强"
        company_hint = "云川医疗" if "income" in raw_name else "星海装备"

        sample_items = [
            VisionExtractItem(product_name="智能巡检终端", quantity=2, unit_price=16800),
            VisionExtractItem(product_name="客户数据接入服务", quantity=1, unit_price=4200),
        ]
        if "deal" in raw_name:
            sample_items = [
                VisionExtractItem(product_name="移动录单套件", quantity=1, unit_price=9800),
                VisionExtractItem(product_name="销售分析大屏授权", quantity=3, unit_price=6800),
            ]

        total = sum(item.quantity * item.unit_price for item in sample_items)
        confidence = 0.91 if "income" in raw_name or "deal" in raw_name else 0.82
        return VisionExtractResponse(
            customer_name=name_hint,
            company=company_hint,
            confidence=confidence,
            summary=f"识别到 {len(sample_items)} 个条目，预估总金额 {total:.0f} 元。",
            items=sample_items,
            suggested_notes=f"AI 于 {date.today().isoformat()} 从图片中提取客户与商品信息，建议人工复核数量与单价。",
        )


class OpenAICompatibleClient:
    async def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, bool]:
        if not settings.llm_api_key:
            return "", True

        endpoint = settings.llm_base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 520,
        }
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except Exception:
            return "", True

        choices = data.get("choices") or []
        if not choices:
            return "", True
        content = choices[0].get("message", {}).get("content", "").strip()
        return content, not bool(content)


class CopilotService:
    stage_weights = {
        LeadStage.new: 20,
        LeadStage.qualified: 42,
        LeadStage.proposal: 62,
        LeadStage.negotiation: 78,
        LeadStage.won: 96,
        LeadStage.lost: 8,
    }

    action_by_stage = {
        LeadStage.new: "补齐预算、决策人和采购时间线，判断是否进入有效商机。",
        LeadStage.qualified: "安排方案演示，确认痛点强度和采购优先级。",
        LeadStage.proposal: "发送 ROI 测算，推动客户确认试点范围和验收口径。",
        LeadStage.negotiation: "准备合同风险清单，明确让步边界并推动采购审批。",
        LeadStage.won: "沉淀赢单复盘，触发续约和增购计划。",
        LeadStage.lost: "记录丢单原因，沉淀竞品和预算信息。",
    }

    def __init__(self) -> None:
        self.llm = OpenAICompatibleClient()

    def build_insight(self, lead: SalesLead) -> CopilotOpportunityInsight:
        today = date.today()
        days_left = (lead.due_date - today).days
        stage_score = self.stage_weights.get(lead.stage, 20)
        amount_score = min(round(lead.expected_amount / 5000), 24)
        urgency_score = 14 if days_left <= 2 else 9 if days_left <= 7 else 4
        ai_score = 5 if lead.ai_assisted else 0
        rule_score = min(stage_score + amount_score + urgency_score + ai_score, 99)
        grade = self.grade_for(rule_score)
        win_rate = max(0.12, min((rule_score - 8) / 100, 0.9))

        reasons = [
            f"阶段 {lead.stage.value} 贡献 {stage_score} 分",
            f"预计金额 {lead.expected_amount:.0f} 元贡献 {amount_score} 分",
            f"距离截止 {days_left} 天贡献 {urgency_score} 分",
        ]
        if lead.ai_assisted:
            reasons.append("已有 AI 辅助记录，补充 5 分")

        return CopilotOpportunityInsight(
            id=lead.id or 0,
            title=lead.title,
            customer_name=lead.customer_name,
            owner=lead.owner,
            region=lead.region,
            expected_amount=lead.expected_amount,
            stage=lead.stage.value,
            due_date=lead.due_date,
            rule_score=rule_score,
            grade=grade,
            win_rate=round(win_rate, 2),
            next_best_action=self.action_by_stage.get(lead.stage, "补充客户信息并制定跟进计划。"),
            score_reasons=reasons,
        )

    def grade_for(self, score: int) -> str:
        if score >= 86:
            return "A"
        if score >= 68:
            return "B"
        if score >= 48:
            return "C"
        return "D"

    async def summarize(self, leads: list[SalesLead]) -> CopilotSummaryResponse:
        insights = sorted((self.build_insight(lead) for lead in leads), key=lambda item: item.rule_score, reverse=True)
        top = insights[0] if insights else None
        forecast_amount = sum(item.expected_amount for item in insights if item.grade in {"A", "B"})
        at_risk_count = sum(1 for item in insights if item.grade == "D" or item.rule_score < 50)
        recommendation = (
            "优先推进 A/B 级商机，同时补齐低分商机的信息缺口。"
            if at_risk_count
            else "当前商机质量较稳，建议集中资源推动高分商机进入合同阶段。"
        )

        fallback = True
        llm_summary = ""
        if insights:
            llm_summary, fallback = await self.llm.complete(
                "你是 CRM 销售主管助手，请用中文输出简洁、可执行的销售复盘建议。",
                "\n".join(
                    f"{item.title}，客户 {item.customer_name}，阶段 {item.stage}，金额 {item.expected_amount:.0f}，评分 {item.rule_score}，建议 {item.next_best_action}"
                    for item in insights[:5]
                ),
            )
        if not llm_summary:
            llm_summary = f"{recommendation} 当前最高优先级为“{top.title if top else '暂无'}”。"

        return CopilotSummaryResponse(
            forecast_amount=forecast_amount,
            at_risk_count=at_risk_count,
            top_opportunity=top,
            recommendation=recommendation,
            llm_summary=llm_summary,
            fallback_used=fallback,
            insights=insights,
        )

    async def follow_up(self, payload: CopilotFollowUpRequest, lead: SalesLead | None = None) -> CopilotFollowUpResponse:
        if lead:
            insight = self.build_insight(lead)
            customer_name = lead.customer_name
            title = lead.title
            stage = lead.stage.value
            expected_amount = lead.expected_amount
            pain_points = [lead.next_action]
        else:
            stage_value = payload.stage or LeadStage.new.value
            synthetic_lead = SalesLead(
                title=payload.opportunity_title or "销售跟进",
                customer_name=payload.customer_name or "目标客户",
                owner="销售人员",
                region="未指定",
                expected_amount=payload.expected_amount,
                stage=LeadStage(stage_value) if stage_value in LeadStage._value2member_map_ else LeadStage.new,
                next_action="; ".join(payload.pain_points) or "补充客户需求",
                due_date=date.today(),
                ai_assisted=True,
            )
            insight = self.build_insight(synthetic_lead)
            customer_name = synthetic_lead.customer_name
            title = synthetic_lead.title
            stage = synthetic_lead.stage.value
            expected_amount = synthetic_lead.expected_amount
            pain_points = payload.pain_points or [synthetic_lead.next_action]

        user_prompt = (
            f"客户：{customer_name}\n商机：{title}\n阶段：{stage}\n预计金额：{expected_amount:.0f}\n"
            f"痛点/上下文：{'、'.join(pain_points)}\n下一步动作：{insight.next_best_action}\n"
            "请输出一段销售跟进话术和一句主管摘要。"
        )
        llm_text, fallback = await self.llm.complete(
            "你是 B2B CRM 销售副驾，输出中文，语气专业、具体、可直接发送给客户。",
            user_prompt,
        )
        if not llm_text:
            llm_text = (
                f"建议围绕“{title}”联系 {customer_name}，先确认当前阶段的关键阻塞，"
                f"再结合 {expected_amount:.0f} 元预期价值说明 ROI。"
            )

        return CopilotFollowUpResponse(
            rule_score=insight.rule_score,
            grade=insight.grade,
            llm_summary=f"{customer_name} 当前处于 {stage} 阶段，建议动作：{insight.next_best_action}",
            message_draft=llm_text,
            next_best_action=insight.next_best_action,
            fallback_used=fallback,
        )

    async def order_draft(
        self,
        customer: Customer,
        products: list[Product],
        business_goal: str,
    ) -> CopilotOrderDraftResponse:
        selected_products = products[:3]
        items = [
            CopilotOrderDraftItem(
                product_id=product.id or 0,
                product_name=product.name,
                quantity=2 if product.category == "硬件" else 1,
                unit_price=product.unit_price,
            )
            for product in selected_products
        ]
        total = sum(item.quantity * item.unit_price for item in items)
        prompt = (
            f"客户：{customer.company}，行业：{customer.industry}，等级：{customer.level}。\n"
            f"业务目标：{business_goal or '推进 CRM 智能化采购'}。\n"
            f"候选商品：{', '.join(item.product_name for item in items)}，合计约 {total:.0f} 元。\n"
            "请生成订单草稿说明，包含推荐理由和复核提醒。"
        )
        llm_summary, fallback = await self.llm.complete(
            "你是 CRM 订单助手，请用中文输出简洁的订单草稿说明。",
            prompt,
        )
        if not llm_summary:
            llm_summary = f"建议为 {customer.company} 生成包含 {len(items)} 个条目的订单草稿，预计金额 {total:.0f} 元。"

        return CopilotOrderDraftResponse(
            customer_id=customer.id or 0,
            customer_name=customer.company,
            items=items,
            suggested_notes=f"AI Copilot 根据客户等级、行业和业务目标生成草稿，预计金额 {total:.0f} 元，提交前请人工复核库存和单价。",
            llm_summary=llm_summary,
            fallback_used=fallback,
        )
