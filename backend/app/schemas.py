from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import LeadStage, OrderApprovalStatus, OrderStatus

T = TypeVar("T")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^[0-9+\-\s]{6,24}$")
CUSTOMER_LEVELS = {"S", "A", "B", "C"}
CUSTOMER_STATUSES = {"active", "nurturing", "proposal", "closed"}
PRODUCT_CATEGORIES = {"硬件", "软件", "服务"}
CONTACT_STATUSES = {"active", "nurturing", "closed"}
ACTIVITY_TYPES = {"call", "meeting", "email", "review"}
ACTIVITY_SENTIMENTS = {"positive", "neutral", "risk", "negative"}
PRIORITIES = {"hot", "warm", "cold"}
CASE_STATUSES = {"open", "working", "closed"}
TASK_STATUSES = {"overdue", "today", "week", "completed", "cancelled"}


def clean_text(value: str | None) -> str:
    return str(value or "").strip()


def optional_clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    return clean_text(value)


def validate_email_value(value: str | None, *, allow_empty: bool = False) -> str | None:
    if value is None:
        return None
    text = clean_text(value).lower()
    if allow_empty and not text:
        return ""
    if not EMAIL_PATTERN.match(text):
        raise ValueError("请输入有效邮箱")
    return text


def validate_phone_value(value: str | None, *, allow_empty: bool = True) -> str | None:
    if value is None:
        return None
    text = clean_text(value)
    if allow_empty and not text:
        return ""
    if not PHONE_PATTERN.match(text):
        raise ValueError("请输入有效手机号")
    return text


def validate_choice(value: str | None, allowed: set[str], label: str) -> str | None:
    if value is None:
        return None
    text = clean_text(value)
    if text not in allowed:
        raise ValueError(f"{label}无效")
    return text


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

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return validate_email_value(value) or ""

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_phone_value(value) or ""

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> "AuthRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


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


class AuthProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2)
    email: str | None = Field(default=None, min_length=5)
    phone: str | None = None
    position: str | None = None
    department: str | None = None
    location: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return validate_email_value(value)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return validate_phone_value(value)

    @field_validator("full_name", "position", "department", "location")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return optional_clean_text(value)


class AuthPasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> "AuthPasswordChangeRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("两次输入的新密码不一致")
        return self


class AuthPasswordChangeResponse(BaseModel):
    changed: bool
    revoked_sessions: int


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


class TeamMemberCreate(BaseModel):
    full_name: str = Field(min_length=2)
    email: str = Field(min_length=5)
    phone: str = ""
    role: str = "销售"
    position: str = "销售顾问"
    department: str = "客户增长中心"
    location: str = "深圳 · 南山"
    status: str = "active"
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return validate_email_value(value) or ""

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_phone_value(value) or ""

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> "TeamMemberCreate":
        if self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


class TeamMemberUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    position: str | None = None
    department: str | None = None
    location: str | None = None
    status: str | None = None
    password: str | None = Field(default=None, min_length=6)
    confirm_password: str | None = Field(default=None, min_length=6)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return validate_email_value(value)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return validate_phone_value(value)

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> "TeamMemberUpdate":
        if (self.password is None) != (self.confirm_password is None):
            raise ValueError("请输入并确认新密码")
        if self.password is not None and self.password != self.confirm_password:
            raise ValueError("两次输入的密码不一致")
        return self


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


class UserPreferenceRead(BaseModel):
    id: int | None = None
    namespace: str
    value: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime | None = None


class UserPreferenceUpdate(BaseModel):
    value: dict[str, Any] = Field(default_factory=dict)


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str
    owner: str
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
    owner: str = ""
    industry: str = "待补充"
    city: str = "深圳"
    contact_person: str = ""
    phone: str = "13800000000"
    email: str = "customer@example.com"
    source: str = "课程演示"
    level: str = "B"
    annual_revenue: float = Field(default=0, ge=0)
    status: str = "active"

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return validate_email_value(value) or ""

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_phone_value(value) or ""

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        return validate_choice(value, CUSTOMER_LEVELS, "客户等级") or ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        return validate_choice(value, CUSTOMER_STATUSES, "客户状态") or ""


class CustomerUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    owner: str | None = None
    industry: str | None = None
    city: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    source: str | None = None
    level: str | None = None
    annual_revenue: float | None = Field(default=None, ge=0)
    status: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return validate_email_value(value)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return validate_phone_value(value)

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str | None) -> str | None:
        return validate_choice(value, CUSTOMER_LEVELS, "客户等级")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        return validate_choice(value, CUSTOMER_STATUSES, "客户状态")


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    category: str
    unit_price: float
    stock: int


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    category: str = "软件"
    unit_price: float = Field(gt=0)
    stock: int = Field(default=0, ge=0)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        return validate_choice(value, PRODUCT_CATEGORIES, "商品分类") or ""


