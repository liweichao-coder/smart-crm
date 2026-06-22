from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import LeadStage, OrderStatus


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str
    industry: str
    city: str
    contact_person: str
    phone: str
    email: str
    source: str
    level: str
    annual_revenue: float
    status: str
    created_at: datetime


class CustomerCreate(BaseModel):
    name: str = ""
    company: str
    industry: str = "待补充"
    city: str = "深圳"
    contact_person: str = ""
    phone: str = "13800000000"
    email: str = "customer@example.com"
    source: str = "课程演示"
    level: str = "B"
    annual_revenue: float = Field(default=0, ge=0)
    status: str = "active"


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    category: str
    unit_price: float
    stock: int


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str
    role: str
    email: str
    phone: str
    owner: str
    status: str
    created_at: datetime


class ContactCreate(BaseModel):
    name: str
    company: str
    role: str = "待确认"
    email: str = "contact@example.com"
    phone: str = "13800000000"
    owner: str = "未分配"
    status: str = "active"


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    customer_name: str
    owner: str
    region: str
    expected_amount: float
    stage: LeadStage
    next_action: str
    due_date: date
    ai_assisted: bool
    created_at: datetime


class SalesLeadCreate(BaseModel):
    title: str
    customer_name: str
    owner: str
    region: str = "华南"
    expected_amount: float = Field(default=0, ge=0)
    stage: LeadStage = LeadStage.new
    next_action: str = "安排下一步跟进"
    due_date: date = Field(default_factory=date.today)
    ai_assisted: bool = False


class SupportCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    account: str
    owner: str
    priority: str
    status: str
    status_label: str
    due_date: date
    created_at: datetime


class SupportCaseCreate(BaseModel):
    title: str
    account: str
    owner: str
    priority: str = "warm"
    status: str = "open"
    status_label: str = "Open"
    due_date: date = Field(default_factory=date.today)


class TaskItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    owner: str
    due_date: str
    priority: str
    status: str
    status_label: str
    created_at: datetime


class TaskItemCreate(BaseModel):
    title: str
    description: str = ""
    owner: str
    due_date: str = "今天 18:00"
    priority: str = "warm"
    status: str = "week"
    status_label: str = "本周"


class SalesGoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    period: str
    current: float
    target: float
    progress: int
    note: str
    created_at: datetime


class SalesGoalCreate(BaseModel):
    name: str
    period: str = "2026 Q2"
    current: float = Field(default=0, ge=0)
    target: float = Field(default=1, ge=0)
    progress: int | None = Field(default=None, ge=0, le=100)
    note: str = ""


class AIInteractionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    operation: str
    provider: str
    model: str
    status: str
    fallback_used: bool
    latency_ms: int
    entity_type: str
    entity_id: int | None
    request_summary: str
    response_summary: str
    created_at: datetime


class OrderItemPayload(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    unit_price: float = Field(gt=0)


class SalesOrderCreate(BaseModel):
    customer_id: int
    owner: str
    region: str
    currency: str = "CNY"
    status: OrderStatus = OrderStatus.draft
    order_date: date
    due_date: date
    notes: str = ""
    created_by_ai: bool = False
    ai_confidence_score: float = Field(default=0, ge=0, le=1)
    items: list[OrderItemPayload]


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    line_total: float


class SalesOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    customer_name: str
    owner: str
    region: str
    currency: str
    status: OrderStatus
    order_date: date
    due_date: date
    notes: str
    created_by_ai: bool
    ai_confidence_score: float
    total_amount: float
    created_at: datetime
    items: list[OrderItemRead]


class DashboardMetric(BaseModel):
    label: str
    value: str
    hint: str


class RevenuePoint(BaseModel):
    month: str
    revenue: float


class DashboardResponse(BaseModel):
    metrics: list[DashboardMetric]
    revenue_trend: list[RevenuePoint]
    stage_distribution: list[dict[str, int | str]]
    ai_orders_ratio: float
    urgent_leads: list[LeadRead]
    recent_orders: list[SalesOrderRead]


class VisionExtractItem(BaseModel):
    product_name: str
    quantity: int
    unit_price: float


class VisionExtractResponse(BaseModel):
    customer_name: str
    company: str
    confidence: float = Field(ge=0, le=1)
    summary: str
    items: list[VisionExtractItem]
    suggested_notes: str
    fallback_used: bool = False
    source: str = "llm_vision"
    raw_text_excerpt: str = ""


class CopilotOpportunityInsight(BaseModel):
    id: int
    title: str
    customer_name: str
    owner: str
    region: str
    expected_amount: float
    stage: str
    due_date: date
    rule_score: int = Field(ge=0, le=100)
    grade: str
    win_rate: float = Field(ge=0, le=1)
    next_best_action: str
    score_reasons: list[str]


class CopilotSummaryResponse(BaseModel):
    forecast_amount: float
    at_risk_count: int
    top_opportunity: CopilotOpportunityInsight | None
    recommendation: str
    llm_summary: str
    fallback_used: bool
    insights: list[CopilotOpportunityInsight]


class CopilotFollowUpRequest(BaseModel):
    lead_id: int | None = None
    customer_name: str = ""
    opportunity_title: str = ""
    stage: str = ""
    pain_points: list[str] = Field(default_factory=list)
    expected_amount: float = 0


class CopilotFollowUpResponse(BaseModel):
    rule_score: int = Field(ge=0, le=100)
    grade: str
    llm_summary: str
    message_draft: str
    next_best_action: str
    fallback_used: bool


class CopilotOrderDraftRequest(BaseModel):
    customer_id: int
    product_ids: list[int] = Field(default_factory=list)
    business_goal: str = ""


class CopilotOrderDraftItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(gt=0)


class CopilotOrderDraftResponse(BaseModel):
    customer_id: int
    customer_name: str
    items: list[CopilotOrderDraftItem]
    suggested_notes: str
    llm_summary: str
    fallback_used: bool
