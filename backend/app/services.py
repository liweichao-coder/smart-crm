from __future__ import annotations

import base64
import json
import re
from datetime import date
from typing import Any

from fastapi import UploadFile
import httpx

from .config import settings
from .models import Contact, CopilotRecommendation, Customer, CustomerActivity, LeadStage, Product, SalesLead, SalesOrder, SupportCase, TaskItem
from .schemas import (
    CustomerAccountPlanResponse,
    CopilotAskResponse,
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
    """Extract order draft fields from uploaded text or image files."""

    def __init__(self) -> None:
        self.llm = OpenAICompatibleClient()

    async def extract(
        self,
        file: UploadFile,
        customers: list[Customer],
        products: list[Product],
    ) -> VisionExtractResponse:
        raw_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"
        filename = file.filename or "uploaded-order"
        text = self.decode_text(raw_bytes, content_type, filename)

        model_response = ""
        fallback_used = True
        if settings.llm_api_key:
            model_response, fallback_used = await self.llm.complete_messages(
                messages=self.build_messages(
                    raw_bytes=raw_bytes,
                    content_type=content_type,
                    filename=filename,
                    text=text,
                    customers=customers,
                    products=products,
                ),
                model=settings.llm_vision_model or settings.llm_model,
                max_tokens=900,
            )

        if model_response:
            parsed_payload = self.parse_json_payload(model_response)
            if parsed_payload:
                return self.build_response(
                    payload=parsed_payload,
                    customers=customers,
                    products=products,
                    fallback_used=fallback_used,
                    source="llm_vision" if self.is_image(content_type, filename) else "llm_text",
                    raw_text=text,
                )

        parsed_payload = self.parse_text_payload(text, customers, products)
        return self.build_response(
            payload=parsed_payload,
            customers=customers,
            products=products,
            fallback_used=True,
            source="local_text_parser" if text else "catalog_fallback",
            raw_text=text,
        )

    def build_messages(
        self,
        raw_bytes: bytes,
        content_type: str,
        filename: str,
        text: str,
        customers: list[Customer],
        products: list[Product],
    ) -> list[dict[str, Any]]:
        product_catalog = "\n".join(f"- {product.name} / {product.sku} / {product.unit_price:.0f} 元" for product in products)
        customer_catalog = "\n".join(f"- {customer.company} / 联系人 {customer.contact_person}" for customer in customers)
        instruction = (
            "请从上传的订单图片、截图、报价单或文本中抽取 CRM 订单草稿。"
            "只返回 JSON，不要 Markdown。JSON 字段：customer_name, company, confidence, summary, "
            "suggested_notes, items。items 内每项包含 product_name, quantity, unit_price。"
            "商品名称和单价优先从商品目录中匹配；数量从上传内容中读取；无法确认时数量为 1，confidence 降低。"
            f"\n\n客户目录：\n{customer_catalog}\n\n商品目录：\n{product_catalog}\n\n文件名：{filename}"
        )

        if self.is_image(content_type, filename):
            image_url = f"data:{content_type};base64,{base64.b64encode(raw_bytes).decode('ascii')}"
            return [
                {"role": "system", "content": "你是 CRM 多模态订单录入助手，擅长从图片中抽取结构化订单草稿。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ]

        return [
            {"role": "system", "content": "你是 CRM 订单录入助手，擅长从中文报价文本中抽取结构化订单草稿。"},
            {"role": "user", "content": f"{instruction}\n\n上传文本：\n{text[:8000]}"},
        ]

    def decode_text(self, raw_bytes: bytes, content_type: str, filename: str) -> str:
        lower_name = filename.lower()
        is_text_file = (
            content_type.startswith("text/")
            or lower_name.endswith((".txt", ".csv", ".md", ".json", ".log"))
        )
        if not is_text_file:
            return ""

        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                return raw_bytes.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        return raw_bytes.decode("utf-8", errors="ignore").strip()

    def parse_json_payload(self, model_response: str) -> dict[str, Any] | None:
        cleaned = model_response.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            payload = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def parse_text_payload(
        self,
        text: str,
        customers: list[Customer],
        products: list[Product],
    ) -> dict[str, Any]:
        matched_customer = self.match_customer(text, customers)
        items: list[dict[str, Any]] = []
        for product in products:
            if product.name in text or product.sku in text:
                quantity = self.extract_quantity(text, product)
                items.append(
                    {
                        "product_name": product.name,
                        "quantity": quantity,
                        "unit_price": product.unit_price,
                    }
                )

        if not items:
            items = self.parse_generic_items(text)

        if not items and products:
            items = [
                {
                    "product_name": products[0].name,
                    "quantity": 1,
                    "unit_price": products[0].unit_price,
                }
            ]

        return {
            "customer_name": matched_customer.contact_person if matched_customer else "",
            "company": matched_customer.company if matched_customer else "",
            "confidence": 0.74 if text and items else 0.42,
            "items": items,
            "summary": "",
            "suggested_notes": "",
        }

    def parse_generic_items(self, text: str) -> list[dict[str, Any]]:
        items = []
        pattern = re.compile(r"(?P<name>[\u4e00-\u9fa5A-Za-z0-9-]{3,40})\s*[x×*]\s*(?P<quantity>\d+)(?:\D{0,8}(?P<price>\d+(?:\.\d+)?))?")
        for match in pattern.finditer(text):
            price = float(match.group("price") or 1)
            items.append(
                {
                    "product_name": match.group("name"),
                    "quantity": int(match.group("quantity")),
                    "unit_price": price,
                }
            )
        return items[:8]

    def build_response(
        self,
        payload: dict[str, Any],
        customers: list[Customer],
        products: list[Product],
        fallback_used: bool,
        source: str,
        raw_text: str,
    ) -> VisionExtractResponse:
        company = str(payload.get("company") or "").strip()
        customer_name = str(payload.get("customer_name") or "").strip()
        matched_customer = self.match_customer(f"{company} {customer_name} {raw_text}", customers)
        if matched_customer:
            company = company or matched_customer.company
            if not customer_name or customer_name == company or customer_name == matched_customer.company:
                customer_name = matched_customer.contact_person
        if not company:
            company = "待复核客户"
        if not customer_name:
            customer_name = matched_customer.contact_person if matched_customer else "待复核联系人"

        items = self.normalize_items(payload.get("items") or [], products)
        if not items and products:
            items = [VisionExtractItem(product_name=products[0].name, quantity=1, unit_price=products[0].unit_price)]

        confidence = self.clamp_confidence(payload.get("confidence"), fallback_used)
        total = sum(item.quantity * item.unit_price for item in items)
        summary = str(payload.get("summary") or "").strip()
        if not summary:
            summary = f"抽取到 {len(items)} 个订单条目，预估总金额 {total:.0f} 元。"

        suggested_notes = str(payload.get("suggested_notes") or "").strip()
        if not suggested_notes:
            suggested_notes = (
                f"AI 于 {date.today().isoformat()} 生成订单草稿；来源 {source}。"
                "提交订单前请人工复核客户、数量、单价和库存。"
            )

        return VisionExtractResponse(
            customer_name=customer_name,
            company=company,
            confidence=confidence,
            summary=summary,
            items=items,
            suggested_notes=suggested_notes,
            fallback_used=fallback_used,
            source=source,
            raw_text_excerpt=raw_text[:500],
        )

    def normalize_items(self, items: list[Any], products: list[Product]) -> list[VisionExtractItem]:
        normalized = []
        for item in items:
            if not isinstance(item, dict):
                continue
            product_name = str(item.get("product_name") or item.get("name") or "").strip()
            matched_product = self.match_product(product_name, products)
            quantity = self.to_int(item.get("quantity"), default=1)
            unit_price = self.to_float(item.get("unit_price"), default=matched_product.unit_price if matched_product else 1)
            normalized.append(
                VisionExtractItem(
                    product_name=matched_product.name if matched_product else product_name or "待复核商品",
                    quantity=max(quantity, 1),
                    unit_price=max(unit_price, 0.01),
                )
            )
        return normalized[:12]

    def match_customer(self, text: str, customers: list[Customer]) -> Customer | None:
        for customer in customers:
            if customer.company in text or customer.contact_person in text or customer.name in text:
                return customer
        return None

    def match_product(self, product_name: str, products: list[Product]) -> Product | None:
        for product in products:
            if product.name == product_name or product.sku == product_name:
                return product
        for product in products:
            if product_name and (product_name in product.name or product.name in product_name):
                return product
        return None

    def extract_quantity(self, text: str, product: Product) -> int:
        escaped_terms = [re.escape(product.name), re.escape(product.sku)]
        pattern = re.compile(rf"({'|'.join(escaped_terms)}).{{0,30}}?(?:x|×|\*|数量[:：]?)\s*(\d+)", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return max(int(match.group(2)), 1)
        return 1

    def clamp_confidence(self, value: Any, fallback_used: bool) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            confidence = 0.72 if fallback_used else 0.86
        return max(0.1, min(confidence, 0.98))

    def to_int(self, value: Any, default: int) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def to_float(self, value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def is_image(self, content_type: str, filename: str) -> bool:
        lower_name = filename.lower()
        return content_type.startswith("image/") or lower_name.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp"))


class OpenAICompatibleClient:
    async def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, bool]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.complete_messages(messages=messages, model=settings.llm_model, max_tokens=520)

    async def complete_messages(
        self,
        messages: list[dict[str, Any]],
        model: str,
        max_tokens: int,
    ) -> tuple[str, bool]:
        if not settings.llm_api_key:
            return "", True

        endpoint = settings.llm_base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": max_tokens,
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

    async def ask(
        self,
        question: str,
        customers: list[Customer],
        activities: list[CustomerActivity],
        leads: list[SalesLead],
        orders: list[SalesOrder],
        tasks: list[TaskItem],
        cases: list[SupportCase],
        recommendations: list[CopilotRecommendation],
    ) -> CopilotAskResponse:
        open_leads = [lead for lead in leads if lead.stage not in {LeadStage.won, LeadStage.lost}]
        top_leads = sorted(open_leads, key=lambda item: item.expected_amount, reverse=True)[:5]
        risk_activities = [activity for activity in activities if activity.sentiment in {"risk", "negative"}][:5]
        overdue_tasks = [task for task in tasks if task.status == "overdue"][:5]
        pending_cases = [case for case in cases if case.status not in {"resolved", "closed"}][:5]
        total_revenue = sum(order.total_amount for order in orders)
        pipeline_amount = sum(lead.expected_amount for lead in open_leads)

        evidence = [
            f"客户 {len(customers)} 个，累计订单收入 {total_revenue:.0f} 元，在管商机 {len(open_leads)} 个，管道金额 {pipeline_amount:.0f} 元。",
            f"最高金额商机：{top_leads[0].title} / {top_leads[0].customer_name} / {top_leads[0].expected_amount:.0f} 元。" if top_leads else "当前没有在管商机。",
            f"风险互动 {len(risk_activities)} 条，逾期任务 {len(overdue_tasks)} 条，未关闭工单 {len(pending_cases)} 条。",
        ]
        if recommendations:
            latest_recommendation = recommendations[0]
            evidence.append(f"最近 Copilot 建议：{latest_recommendation.next_best_action or latest_recommendation.llm_summary}")

        next_actions = []
        for lead in top_leads:
            if lead.next_action:
                next_actions.append(f"{lead.customer_name}：{lead.next_action}")
        for activity in risk_activities:
            if activity.next_action:
                next_actions.append(f"{activity.customer_name}：{activity.next_action}")
        for task in overdue_tasks:
            next_actions.append(f"{task.owner}：处理逾期任务“{task.title}”")
        if not next_actions:
            next_actions.append("筛选 A/B 级商机，安排一次客户复盘会议并确认预算、决策人和时间点。")

        context = "\n".join(
            [
                f"用户问题：{question}",
                f"客户概览：{len(customers)} 个客户，订单 {len(orders)} 张，累计收入 {total_revenue:.0f} 元。",
                f"商机：{len(open_leads)} 个在管，管道金额 {pipeline_amount:.0f} 元。",
                "重点商机：" + "；".join(f"{lead.title}/{lead.customer_name}/{lead.stage.value}/{lead.expected_amount:.0f}/{lead.next_action}" for lead in top_leads),
                "风险互动：" + "；".join(f"{activity.customer_name}/{activity.subject}/{activity.sentiment}/{activity.next_action}" for activity in risk_activities),
                "逾期任务：" + "；".join(f"{task.owner}/{task.title}/{task.due_date}" for task in overdue_tasks),
                "未关闭工单：" + "；".join(f"{case.account}/{case.title}/{case.priority}/{case.due_date}" for case in pending_cases),
                "最近建议：" + "；".join((item.next_best_action or item.llm_summary) for item in recommendations[:5]),
            ]
        )
        answer, fallback = await self.llm.complete(
            "你是 Smart CRM 的销售经营问答 Copilot。必须只基于提供的 CRM 数据回答，中文输出，先给结论，再给2到4条行动建议；不要编造不存在的客户、金额或任务。",
            context,
        )
        if not answer:
            answer = (
                f"基于当前 CRM 数据，优先关注 {len(open_leads)} 个在管商机和 {len(risk_activities)} 条风险互动。"
                f"管道金额约 {pipeline_amount:.0f} 元，建议先推进最高金额商机，并处理逾期任务和未关闭工单。"
            )

        return CopilotAskResponse(
            question=question,
            answer=answer,
            next_actions=next_actions[:5],
            evidence=evidence[:5],
            fallback_used=fallback,
            model=settings.llm_model,
        )

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

    async def account_plan(
        self,
        customer: Customer,
        contacts: list[Contact],
        activities: list[CustomerActivity],
        leads: list[SalesLead],
        orders: list[SalesOrder],
        cases: list[SupportCase],
        recommendations: list[CopilotRecommendation],
    ) -> CustomerAccountPlanResponse:
        open_leads = [lead for lead in leads if lead.stage not in {LeadStage.won, LeadStage.lost}]
        won_leads = [lead for lead in leads if lead.stage == LeadStage.won]
        active_cases = [case for case in cases if case.status not in {"resolved", "closed"}]
        total_revenue = sum(order.total_amount for order in orders)
        pipeline_amount = sum(lead.expected_amount for lead in open_leads)
        latest_recommendations = [item.next_best_action for item in recommendations if item.next_best_action][:3]
        latest_activities = activities[:4]
        risk_activities = [activity for activity in activities if activity.sentiment in {"risk", "negative"}]

        context = (
            f"客户：{customer.company}\n"
            f"行业：{customer.industry}；等级：{customer.level}；城市：{customer.city}；负责人：{customer.owner}\n"
            f"联系人：{len(contacts)} 位，关键联系人：{', '.join(contact.name + '/' + contact.role for contact in contacts[:4]) or '暂无'}\n"
            f"最近互动：{len(activities)} 条，"
            f"{'；'.join(activity.subject + '/' + activity.outcome for activity in latest_activities) or '暂无'}\n"
            f"订单：{len(orders)} 张，累计收入 {total_revenue:.0f} 元\n"
            f"在管商机：{len(open_leads)} 个，管道金额 {pipeline_amount:.0f} 元；已赢单商机 {len(won_leads)} 个\n"
            f"未关闭工单：{len(active_cases)} 个\n"
            f"Copilot 最近建议：{'；'.join(latest_recommendations) or '暂无'}\n"
            "请输出一段 80 字以内的客户经营摘要，包含关系状态、收入机会和当前风险。"
        )
        llm_summary, fallback = await self.llm.complete(
            "你是 B2B CRM 客户成功和销售主管助手，请基于真实 CRM 数据输出中文客户经营摘要。",
            context,
        )

        if not llm_summary:
            llm_summary = (
                f"{customer.company} 当前累计收入 {total_revenue:.0f} 元，在管商机 {len(open_leads)} 个，"
                f"未关闭工单 {len(active_cases)} 个，建议围绕高价值商机和服务风险同步推进。"
            )

        expansion_paths = []
        if open_leads:
            top_lead = max(open_leads, key=lambda item: item.expected_amount)
            expansion_paths.append(f"推进“{top_lead.title}”进入下一阶段，预计增量 {top_lead.expected_amount:.0f} 元。")
        if orders:
            expansion_paths.append("基于历史订单复购同类软件服务，优先复核续费和增购窗口。")
        if contacts:
            expansion_paths.append(f"围绕 {contacts[0].name} 建立多联系人关系图，补齐采购、技术和财务角色。")
        if not expansion_paths:
            expansion_paths.append("先补齐关键联系人和需求背景，再生成可执行商机。")

        risks = []
        if active_cases:
            risks.append(f"存在 {len(active_cases)} 个未关闭工单，需避免服务问题影响成交。")
        if risk_activities:
            risks.append(f"最近 {len(risk_activities)} 条互动带有风险信号，需复核异议和承诺事项。")
        if not contacts:
            risks.append("缺少联系人沉淀，客户关系稳定性不足。")
        if pipeline_amount == 0:
            risks.append("当前没有在管商机，客户经营可能停留在存量维护。")
        if not risks:
            risks.append("暂无高危服务阻塞，重点风险在于商机推进节奏。")

        next_actions = latest_recommendations[:]
        for activity in activities:
            if activity.next_action and activity.next_action not in next_actions:
                next_actions.append(activity.next_action)
                break
        if open_leads:
            next_actions.append(max(open_leads, key=lambda item: item.expected_amount).next_action)
        if active_cases:
            next_actions.append(f"先关闭工单“{active_cases[0].title}”，再推进商务沟通。")
        if len(next_actions) < 3:
            next_actions.append("安排一次客户复盘会议，确认预算、决策人和下一步时间点。")

        return CustomerAccountPlanResponse(
            summary=llm_summary,
            expansion_paths=expansion_paths[:4],
            risks=risks[:4],
            next_actions=next_actions[:4],
            fallback_used=fallback,
            model=settings.llm_model,
        )