class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    category: str | None = None
    unit_price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)

    @field_validator("name", "sku")
    @classmethod
    def validate_required_text(cls, value: str | None) -> str | None:
        text = optional_clean_text(value)
        if text == "":
            raise ValueError("字段不能为空")
        return text

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str | None) -> str | None:
        return validate_choice(value, PRODUCT_CATEGORIES, "商品分类")


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
    is_read: bool = False
    dismissed: bool = False
    state_updated_at: datetime | None = None
    created_at: datetime


class NotificationStateUpdate(BaseModel):
    action: Literal["read", "unread", "dismiss"]


class NotificationStateResponse(BaseModel):
    notification_id: str
    status: str
    is_read: bool
    dismissed: bool
    read_at: datetime | None = None
    dismissed_at: datetime | None = None
    updated_at: datetime


class NotificationBulkUpdateResponse(BaseModel):
    updated_count: int


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
    name: str = Field(min_length=1)
    company: str = Field(min_length=1)
    role: str = "待确认"
    email: str = "contact@example.com"
    phone: str = "13800000000"
    owner: str = "未分配"
    status: str = "active"

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return validate_email_value(value) or ""

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_phone_value(value) or ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        return validate_choice(value, CONTACT_STATUSES, "联系人状态") or ""


class ContactUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    owner: str | None = None
    status: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return validate_email_value(value)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return validate_phone_value(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        return validate_choice(value, CONTACT_STATUSES, "联系人状态")


class CustomerActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    customer_name: str
    owner: str
    activity_type: str
    subject: str
    summary: str
    outcome: str
    next_action: str
    sentiment: str
    occurred_at: datetime
    created_at: datetime


class CustomerActivityCreate(BaseModel):
    owner: str = ""
    activity_type: str = "call"
    subject: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    outcome: str = ""
    next_action: str = ""
    sentiment: str = "neutral"
    occurred_at: datetime | None = None

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, value: str) -> str:
        return validate_choice(value, ACTIVITY_TYPES, "互动类型") or ""

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, value: str) -> str:
        return validate_choice(value, ACTIVITY_SENTIMENTS, "互动信号") or ""


class CustomerActivityUpdate(BaseModel):
    owner: str | None = None
    activity_type: str | None = None
    subject: str | None = None
    summary: str | None = None
    outcome: str | None = None
    next_action: str | None = None
    sentiment: str | None = None
    occurred_at: datetime | None = None

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, value: str | None) -> str | None:
        return validate_choice(value, ACTIVITY_TYPES, "互动类型")

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, value: str | None) -> str | None:
        return validate_choice(value, ACTIVITY_SENTIMENTS, "互动信号")


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
    title: str = Field(min_length=1)
    customer_name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    region: str = "华南"
    expected_amount: float = Field(default=0, ge=0)
    stage: LeadStage = LeadStage.new
    next_action: str = "安排下一步跟进"
    due_date: date = Field(default_factory=date.today)
    ai_assisted: bool = False

    @field_validator("title", "customer_name", "owner", "region")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        text = clean_text(value)
        if not text:
            raise ValueError("字段不能为空")
        return text

    @field_validator("next_action")
    @classmethod
    def validate_next_action(cls, value: str) -> str:
        return clean_text(value)


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

    @field_validator("title", "customer_name", "owner", "region", "next_action")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        text = optional_clean_text(value)
        if text == "" and value is not None:
            raise ValueError("字段不能为空")
        return text


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
    title: str = Field(min_length=1)
    account: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    priority: str = "warm"
    status: str = "open"
    status_label: str = "Open"
    due_date: date = Field(default_factory=date.today)

    @field_validator("title", "account", "owner", "status_label")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        text = clean_text(value)
        if not text:
            raise ValueError("字段不能为空")
        return text

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        return validate_choice(value, PRIORITIES, "优先级") or ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        return validate_choice(value, CASE_STATUSES, "工单状态") or ""


