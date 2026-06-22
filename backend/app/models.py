from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class LeadStage(str, Enum):
    new = "new"
    qualified = "qualified"
    proposal = "proposal"
    negotiation = "negotiation"
    won = "won"
    lost = "lost"


class OrderStatus(str, Enum):
    draft = "draft"
    confirmed = "confirmed"
    fulfilled = "fulfilled"


class OrderApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class OrganizationBase(SQLModel):
    name: str = Field(index=True)
    slug: str = Field(index=True, sa_column_kwargs={"unique": True})
    plan: str = "course"
    status: str = Field(default="active", index=True)


class Organization(OrganizationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class AuthUserBase(SQLModel):
    organization_id: int = Field(foreign_key="organization.id", index=True)
    full_name: str
    email: str = Field(index=True, sa_column_kwargs={"unique": True})
    phone: str = Field(default="", index=True)
    role: str = "管理员"
    position: str = "CRM 运营管理员"
    department: str = "客户增长中心"
    location: str = "深圳 · 南山"
    status: str = Field(default="active", index=True)
    password_hash: str


class AuthUser(AuthUserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class AuthSessionBase(SQLModel):
    user_id: int = Field(foreign_key="authuser.id", index=True)
    token_hash: str = Field(index=True, sa_column_kwargs={"unique": True})
    expires_at: datetime
    revoked_at: Optional[datetime] = None


class AuthSession(AuthSessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class AuthAuditLogBase(SQLModel):
    event: str = Field(index=True)
    account: str = Field(index=True)
    user_id: Optional[int] = Field(default=None, index=True)
    organization_id: Optional[int] = Field(default=None, index=True)
    status: str = Field(default="success", index=True)
    detail: str = ""


class AuthAuditLog(AuthAuditLogBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class CustomerBase(SQLModel):
    name: str = Field(index=True)
    company: str
    owner: str = Field(default="李伟超", index=True)
    industry: str
    city: str
    contact_person: str
    phone: str
    email: str
    source: str
    level: str
    annual_revenue: float = 0
    status: str = "active"


class Customer(CustomerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ProductBase(SQLModel):
    name: str = Field(index=True)
    sku: str = Field(index=True)
    category: str
    unit_price: float
    stock: int


class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class InventoryMovementBase(SQLModel):
    product_id: int = Field(foreign_key="product.id", index=True)
    change_quantity: int
    before_stock: int
    after_stock: int
    reason: str
    operator: str
    source: str = Field(default="manual_restock", index=True)


class InventoryMovement(InventoryMovementBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ContactBase(SQLModel):
    name: str = Field(index=True)
    company: str = Field(index=True)
    role: str
    email: str
    phone: str
    owner: str
    status: str = "active"


class Contact(ContactBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SalesLeadBase(SQLModel):
    title: str
    customer_name: str
    owner: str
    region: str
    expected_amount: float
    stage: LeadStage = Field(default=LeadStage.new)
    next_action: str
    due_date: date
    ai_assisted: bool = False


class SalesLead(SalesLeadBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SupportCaseBase(SQLModel):
    title: str
    account: str = Field(index=True)
    owner: str
    priority: str
    status: str
    status_label: str
    due_date: date


class SupportCase(SupportCaseBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class TaskItemBase(SQLModel):
    title: str
    description: str
    owner: str
    due_date: str
    priority: str
    status: str
    status_label: str


class TaskItem(TaskItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SalesGoalBase(SQLModel):
    name: str
    period: str
    current: float
    target: float
    progress: int
    note: str


class SalesGoal(SalesGoalBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class AIInteractionLogBase(SQLModel):
    operation: str = Field(index=True)
    provider: str = "openai-compatible"
    model: str = ""
    status: str = Field(default="fallback", index=True)
    fallback_used: bool = True
    latency_ms: int = 0
    entity_type: str = ""
    entity_id: Optional[int] = None
    request_summary: str = ""
    response_summary: str = ""


class AIInteractionLog(AIInteractionLogBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class CopilotRecommendationBase(SQLModel):
    source: str = Field(index=True)
    lead_id: Optional[int] = Field(default=None, index=True)
    lead_title: str = ""
    customer_name: str = Field(default="", index=True)
    owner: str = ""
    region: str = ""
    stage: str = Field(default="", index=True)
    grade: str = Field(default="", index=True)
    rule_score: int = Field(default=0, index=True)
    win_rate: float = 0
    expected_amount: float = 0
    next_best_action: str = ""
    score_reasons_json: str = "[]"
    llm_summary: str = ""
    message_draft: str = ""
    fallback_used: bool = Field(default=True, index=True)
    model: str = ""


class CopilotRecommendation(CopilotRecommendationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class BusinessAuditLogBase(SQLModel):
    action: str = Field(index=True)
    entity_type: str = Field(index=True)
    entity_id: Optional[int] = Field(default=None, index=True)
    operator: str = ""
    status: str = Field(default="success", index=True)
    summary: str
    detail: str = ""


class BusinessAuditLog(BusinessAuditLogBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SalesOrderBase(SQLModel):
    customer_id: int = Field(foreign_key="customer.id")
    owner: str
    region: str
    currency: str = "CNY"
    status: OrderStatus = Field(default=OrderStatus.draft)
    order_date: date
    due_date: date
    notes: str = ""
    created_by_ai: bool = False
    ai_confidence_score: float = 0


class SalesOrder(SalesOrderBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    total_amount: float = 0
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class OrderApprovalRequestBase(SQLModel):
    order_id: int = Field(foreign_key="salesorder.id", index=True)
    owner: str = Field(index=True)
    requester: str = Field(index=True)
    reviewer: str = ""
    status: OrderApprovalStatus = Field(default=OrderApprovalStatus.pending, index=True)
    reason: str = ""
    risk_summary: str = ""
    requested_total: float = 0
    previous_order_status: OrderStatus = Field(default=OrderStatus.draft)
    target_order_status: OrderStatus = Field(default=OrderStatus.confirmed)
    decision_comment: str = ""


class OrderApprovalRequest(OrderApprovalRequestBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    decided_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class OrderItemBase(SQLModel):
    order_id: int = Field(foreign_key="salesorder.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int
    unit_price: float
    line_total: float


class OrderItem(OrderItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
