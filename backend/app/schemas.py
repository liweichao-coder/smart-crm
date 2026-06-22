from __future__ import annotations

from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .models import LeadStage, OrderStatus

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_previous: bool


class AuthOrganizationRead(BaseModel):
    id: int
    name: str
    slug: str
    role: str
    plan: str
    status: str


class AuthUserRead(BaseModel):
    id: int
    organization_id: int
    organization_name: str
    full_name: str
    email: str
    phone: str
    role: str
    data_scope: str
    position: str
    department: str
    location: str
    status: str
    permissions: list[str]
    created_at: datetime
    last_login_at: datetime | None = None


class AuthLoginRequest(BaseModel):
    account: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AuthRegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2)
    full_name: str = Field(min_length=2)
    email: str = Field(min_length=5)
    phone: str = ""
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)


class AuthSessionResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: AuthUserRead
    organizations: list[AuthOrganizationRead]


class AuthMeResponse(BaseModel):
    expires_at: datetime
    user: AuthUserRead
    organizations: list[AuthOrganizationRead]


class AuthLogoutResponse(BaseModel):
    revoked: bool


class PermissionCatalogItem(BaseModel):
    key: str
    label: str
    category: str
    description: str


class RolePermissionRead(BaseModel):
    role: str
    description: str
    data_scope: str
    permissions: list[str]
    granted_count: int
    all_permissions: bool


class ModulePermissionRead(BaseModel):
    path: str
    label: str
    permission: str
    roles: list[str]


class PermissionMatrixResponse(BaseModel):
    generated_at: datetime
    current_role: str
    permission_catalog: list[PermissionCatalogItem]
    roles: list[RolePermissionRead]
    modules: list[ModulePermissionRead]


class AuthAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event: str
    account: str
    user_id: int | None
    organization_id: int | None
    status: str
    detail: str
    created_at: datetime


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


class CustomerUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    industry: str | None = None
    city: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    source: str | None = None
    level: str | None = None
    annual_revenue: float | None = Field(default=None, ge=0)
    status: str | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    category: str
    unit_price: float
    stock: int


class ProductCreate(BaseModel):
    name: str
    sku: str
    category: str = "软件"
    unit_price: float = Field(gt=0)
    stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    category: str | None = None
    unit_price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)


class InventoryRestockAlertRead(BaseModel):
    product_id: int
    name: str
    sku: str
    category: str
    unit_price: float
    current_stock: int
    priority: str
    danger_threshold: int
    warning_threshold: int
    recent_order_quantity: int
    recommended_restock: int
    reason: str


class NotificationRead(BaseModel):
    id: str
    category: str
    severity: str
    title: str
    message: str
    href: str
    action_label: str
    entity_type: str
    entity_id: int | None = None
    created_at: datetime


class ProductRestockRequest(BaseModel):
    quantity: int = Field(ge=1, le=100000)
    reason: str = "低库存补货"
    operator: str = "李伟超"


class InventoryMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    sku: str
    change_quantity: int
    before_stock: int
    after_stock: int
    reason: str
    operator: str
    source: str
    created_at: datetime


class ProductRestockResponse(BaseModel):
    product: ProductRead
    movement: InventoryMovementRead
    alert: InventoryRestockAlertRead | None = None


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


class ContactUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    owner: str | None = None
    status: str | None = None


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


class SalesLeadUpdate(BaseModel):
    title: str | None = None
    customer_name: str | None = None
    owner: str | None = None
    region: str | None = None
    expected_amount: float | None = Field(default=None, ge=0)
    stage: LeadStage | None = None
    next_action: str | None = None
    due_date: date | None = None
    ai_assisted: bool | None = None


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


class SupportCaseUpdate(BaseModel):
    title: str | None = None
    account: str | None = None
    owner: str | None = None
    priority: str | None = None
    status: str | None = None
    status_label: str | None = None
    due_date: date | None = None


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


class TaskItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    owner: str | None = None
    due_date: str | None = None
    priority: str | None = None
    status: str | None = None
    status_label: str | None = None


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


class SalesGoalUpdate(BaseModel):
    name: str | None = None
    period: str | None = None
    current: float | None = Field(default=None, ge=0)
    target: float | None = Field(default=None, ge=0)
    progress: int | None = Field(default=None, ge=0, le=100)
    note: str | None = None


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


class BusinessAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    entity_type: str
    entity_id: int | None
    operator: str
    status: str
    summary: str
    detail: str
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


class SalesOrderUpdate(BaseModel):
    owner: str | None = None
    region: str | None = None
    status: OrderStatus | None = None
    due_date: date | None = None
    notes: str | None = None
    items: list[OrderItemPayload] | None = None


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


class SalesReportBreakdown(BaseModel):
    name: str
    revenue: float
    order_count: int
    ai_order_count: int
    average_order_value: float
    pipeline_amount: float
    open_leads: int


class SalesReportFunnelStage(BaseModel):
    stage: str
    label: str
    lead_count: int
    expected_amount: float
    share: float


class SalesReportAiImpact(BaseModel):
    ai_order_count: int
    manual_order_count: int
    ai_revenue: float
    manual_revenue: float
    average_ai_confidence: float
    ai_revenue_ratio: float


class SalesPerformanceReportResponse(BaseModel):
    generated_at: datetime
    metrics: list[DashboardMetric]
    revenue_trend: list[RevenuePoint]
    owner_performance: list[SalesReportBreakdown]
    region_performance: list[SalesReportBreakdown]
    funnel: list[SalesReportFunnelStage]
    ai_impact: SalesReportAiImpact
    inventory_risks: list[InventoryRestockAlertRead]
    applied_filters: dict[str, str]


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


class CopilotRecommendationRead(BaseModel):
    id: int
    source: str
    lead_id: int | None = None
    lead_title: str
    customer_name: str
    owner: str
    region: str
    stage: str
    grade: str
    rule_score: int = Field(ge=0, le=100)
    win_rate: float = Field(ge=0, le=1)
    expected_amount: float
    next_best_action: str
    score_reasons: list[str]
    llm_summary: str
    message_draft: str
    fallback_used: bool
    model: str
    created_at: datetime


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