class SupportCaseUpdate(BaseModel):
    title: str | None = None
    account: str | None = None
    owner: str | None = None
    priority: str | None = None
    status: str | None = None
    status_label: str | None = None
    due_date: date | None = None

    @field_validator("title", "account", "owner", "status_label")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        text = optional_clean_text(value)
        if text == "" and value is not None:
            raise ValueError("字段不能为空")
        return text

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        return validate_choice(value, PRIORITIES, "优先级")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        return validate_choice(value, CASE_STATUSES, "工单状态")


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
    title: str = Field(min_length=1)
    description: str = ""
    owner: str = Field(min_length=1)
    due_date: str = "今天 18:00"
    priority: str = "warm"
    status: str = "week"
    status_label: str = "本周"

    @field_validator("title", "owner", "due_date", "status_label")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        text = clean_text(value)
        if not text:
            raise ValueError("字段不能为空")
        return text

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return clean_text(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        return validate_choice(value, PRIORITIES, "优先级") or ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        return validate_choice(value, TASK_STATUSES, "任务状态") or ""


class TaskItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    owner: str | None = None
    due_date: str | None = None
    priority: str | None = None
    status: str | None = None
    status_label: str | None = None

    @field_validator("title", "owner", "due_date", "status_label")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        text = optional_clean_text(value)
        if text == "" and value is not None:
            raise ValueError("字段不能为空")
        return text

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        return optional_clean_text(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        return validate_choice(value, PRIORITIES, "优先级")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        return validate_choice(value, TASK_STATUSES, "任务状态")


class SalesGoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    period: str
    owner: str
    current: float
    target: float
    progress: int
    note: str
    created_at: datetime


class SalesGoalCreate(BaseModel):
    name: str = Field(min_length=1)
    period: str = "2026 Q2"
    owner: str = "未分配"
    current: float = Field(default=0, ge=0)
    target: float = Field(default=1, gt=0)
    progress: int | None = Field(default=None, ge=0, le=100)
    note: str = ""

    @field_validator("name", "period", "owner")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        text = clean_text(value)
        if not text:
            raise ValueError("字段不能为空")
        return text

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str) -> str:
        return clean_text(value)


class SalesGoalUpdate(BaseModel):
    name: str | None = None
    period: str | None = None
    owner: str | None = None
    current: float | None = Field(default=None, ge=0)
    target: float | None = Field(default=None, gt=0)
    progress: int | None = Field(default=None, ge=0, le=100)
    note: str | None = None

    @field_validator("name", "period", "owner")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        text = optional_clean_text(value)
        if text == "" and value is not None:
            raise ValueError("字段不能为空")
        return text

    @field_validator("note")
    @classmethod
    def validate_note(cls, value: str | None) -> str | None:
        return optional_clean_text(value)


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


class ConsistencyCheckRead(BaseModel):
    id: str
    category: str
    severity: str
    status: str
    title: str
    detail: str
    entity_type: str
    entity_id: int | None = None
    suggestion: str


class ConsistencyReportResponse(BaseModel):
    overall_status: str
    total_checks: int
    issue_count: int
    critical_count: int
    warning_count: int
    ok_count: int
    generated_at: datetime
    checks: list[ConsistencyCheckRead]


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
    items: list[OrderItemPayload] = Field(min_length=1)

    @field_validator("owner", "region")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        text = clean_text(value)
        if not text:
            raise ValueError("字段不能为空")
        return text

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str) -> str:
        return clean_text(value)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        text = clean_text(value).upper()
        if not re.fullmatch(r"[A-Z]{3}", text):
            raise ValueError("币种必须是 3 位大写字母代码")
        return text

    @model_validator(mode="after")
    def validate_order_dates(self) -> "SalesOrderCreate":
        if self.due_date < self.order_date:
            raise ValueError("交付日期不能早于下单日期")
        return self


class SalesOrderUpdate(BaseModel):
    owner: str | None = None
    region: str | None = None
    status: OrderStatus | None = None
    due_date: date | None = None
    notes: str | None = None
    items: list[OrderItemPayload] | None = Field(default=None, min_length=1)

    @field_validator("owner", "region")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        text = optional_clean_text(value)
        if text == "" and value is not None:
            raise ValueError("字段不能为空")
        return text

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        return optional_clean_text(value)


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


class OrderApprovalCreate(BaseModel):
    reason: str = ""
    reviewer: str = "销售经理"
    target_order_status: OrderStatus = OrderStatus.confirmed


class OrderApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: str = ""
    reviewer: str = ""


class OrderApprovalReminderCreate(BaseModel):
    message: str = Field(default="", max_length=360)


class OrderApprovalAssignmentCreate(BaseModel):
    reviewer: str = Field(min_length=1, max_length=64)
    comment: str = Field(default="", max_length=360)


class OrderApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    customer_name: str
    owner: str
    requester: str
    reviewer: str
    status: OrderApprovalStatus
    reason: str
    risk_summary: str
    risk_level: str
    requested_total: float
    previous_order_status: OrderStatus
    target_order_status: OrderStatus
    decision_comment: str
    sla_due_at: datetime | None
    sla_status: str
    sla_hours_remaining: int | None
    decided_at: datetime | None
    created_at: datetime


class DashboardMetric(BaseModel):
    label: str
    value: str
    hint: str


