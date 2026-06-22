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


class CustomerBase(SQLModel):
    name: str = Field(index=True)
    company: str
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


class OrderItemBase(SQLModel):
    order_id: int = Field(foreign_key="salesorder.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int
    unit_price: float
    line_total: float


class OrderItem(OrderItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
