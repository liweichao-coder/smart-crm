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