class AIQualityOperationBreakdown(BaseModel):
    operation: str
    label: str
    total_count: int
    llm_count: int
    fallback_count: int
    fallback_rate: float
    average_latency_ms: int


class AIQualityModelBreakdown(BaseModel):
    model: str
    total_count: int
    llm_count: int
    fallback_count: int
    fallback_rate: float
    average_latency_ms: int


class AIQualityRecommendationSignal(BaseModel):
    total_recommendations: int
    average_rule_score: float
    average_win_rate: float
    fallback_count: int
    fallback_rate: float
    converted_task_count: int
    conversion_rate: float
    feedback_count: int
    positive_feedback_count: int
    negative_feedback_count: int
    positive_feedback_rate: float
    average_feedback_rating: float


class AIQualityReportResponse(BaseModel):
    generated_at: datetime
    metrics: list[DashboardMetric]
    operation_breakdown: list[AIQualityOperationBreakdown]
    model_breakdown: list[AIQualityModelBreakdown]
    recommendation_signal: AIQualityRecommendationSignal
    recent_fallbacks: list[AIInteractionLogRead]
    applied_filters: dict[str, str]


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


class ApprovalReportDistributionItem(BaseModel):
    key: str
    label: str
    count: int
    share: float


class ApprovalReviewerWorkload(BaseModel):
    name: str
    pending_count: int
    approved_count: int
    rejected_count: int
    overdue_count: int
    average_resolution_hours: float


class ApprovalPerformanceReportResponse(BaseModel):
    generated_at: datetime
    metrics: list[DashboardMetric]
    risk_distribution: list[ApprovalReportDistributionItem]
    sla_distribution: list[ApprovalReportDistributionItem]
    status_distribution: list[ApprovalReportDistributionItem]
    reviewer_workload: list[ApprovalReviewerWorkload]
    recent_approvals: list[OrderApprovalRead]
    applied_filters: dict[str, str]


class ReportSnapshotCreate(BaseModel):
    report_type: Literal["sales_performance", "approval_performance"]
    title: str = Field(default="", max_length=120)
    filters: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    summary: str = Field(default="", max_length=500)

    @field_validator("title", "summary")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return clean_text(value)


class ReportSnapshotRead(BaseModel):
    id: int
    report_type: str
    report_type_label: str
    title: str
    filters: dict[str, Any]
    payload: dict[str, Any]
    summary: str
    metric_count: int
    created_by: str
    created_at: datetime


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


class CopilotAskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    customer_id: int | None = None


class CopilotAskResponse(BaseModel):
    question: str
    answer: str
    next_actions: list[str]
    evidence: list[str]
    fallback_used: bool
    model: str


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
    feedback_status: str = ""
    feedback_rating: int = 0
    feedback_note: str = ""
    feedback_by: str = ""
    feedback_at: datetime | None = None
    created_at: datetime


class CopilotRecommendationFeedbackRequest(BaseModel):
    feedback_status: Literal["accepted", "helpful", "not_helpful", "dismissed"]
    feedback_rating: int | None = Field(default=None, ge=1, le=5)
    feedback_note: str = Field(default="", max_length=360)


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


class CustomerTimelineItem(BaseModel):
    id: str
    category: str
    title: str
    description: str
    timestamp: datetime
    href: str
    severity: str = "info"


class CustomerAccountPlanResponse(BaseModel):
    summary: str
    expansion_paths: list[str]
    risks: list[str]
    next_actions: list[str]
    fallback_used: bool
    model: str


class CustomerHealthFactor(BaseModel):
    key: str
    label: str
    score: int = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    level: Literal["strong", "stable", "watch", "risk"]
    detail: str


class CustomerHealthAction(BaseModel):
    title: str
    detail: str
    priority: Literal["hot", "warm", "cold"]
    source: str


class CustomerHealthProfile(BaseModel):
    score: int = Field(ge=0, le=100)
    grade: Literal["excellent", "healthy", "watch", "risk"]
    grade_label: str
    trend: Literal["up", "stable", "down"]
    churn_probability: float = Field(ge=0, le=1)
    evidence_summary: str
    factors: list[CustomerHealthFactor]
    risk_flags: list[str]
    strengths: list[str]
    recommended_actions: list[CustomerHealthAction]


class CustomerWorkspaceResponse(BaseModel):
    customer: CustomerRead
    metrics: list[DashboardMetric]
    contacts: list[ContactRead]
    activities: list[CustomerActivityRead]
    leads: list[LeadRead]
    orders: list[SalesOrderRead]
    cases: list[SupportCaseRead]
    recommendations: list[CopilotRecommendationRead]
    timeline: list[CustomerTimelineItem]
    account_plan: CustomerAccountPlanResponse
    health_profile: CustomerHealthProfile
