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
    created_at: datetime


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    category: str
    unit_price: float
    stock: int


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
