from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from math import ceil
from time import perf_counter
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from .auth import generate_session_token, hash_password, hash_session_token, verify_password
from .config import settings
from .database import create_db_and_tables, engine, get_session
from .models import AIInteractionLog, AuthAuditLog, AuthSession, AuthUser, BusinessAuditLog, Contact, Customer, InventoryMovement, OrderItem, Organization, Product, SalesGoal, SalesLead, SalesOrder, SupportCase, TaskItem
from .schemas import (
    AIInteractionLogRead,
    AuthAuditLogRead,
    AuthLoginRequest,
    AuthLogoutResponse,
    AuthMeResponse,
    AuthOrganizationRead,
    AuthRegisterRequest,
    AuthSessionResponse,
    AuthUserRead,
    BusinessAuditLogRead,
    ContactCreate,
    ContactRead,
    ContactUpdate,
    CopilotFollowUpRequest,
    CopilotFollowUpResponse,
    CopilotOrderDraftRequest,
    CopilotOrderDraftResponse,
    CopilotSummaryResponse,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    DashboardMetric,
    DashboardResponse,
    InventoryMovementRead,
    InventoryRestockAlertRead,
    LeadRead,
    OrderItemRead,
    PaginatedResponse,
    ProductCreate,
    ProductRestockRequest,
    ProductRestockResponse,
    ProductRead,
    ProductUpdate,
    RevenuePoint,
    SalesGoalCreate,
    SalesGoalRead,
    SalesGoalUpdate,
    SalesLeadCreate,
    SalesLeadUpdate,
    SalesOrderCreate,
    SalesOrderRead,
    SalesOrderUpdate,
    SupportCaseCreate,
    SupportCaseRead,
    SupportCaseUpdate,
    TaskItemCreate,
    TaskItemRead,
    TaskItemUpdate,
    VisionExtractResponse,
)
from .seed import seed_data
from .services import CopilotService, VisionExtractionService


vision_service = VisionExtractionService()
copilot_service = CopilotService()
SessionDep = Annotated[Session, Depends(get_session)]
auth_scheme = HTTPBearer(auto_error=False)
RESTOCK_DANGER_THRESHOLD = 80
RESTOCK_WARNING_THRESHOLD = 300
AUTH_SESSION_DAYS = 7
ALL_PERMISSIONS = "*"
KNOWN_PERMISSIONS = {
    "ai:use",
    "audit:read",
    "catalog:manage",
    "crm:read",
    "crm:write",
    "dashboard:read",
    "inventory:manage",
    "order:manage",
}
ROLE_PERMISSIONS = {
    "管理员": {ALL_PERMISSIONS},
    "销售": {"crm:read", "crm:write", "order:manage", "ai:use", "dashboard:read"},
    "销售经理": {"crm:read", "crm:write", "order:manage", "ai:use", "dashboard:read", "audit:read"},
    "支持": {"crm:read", "case:write", "task:write", "dashboard:read"},
    "审计员": {"crm:read", "audit:read", "dashboard:read"},
}
CATEGORY_TARGET_STOCK = {
    "硬件": 600,
    "软件": 1200,
    "服务": 420,
}


def summarize_text(value: str, limit: int = 220) -> str:
    normalized = " ".join(str(value or "").split())
    return normalized[:limit]


def apply_updates(instance, updates: dict) -> None:
    for key, value in updates.items():
        setattr(instance, key, value)


def patch_values(payload) -> dict:
    return payload.model_dump(exclude_unset=True, exclude_none=True)


def delete_response(entity: str, item_id: int) -> dict[str, bool | int | str]:
    return {"deleted": True, "entity": entity, "id": item_id}


def normalized_query_value(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        value = value.value
    return str(value).strip().lower()


def filter_records(records: list, *, q: str = "", fields: tuple[str, ...] = (), **filters) -> list:
    result = records
    term = normalized_query_value(q)
    if term and fields:
        result = [
            record
            for record in result
            if any(term in normalized_query_value(getattr(record, field, "")) for field in fields)
        ]

    for field, expected in filters.items():
        if expected is None:
            continue
        expected_value = normalized_query_value(expected)
        if not expected_value:
            continue
        result = [record for record in result if normalized_query_value(getattr(record, field, "")) == expected_value]
    return result


def filter_bool(records: list, field: str, expected: bool | None) -> list:
    if expected is None:
        return records
    return [record for record in records if bool(getattr(record, field, False)) is expected]


def paginate_or_list(records: list, *, page: int | None = None, per_page: int | None = None) -> list | dict:
    if page is None and per_page is None:
        return records

    safe_page = page or 1
    safe_per_page = min(per_page or 20, 100)
    total = len(records)
    start = (safe_page - 1) * safe_per_page
    end = start + safe_per_page
    pages = ceil(total / safe_per_page) if total else 0
    return {
        "items": records[start:end],
        "total": total,
        "page": safe_page,
        "per_page": safe_per_page,
        "pages": pages,
        "has_next": safe_page < pages,
        "has_previous": safe_page > 1 and total > 0,
    }


def normalize_account(account: str) -> str:
    return " ".join(str(account or "").split()).lower()


def build_organization_slug(name: str) -> str:
    base = "".join(ch.lower() for ch in name if ch.isalnum())
    return base[:40] or f"org-{round(datetime.utcnow().timestamp())}"


def build_unique_organization_slug(session: Session, name: str) -> str:
    base = build_organization_slug(name)
    slug = base
    suffix = 2
    while session.exec(select(Organization).where(Organization.slug == slug)).first():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def find_user_by_account(session: Session, account: str) -> AuthUser | None:
    normalized = normalize_account(account)
    user = session.exec(select(AuthUser).where(AuthUser.email == normalized)).first()
    if user:
        return user
    return session.exec(select(AuthUser).where(AuthUser.phone == normalized)).first()


def user_permissions(user: AuthUser) -> list[str]:
    permissions = ROLE_PERMISSIONS.get(user.role, {"crm:read"})
    if ALL_PERMISSIONS in permissions:
        return [ALL_PERMISSIONS, *sorted(KNOWN_PERMISSIONS)]
    return sorted(permissions)


def has_permission(user: AuthUser, permission: str) -> bool:
    permissions = set(ROLE_PERMISSIONS.get(user.role, {"crm:read"}))
    return ALL_PERMISSIONS in permissions or permission in permissions


def serialize_auth_organization(user: AuthUser, organization: Organization) -> AuthOrganizationRead:
    return AuthOrganizationRead(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        role=user.role,
        plan=organization.plan,
        status=organization.status,
    )


def serialize_auth_user(user: AuthUser, organization: Organization) -> AuthUserRead:
    return AuthUserRead(
        id=user.id,
        organization_id=user.organization_id,
        organization_name=organization.name,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        position=user.position,
        department=user.department,
        location=user.location,
        status=user.status,
        permissions=user_permissions(user),
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def build_auth_payload(token: str, auth_session: AuthSession, user: AuthUser, organization: Organization) -> AuthSessionResponse:
    return AuthSessionResponse(
        token=token,
        expires_at=auth_session.expires_at,
        user=serialize_auth_user(user, organization),
        organizations=[serialize_auth_organization(user, organization)],
    )


def record_auth_audit(
    session: Session,
    *,
    event: str,
    account: str,
    status: str,
    detail: str = "",
    user: AuthUser | None = None,
) -> None:
    session.add(
        AuthAuditLog(
            event=event,
            account=summarize_text(account, limit=120),
            user_id=user.id if user else None,
            organization_id=user.organization_id if user else None,
            status=status,
            detail=summarize_text(detail, limit=240),
        )
    )


def create_auth_session(session: Session, user: AuthUser) -> tuple[str, AuthSession]:
    token = generate_session_token()
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=datetime.utcnow() + timedelta(days=AUTH_SESSION_DAYS),
    )
    session.add(auth_session)
    return token, auth_session


def require_current_auth(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(auth_scheme)] = None,
) -> tuple[AuthUser, AuthSession]:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="请先登录")
    token_hash = hash_session_token(credentials.credentials)
    auth_session = session.exec(select(AuthSession).where(AuthSession.token_hash == token_hash)).first()
    if not auth_session or auth_session.revoked_at is not None or auth_session.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")
    user = session.get(AuthUser, auth_session.user_id)
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="账号不可用")
    return user, auth_session


def require_permission(permission: str):
    def dependency(current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)]) -> AuthUser:
        user, _ = current
        if not has_permission(user, permission):
            raise HTTPException(status_code=403, detail="当前账号没有访问权限")
        return user

    return dependency


def product_recent_order_quantity(product_id: int, session: Session) -> int:
    order_items = session.exec(select(OrderItem).where(OrderItem.product_id == product_id)).all()
    return sum(item.quantity for item in order_items)


def build_restock_alert(product: Product, session: Session) -> InventoryRestockAlertRead | None:
    recent_quantity = product_recent_order_quantity(product.id, session)
    if product.stock > RESTOCK_WARNING_THRESHOLD:
        return None

    priority = "critical" if product.stock <= RESTOCK_DANGER_THRESHOLD else "warning"
    target_stock = max(CATEGORY_TARGET_STOCK.get(product.category, 600), recent_quantity * 12, RESTOCK_WARNING_THRESHOLD + 200)
    recommended_restock = max(target_stock - product.stock, 0)
    threshold = RESTOCK_DANGER_THRESHOLD if priority == "critical" else RESTOCK_WARNING_THRESHOLD
    reason = f"当前库存 {product.stock} 件，低于{'危险' if priority == 'critical' else '预警'}线 {threshold} 件；历史订单累计消耗 {recent_quantity} 件。"
    return InventoryRestockAlertRead(
        product_id=product.id,
        name=product.name,
        sku=product.sku,
        category=product.category,
        unit_price=product.unit_price,
        current_stock=product.stock,
        priority=priority,
        danger_threshold=RESTOCK_DANGER_THRESHOLD,
        warning_threshold=RESTOCK_WARNING_THRESHOLD,
        recent_order_quantity=recent_quantity,
        recommended_restock=recommended_restock,
        reason=reason,
    )


def list_restock_alerts(session: Session) -> list[InventoryRestockAlertRead]:
    products = session.exec(select(Product)).all()
    alerts = [alert for product in products if (alert := build_restock_alert(product, session))]
    priority_rank = {"critical": 0, "warning": 1}
    return sorted(alerts, key=lambda alert: (priority_rank.get(alert.priority, 9), alert.current_stock, -alert.recent_order_quantity))


def serialize_inventory_movement(movement: InventoryMovement, session: Session) -> InventoryMovementRead:
    product = session.get(Product, movement.product_id)
    return InventoryMovementRead(
        id=movement.id,
        product_id=movement.product_id,
        product_name=product.name if product else "未知商品",
        sku=product.sku if product else "-",
        change_quantity=movement.change_quantity,
        before_stock=movement.before_stock,
        after_stock=movement.after_stock,
        reason=movement.reason,
        operator=movement.operator,
        source=movement.source,
        created_at=movement.created_at,
    )


def save_ai_interaction(
    session: Session,
    *,
    operation: str,
    model: str,
    fallback_used: bool,
    start_time: float,
    request_summary: str,
    response_summary: str,
    entity_type: str = "",
    entity_id: int | None = None,
) -> None:
    latency_ms = max(0, round((perf_counter() - start_time) * 1000))
    log = AIInteractionLog(
        operation=operation,
        provider="openai-compatible",
        model=model,
        status="fallback" if fallback_used else "llm",
        fallback_used=fallback_used,
        latency_ms=latency_ms,
        entity_type=entity_type,
        entity_id=entity_id,
        request_summary=summarize_text(request_summary),
        response_summary=summarize_text(response_summary),
    )
    session.add(log)
    session.commit()


def add_business_audit(
    session: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: int | None,
    operator: str,
    summary: str,
    detail: str = "",
    status: str = "success",
) -> None:
    session.add(
        BusinessAuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            operator=operator,
            status=status,
            summary=summarize_text(summary),
            detail=summarize_text(detail, limit=360),
        )
    )


def serialize_order(order: SalesOrder, session: Session) -> SalesOrderRead:
    customer = session.get(Customer, order.customer_id)
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    serialized_items = []
    for item in items:
        product = session.get(Product, item.product_id)
        serialized_items.append(
            OrderItemRead(
                id=item.id,
                product_id=item.product_id,
                product_name=product.name if product else "未知商品",
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total,
            )
        )

    return SalesOrderRead(
        id=order.id,
        customer_id=order.customer_id,
        customer_name=customer.company if customer else "未知客户",
        owner=order.owner,
        region=order.region,
        currency=order.currency,
        status=order.status,
        order_date=order.order_date,
        due_date=order.due_date,
        notes=order.notes,
        created_by_ai=order.created_by_ai,
        ai_confidence_score=order.ai_confidence_score,
        total_amount=order.total_amount,
        created_at=order.created_at,
        items=serialized_items,
    )


def replace_order_items(order: SalesOrder, payload_items, session: Session) -> None:
    if not payload_items:
        raise HTTPException(status_code=400, detail="订单明细不能为空")

    existing_items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    old_quantities = Counter()
    new_quantities = Counter()
    for item in existing_items:
        old_quantities[item.product_id] += item.quantity
    for item in payload_items:
        new_quantities[item.product_id] += item.quantity

    new_product_ids = set(new_quantities)
    all_product_ids = sorted(set(old_quantities) | new_product_ids)
    products = session.exec(select(Product).where(Product.id.in_(all_product_ids))).all() if all_product_ids else []
    product_map = {product.id: product for product in products}
    if not new_product_ids <= set(product_map):
        raise HTTPException(status_code=400, detail="存在无效商品")
    if not set(old_quantities) <= set(product_map):
        raise HTTPException(status_code=400, detail="订单包含无效历史商品")

    for product_id in all_product_ids:
        delta = new_quantities[product_id] - old_quantities[product_id]
        if delta <= 0:
            continue
        product = product_map[product_id]
        if delta > product.stock:
            raise HTTPException(status_code=400, detail=f"{product.name} 库存不足，当前仅剩 {product.stock} 件，无法增加 {delta} 件")

    for product_id in all_product_ids:
        delta = new_quantities[product_id] - old_quantities[product_id]
        if delta == 0:
            continue
        product = product_map[product_id]
        before_stock = product.stock
        product.stock = product.stock - delta
        session.add(product)
        session.add(
            InventoryMovement(
                product_id=product.id,
                change_quantity=-delta,
                before_stock=before_stock,
                after_stock=product.stock,
                reason=f"订单 #{order.id} 明细调整：{product.name} 净变化 {delta:+d} 件",
                operator=order.owner,
                source="order_adjustment",
            )
        )

    for item in existing_items:
        session.delete(item)
    session.flush()

    total_amount = 0.0
    for item in payload_items:
        line_total = item.quantity * item.unit_price
        total_amount += line_total
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=line_total,
            )
        )

    order.total_amount = total_amount
    session.add(order)


def build_orders_csv(orders: list[SalesOrderRead]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "订单ID",
            "客户",
            "负责人",
            "区域",
            "状态",
            "下单日期",
            "交付日期",
            "来源",
            "AI置信度",
            "订单总额",
            "商品",
            "数量",
            "单价",
            "明细金额",
            "备注",
        ]
    )
    for order in orders:
        source = "AI" if order.created_by_ai else "人工"
        status = order.status.value if hasattr(order.status, "value") else str(order.status)
        if not order.items:
            writer.writerow(
                [
                    order.id,
                    order.customer_name,
                    order.owner,
                    order.region,
                    status,
                    order.order_date.isoformat(),
                    order.due_date.isoformat(),
                    source,
                    order.ai_confidence_score,
                    order.total_amount,
                    "",
                    0,
                    0,
                    0,
                    order.notes,
                ]
            )
            continue
        for item in order.items:
            writer.writerow(
                [
                    order.id,
                    order.customer_name,
                    order.owner,
                    order.region,
                    status,
                    order.order_date.isoformat(),
                    order.due_date.isoformat(),
                    source,
                    order.ai_confidence_score,
                    order.total_amount,
                    item.product_name,
                    item.quantity,
                    item.unit_price,
                    item.line_total,
                    order.notes,
                ]
            )
    return "\ufeff" + output.getvalue()


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_data(session)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=AuthSessionResponse)
def login(payload: AuthLoginRequest, session: SessionDep) -> AuthSessionResponse:
    account = normalize_account(payload.account)
    user = find_user_by_account(session, account)
    if not user or not verify_password(payload.password, user.password_hash):
        record_auth_audit(session, event="login", account=account, status="failed", detail="账号或密码错误", user=user)
        session.commit()
        raise HTTPException(status_code=401, detail="账号或密码错误")
    if user.status != "active":
        record_auth_audit(session, event="login", account=account, status="failed", detail="账号已停用", user=user)
        session.commit()
        raise HTTPException(status_code=403, detail="账号已停用")

    organization = session.get(Organization, user.organization_id)
    if not organization or organization.status != "active":
        record_auth_audit(session, event="login", account=account, status="failed", detail="组织不可用", user=user)
        session.commit()
        raise HTTPException(status_code=403, detail="组织不可用")

    user.last_login_at = datetime.utcnow()
    session.add(user)
    token, auth_session = create_auth_session(session, user)
    record_auth_audit(session, event="login", account=account, status="success", detail="登录成功", user=user)
    session.commit()
    session.refresh(user)
    session.refresh(auth_session)
    return build_auth_payload(token, auth_session, user, organization)


@app.post("/api/auth/register", response_model=AuthSessionResponse, status_code=201)
def register(payload: AuthRegisterRequest, session: SessionDep) -> AuthSessionResponse:
    email = normalize_account(payload.email)
    if "@" not in email:
        raise HTTPException(status_code=400, detail="请输入有效邮箱")
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    if session.exec(select(AuthUser).where(AuthUser.email == email)).first():
        record_auth_audit(session, event="register", account=email, status="failed", detail="邮箱已注册")
        session.commit()
        raise HTTPException(status_code=400, detail="邮箱已注册")

    organization = Organization(
        name=payload.organization_name.strip(),
        slug=build_unique_organization_slug(session, payload.organization_name),
        plan="course",
        status="active",
    )
    session.add(organization)
    session.flush()
    user = AuthUser(
        organization_id=organization.id,
        full_name=payload.full_name.strip(),
        email=email,
        phone=normalize_account(payload.phone),
        role="管理员",
        position="CRM 运营管理员",
        department="客户增长中心",
        location="深圳 · 南山",
        status="active",
        password_hash=hash_password(payload.password),
        last_login_at=datetime.utcnow(),
    )
    session.add(user)
    session.flush()
    token, auth_session = create_auth_session(session, user)
    record_auth_audit(session, event="register", account=email, status="success", detail=f"创建组织 {organization.name}", user=user)
    session.commit()
    session.refresh(user)
    session.refresh(auth_session)
    session.refresh(organization)
    return build_auth_payload(token, auth_session, user, organization)


@app.get("/api/auth/me", response_model=AuthMeResponse)
def get_current_user(
    current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)],
    session: SessionDep,
) -> AuthMeResponse:
    user, auth_session = current
    organization = session.get(Organization, user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="组织不存在")
    return AuthMeResponse(
        expires_at=auth_session.expires_at,
        user=serialize_auth_user(user, organization),
        organizations=[serialize_auth_organization(user, organization)],
    )


@app.post("/api/auth/logout", response_model=AuthLogoutResponse)
def logout(
    current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)],
    session: SessionDep,
) -> AuthLogoutResponse:
    user, auth_session = current
    auth_session.revoked_at = datetime.utcnow()
    session.add(auth_session)
    record_auth_audit(session, event="logout", account=user.email, status="success", detail="退出登录", user=user)
    session.commit()
    return AuthLogoutResponse(revoked=True)


@app.get(
    "/api/auth/audit-logs",
    response_model=list[AuthAuditLogRead] | PaginatedResponse[AuthAuditLogRead],
    dependencies=[Depends(require_permission("audit:read"))],
)
def list_auth_audit_logs(
    session: SessionDep,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    event: str = "",
    status: str = "",
) -> list[AuthAuditLog] | dict:
    logs = session.exec(select(AuthAuditLog).order_by(AuthAuditLog.created_at.desc())).all()
    logs = filter_records(logs, q=q, fields=("event", "account", "status", "detail"), event=event, status=status)
    return paginate_or_list(logs, page=page, per_page=per_page)


@app.get("/api/customers", response_model=list[CustomerRead] | PaginatedResponse[CustomerRead], dependencies=[Depends(require_permission("crm:read"))])
def list_customers(
    session: SessionDep,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    status: str = "",
    level: str = "",
    city: str = "",
    industry: str = "",
) -> list[Customer] | dict:
    customers = session.exec(select(Customer).order_by(Customer.created_at.desc())).all()
    customers = filter_records(
        customers,
        q=q,
        fields=("name", "company", "industry", "city", "contact_person", "phone", "email", "source"),
        status=status,
        level=level,
        city=city,
        industry=industry,
    )
    return paginate_or_list(customers, page=page, per_page=per_page)


@app.post("/api/customers", response_model=CustomerRead, status_code=201, dependencies=[Depends(require_permission("crm:write"))])
def create_customer(payload: CustomerCreate, session: SessionDep) -> Customer:
    contact_person = payload.contact_person or payload.name or payload.company
    customer = Customer(
        name=payload.name or contact_person,
        company=payload.company,
        industry=payload.industry,
        city=payload.city,
        contact_person=contact_person,
        phone=payload.phone,
        email=payload.email,
        source=payload.source,
        level=payload.level,
        annual_revenue=payload.annual_revenue,
        status=payload.status,
    )
    session.add(customer)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="customer",
        entity_id=customer.id,
        operator=customer.contact_person,
        summary=f"新建客户 {customer.company}",
        detail=f"行业 {customer.industry}，城市 {customer.city}，等级 {customer.level}",
    )
    session.commit()
    session.refresh(customer)
    return customer


@app.patch("/api/customers/{customer_id}", response_model=CustomerRead, dependencies=[Depends(require_permission("crm:write"))])
def update_customer(customer_id: int, payload: CustomerUpdate, session: SessionDep) -> Customer:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    apply_updates(customer, patch_values(payload))
    if not customer.contact_person:
        customer.contact_person = customer.name or customer.company
    if not customer.name:
        customer.name = customer.contact_person or customer.company
    session.add(customer)
    add_business_audit(
        session,
        action="update",
        entity_type="customer",
        entity_id=customer.id,
        operator=customer.contact_person,
        summary=f"更新客户 {customer.company}",
        detail=", ".join(sorted(patch_values(payload).keys())) or "更新客户资料",
    )
    session.commit()
    session.refresh(customer)
    return customer


@app.delete("/api/customers/{customer_id}", dependencies=[Depends(require_permission("crm:write"))])
def delete_customer(customer_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    order = session.exec(select(SalesOrder).where(SalesOrder.customer_id == customer_id)).first()
    if order:
        raise HTTPException(status_code=400, detail="客户已有订单，不能直接删除")
    add_business_audit(
        session,
        action="delete",
        entity_type="customer",
        entity_id=customer_id,
        operator=customer.contact_person,
        summary=f"删除客户 {customer.company}",
        detail=f"客户 ID {customer_id}",
    )
    session.delete(customer)
    session.commit()
    return delete_response("customer", customer_id)


@app.get("/api/products", response_model=list[ProductRead] | PaginatedResponse[ProductRead], dependencies=[Depends(require_permission("crm:read"))])
def list_products(
    session: SessionDep,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    category: str = "",
) -> list[Product] | dict:
    products = session.exec(select(Product).order_by(Product.created_at.desc())).all()
    products = filter_records(products, q=q, fields=("name", "sku", "category"), category=category)
    return paginate_or_list(products, page=page, per_page=per_page)


@app.post("/api/products", response_model=ProductRead, status_code=201, dependencies=[Depends(require_permission("catalog:manage"))])
def create_product(payload: ProductCreate, session: SessionDep) -> Product:
    existing = session.exec(select(Product).where(Product.sku == payload.sku)).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU 已存在")
    product = Product(**payload.model_dump())
    session.add(product)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="product",
        entity_id=product.id,
        operator="商品管理员",
        summary=f"新建商品 {product.name}",
        detail=f"SKU {product.sku}，库存 {product.stock}，单价 {product.unit_price}",
    )
    session.commit()
    session.refresh(product)
    return product


@app.patch("/api/products/{product_id}", response_model=ProductRead, dependencies=[Depends(require_permission("catalog:manage"))])
def update_product(product_id: int, payload: ProductUpdate, session: SessionDep) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    updates = patch_values(payload)
    next_sku = updates.get("sku")
    if next_sku and next_sku != product.sku:
        existing = session.exec(select(Product).where(Product.sku == next_sku)).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU 已存在")
    apply_updates(product, updates)
    session.add(product)
    add_business_audit(
        session,
        action="update",
        entity_type="product",
        entity_id=product.id,
        operator="商品管理员",
        summary=f"更新商品 {product.name}",
        detail=", ".join(sorted(updates.keys())) or "更新商品资料",
    )
    session.commit()
    session.refresh(product)
    return product


@app.delete("/api/products/{product_id}", dependencies=[Depends(require_permission("catalog:manage"))])
def delete_product(product_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    order_item = session.exec(select(OrderItem).where(OrderItem.product_id == product_id)).first()
    movement = session.exec(select(InventoryMovement).where(InventoryMovement.product_id == product_id)).first()
    if order_item or movement:
        raise HTTPException(status_code=400, detail="商品已有订单或库存流水，不能直接删除")
    add_business_audit(
        session,
        action="delete",
        entity_type="product",
        entity_id=product_id,
        operator="商品管理员",
        summary=f"删除商品 {product.name}",
        detail=f"SKU {product.sku}",
    )
    session.delete(product)
    session.commit()
    return delete_response("product", product_id)


@app.get("/api/inventory/restock-alerts", response_model=list[InventoryRestockAlertRead], dependencies=[Depends(require_permission("crm:read"))])
def get_restock_alerts(session: SessionDep) -> list[InventoryRestockAlertRead]:
    return list_restock_alerts(session)


@app.get("/api/inventory/movements", response_model=list[InventoryMovementRead] | PaginatedResponse[InventoryMovementRead], dependencies=[Depends(require_permission("crm:read"))])
def get_inventory_movements(
    session: SessionDep,
    limit: int = 30,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    source: str = "",
) -> list[InventoryMovementRead] | dict:
    safe_limit = min(max(limit, 1), 100)
    has_filter = bool(q.strip() or source.strip())
    query_limit = None if page is not None or per_page is not None or has_filter else safe_limit
    statement = select(InventoryMovement).order_by(InventoryMovement.created_at.desc())
    if query_limit is not None:
        statement = statement.limit(query_limit)
    movements = [serialize_inventory_movement(movement, session) for movement in session.exec(statement).all()]
    movements = filter_records(movements, q=q, fields=("product_name", "sku", "reason", "operator", "source"), source=source)
    return paginate_or_list(movements, page=page, per_page=per_page)


@app.post("/api/products/{product_id}/restock", response_model=ProductRestockResponse, dependencies=[Depends(require_permission("inventory:manage"))])
def restock_product(product_id: int, payload: ProductRestockRequest, session: SessionDep) -> ProductRestockResponse:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    before_stock = product.stock
    product.stock += payload.quantity
    movement = InventoryMovement(
        product_id=product.id,
        change_quantity=payload.quantity,
        before_stock=before_stock,
        after_stock=product.stock,
        reason=payload.reason,
        operator=payload.operator,
        source="manual_restock",
    )
    session.add(product)
    session.add(movement)
    session.flush()
    add_business_audit(
        session,
        action="restock",
        entity_type="product",
        entity_id=product.id,
        operator=payload.operator,
        summary=f"补货 {product.name} {payload.quantity} 件",
        detail=f"库存 {before_stock} -> {product.stock}；原因：{payload.reason}",
    )
    session.commit()
    session.refresh(product)
    session.refresh(movement)
    return ProductRestockResponse(
        product=product,
        movement=serialize_inventory_movement(movement, session),
        alert=build_restock_alert(product, session),
    )


@app.get("/api/contacts", response_model=list[ContactRead] | PaginatedResponse[ContactRead], dependencies=[Depends(require_permission("crm:read"))])
def list_contacts(
    session: SessionDep,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    status: str = "",
) -> list[Contact] | dict:
    contacts = session.exec(select(Contact).order_by(Contact.created_at.desc())).all()
    contacts = filter_records(
        contacts,
        q=q,
        fields=("name", "company", "role", "email", "phone", "owner"),
        owner=owner,
        status=status,
    )
    return paginate_or_list(contacts, page=page, per_page=per_page)


@app.post("/api/contacts", response_model=ContactRead, status_code=201, dependencies=[Depends(require_permission("crm:write"))])
def create_contact(payload: ContactCreate, session: SessionDep) -> Contact:
    contact = Contact(**payload.model_dump())
    session.add(contact)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="contact",
        entity_id=contact.id,
        operator=contact.owner,
        summary=f"新建联系人 {contact.name}",
        detail=f"客户 {contact.company}，角色 {contact.role}",
    )
    session.commit()
    session.refresh(contact)
    return contact


@app.patch("/api/contacts/{contact_id}", response_model=ContactRead, dependencies=[Depends(require_permission("crm:write"))])
def update_contact(contact_id: int, payload: ContactUpdate, session: SessionDep) -> Contact:
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")
    updates = patch_values(payload)
    apply_updates(contact, updates)
    session.add(contact)
    add_business_audit(
        session,
        action="update",
        entity_type="contact",
        entity_id=contact.id,
        operator=contact.owner,
        summary=f"更新联系人 {contact.name}",
        detail=", ".join(sorted(updates.keys())) or "更新联系人资料",
    )
    session.commit()
    session.refresh(contact)
    return contact


@app.delete("/api/contacts/{contact_id}", dependencies=[Depends(require_permission("crm:write"))])
def delete_contact(contact_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")
    add_business_audit(
        session,
        action="delete",
        entity_type="contact",
        entity_id=contact_id,
        operator=contact.owner,
        summary=f"删除联系人 {contact.name}",
        detail=f"客户 {contact.company}",
    )
    session.delete(contact)
    session.commit()
    return delete_response("contact", contact_id)


@app.get("/api/leads", response_model=list[LeadRead] | PaginatedResponse[LeadRead], dependencies=[Depends(require_permission("crm:read"))])
def list_leads(
    session: SessionDep,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    stage: str = "",
    owner: str = "",
    region: str = "",
    ai_assisted: bool | None = None,
) -> list[SalesLead] | dict:
    leads = session.exec(select(SalesLead).order_by(SalesLead.due_date.asc())).all()
    leads = filter_records(
        leads,
        q=q,
        fields=("title", "customer_name", "owner", "region", "next_action"),
        stage=stage,
        owner=owner,
        region=region,
    )
    leads = filter_bool(leads, "ai_assisted", ai_assisted)
    return paginate_or_list(leads, page=page, per_page=per_page)


@app.post("/api/leads", response_model=LeadRead, status_code=201, dependencies=[Depends(require_permission("crm:write"))])
def create_lead(payload: SalesLeadCreate, session: SessionDep) -> SalesLead:
    lead = SalesLead(**payload.model_dump())
    session.add(lead)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="lead",
        entity_id=lead.id,
        operator=lead.owner,
        summary=f"新建商机 {lead.title}",
        detail=f"客户 {lead.customer_name}，阶段 {lead.stage.value}，金额 {lead.expected_amount:.0f}",
    )
    session.commit()
    session.refresh(lead)
    return lead


@app.patch("/api/leads/{lead_id}", response_model=LeadRead, dependencies=[Depends(require_permission("crm:write"))])
def update_lead(lead_id: int, payload: SalesLeadUpdate, session: SessionDep) -> SalesLead:
    lead = session.get(SalesLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="商机不存在")
    updates = patch_values(payload)
    apply_updates(lead, updates)
    session.add(lead)
    add_business_audit(
        session,
        action="update",
        entity_type="lead",
        entity_id=lead.id,
        operator=lead.owner,
        summary=f"更新商机 {lead.title}",
        detail=", ".join(sorted(updates.keys())) or "更新商机资料",
    )
    session.commit()
    session.refresh(lead)
    return lead


@app.delete("/api/leads/{lead_id}", dependencies=[Depends(require_permission("crm:write"))])
def delete_lead(lead_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    lead = session.get(SalesLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="商机不存在")
    add_business_audit(
        session,
        action="delete",
        entity_type="lead",
        entity_id=lead_id,
        operator=lead.owner,
        summary=f"删除商机 {lead.title}",
        detail=f"客户 {lead.customer_name}",
    )
    session.delete(lead)
    session.commit()
    return delete_response("lead", lead_id)


@app.get("/api/cases", response_model=list[SupportCaseRead] | PaginatedResponse[SupportCaseRead], dependencies=[Depends(require_permission("crm:read"))])
def list_cases(
    session: SessionDep,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    priority: str = "",
    status: str = "",
) -> list[SupportCase] | dict:
    cases = session.exec(select(SupportCase).order_by(SupportCase.due_date.asc())).all()
    cases = filter_records(
        cases,
        q=q,
        fields=("title", "account", "owner", "priority", "status", "status_label"),
        owner=owner,
        priority=priority,
        status=status,
    )
    return paginate_or_list(cases, page=page, per_page=per_page)


@app.post("/api/cases", response_model=SupportCaseRead, status_code=201, dependencies=[Depends(require_permission("crm:write"))])
def create_case(payload: SupportCaseCreate, session: SessionDep) -> SupportCase:
    support_case = SupportCase(**payload.model_dump())
    session.add(support_case)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="case",
        entity_id=support_case.id,
        operator=support_case.owner,
        summary=f"新建工单 {support_case.title}",
        detail=f"客户 {support_case.account}，状态 {support_case.status_label}",
    )
    session.commit()
    session.refresh(support_case)
    return support_case


@app.patch("/api/cases/{case_id}", response_model=SupportCaseRead, dependencies=[Depends(require_permission("crm:write"))])
def update_case(case_id: int, payload: SupportCaseUpdate, session: SessionDep) -> SupportCase:
    support_case = session.get(SupportCase, case_id)
    if not support_case:
        raise HTTPException(status_code=404, detail="工单不存在")
    updates = patch_values(payload)
    apply_updates(support_case, updates)
    session.add(support_case)
    add_business_audit(
        session,
        action="update",
        entity_type="case",
        entity_id=support_case.id,
        operator=support_case.owner,
        summary=f"更新工单 {support_case.title}",
        detail=", ".join(sorted(updates.keys())) or "更新工单资料",
    )
    session.commit()
    session.refresh(support_case)
    return support_case


@app.delete("/api/cases/{case_id}", dependencies=[Depends(require_permission("crm:write"))])
def delete_case(case_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    support_case = session.get(SupportCase, case_id)
    if not support_case:
        raise HTTPException(status_code=404, detail="工单不存在")
    add_business_audit(
        session,
        action="delete",
        entity_type="case",
        entity_id=case_id,
        operator=support_case.owner,
        summary=f"删除工单 {support_case.title}",
        detail=f"客户 {support_case.account}",
    )
    session.delete(support_case)
    session.commit()
    return delete_response("case", case_id)


@app.get("/api/tasks", response_model=list[TaskItemRead] | PaginatedResponse[TaskItemRead], dependencies=[Depends(require_permission("crm:read"))])
def list_tasks(
    session: SessionDep,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    priority: str = "",
    status: str = "",
) -> list[TaskItem] | dict:
    tasks = session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()
    tasks = filter_records(
        tasks,
        q=q,
        fields=("title", "description", "owner", "due_date", "priority", "status", "status_label"),
        owner=owner,
        priority=priority,
        status=status,
    )
    return paginate_or_list(tasks, page=page, per_page=per_page)


@app.post("/api/tasks", response_model=TaskItemRead, status_code=201, dependencies=[Depends(require_permission("crm:write"))])
def create_task(payload: TaskItemCreate, session: SessionDep) -> TaskItem:
    task = TaskItem(**payload.model_dump())
    session.add(task)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="task",
        entity_id=task.id,
        operator=task.owner,
        summary=f"新建任务 {task.title}",
        detail=f"状态 {task.status_label}，优先级 {task.priority}",
    )
    session.commit()
    session.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}", response_model=TaskItemRead, dependencies=[Depends(require_permission("crm:write"))])
def update_task(task_id: int, payload: TaskItemUpdate, session: SessionDep) -> TaskItem:
    task = session.get(TaskItem, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    updates = patch_values(payload)
    apply_updates(task, updates)
    session.add(task)
    add_business_audit(
        session,
        action="update",
        entity_type="task",
        entity_id=task.id,
        operator=task.owner,
        summary=f"更新任务 {task.title}",
        detail=", ".join(sorted(updates.keys())) or "更新任务资料",
    )
    session.commit()
    session.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}", dependencies=[Depends(require_permission("crm:write"))])
def delete_task(task_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    task = session.get(TaskItem, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    add_business_audit(
        session,
        action="delete",
        entity_type="task",
        entity_id=task_id,
        operator=task.owner,
        summary=f"删除任务 {task.title}",
        detail=f"状态 {task.status_label}",
    )
    session.delete(task)
    session.commit()
    return delete_response("task", task_id)


@app.get("/api/goals", response_model=list[SalesGoalRead] | PaginatedResponse[SalesGoalRead], dependencies=[Depends(require_permission("crm:read"))])
def list_goals(
    session: SessionDep,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    period: str = "",
) -> list[SalesGoal] | dict:
    goals = session.exec(select(SalesGoal).order_by(SalesGoal.created_at.desc())).all()
    goals = filter_records(goals, q=q, fields=("name", "period", "note"), period=period)
    return paginate_or_list(goals, page=page, per_page=per_page)


@app.post("/api/goals", response_model=SalesGoalRead, status_code=201, dependencies=[Depends(require_permission("crm:write"))])
def create_goal(payload: SalesGoalCreate, session: SessionDep) -> SalesGoal:
    progress = payload.progress
    if progress is None:
        progress = round(payload.current / payload.target * 100) if payload.target else 0
    goal = SalesGoal(
        name=payload.name,
        period=payload.period,
        current=payload.current,
        target=payload.target,
        progress=min(max(progress, 0), 100),
        note=payload.note,
    )
    session.add(goal)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="goal",
        entity_id=goal.id,
        operator="目标管理员",
        summary=f"新建销售目标 {goal.name}",
        detail=f"周期 {goal.period}，进度 {goal.progress}%",
    )
    session.commit()
    session.refresh(goal)
    return goal


@app.patch("/api/goals/{goal_id}", response_model=SalesGoalRead, dependencies=[Depends(require_permission("crm:write"))])
def update_goal(goal_id: int, payload: SalesGoalUpdate, session: SessionDep) -> SalesGoal:
    goal = session.get(SalesGoal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")
    updates = patch_values(payload)
    apply_updates(goal, updates)
    if "progress" not in updates and goal.target:
        goal.progress = min(max(round(goal.current / goal.target * 100), 0), 100)
    session.add(goal)
    add_business_audit(
        session,
        action="update",
        entity_type="goal",
        entity_id=goal.id,
        operator="目标管理员",
        summary=f"更新销售目标 {goal.name}",
        detail=", ".join(sorted(updates.keys())) or "更新目标资料",
    )
    session.commit()
    session.refresh(goal)
    return goal


@app.delete("/api/goals/{goal_id}", dependencies=[Depends(require_permission("crm:write"))])
def delete_goal(goal_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    goal = session.get(SalesGoal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")
    add_business_audit(
        session,
        action="delete",
        entity_type="goal",
        entity_id=goal_id,
        operator="目标管理员",
        summary=f"删除销售目标 {goal.name}",
        detail=f"周期 {goal.period}",
    )
    session.delete(goal)
    session.commit()
    return delete_response("goal", goal_id)


@app.get("/api/ai-audit-logs", response_model=list[AIInteractionLogRead] | PaginatedResponse[AIInteractionLogRead], dependencies=[Depends(require_permission("audit:read"))])
def list_ai_audit_logs(
    session: SessionDep,
    limit: int = 30,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    operation: str = "",
    status: str = "",
    entity_type: str = "",
    fallback_used: bool | None = None,
) -> list[AIInteractionLog] | dict:
    safe_limit = min(max(limit, 1), 100)
    has_filter = bool(q.strip() or operation.strip() or status.strip() or entity_type.strip() or fallback_used is not None)
    query_limit = None if page is not None or per_page is not None or has_filter else safe_limit
    statement = select(AIInteractionLog).order_by(AIInteractionLog.created_at.desc())
    if query_limit is not None:
        statement = statement.limit(query_limit)
    logs = session.exec(statement).all()
    logs = filter_records(
        logs,
        q=q,
        fields=("operation", "provider", "model", "status", "entity_type", "request_summary", "response_summary"),
        operation=operation,
        status=status,
        entity_type=entity_type,
    )
    logs = filter_bool(logs, "fallback_used", fallback_used)
    return paginate_or_list(logs, page=page, per_page=per_page)


@app.get("/api/business-audit-logs", response_model=list[BusinessAuditLogRead] | PaginatedResponse[BusinessAuditLogRead], dependencies=[Depends(require_permission("audit:read"))])
def list_business_audit_logs(
    session: SessionDep,
    limit: int = 40,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    action: str = "",
    entity_type: str = "",
    operator: str = "",
    status: str = "",
) -> list[BusinessAuditLog] | dict:
    safe_limit = min(max(limit, 1), 120)
    has_filter = bool(q.strip() or action.strip() or entity_type.strip() or operator.strip() or status.strip())
    query_limit = None if page is not None or per_page is not None or has_filter else safe_limit
    statement = select(BusinessAuditLog).order_by(BusinessAuditLog.created_at.desc())
    if query_limit is not None:
        statement = statement.limit(query_limit)
    logs = session.exec(statement).all()
    logs = filter_records(
        logs,
        q=q,
        fields=("action", "entity_type", "operator", "status", "summary", "detail"),
        action=action,
        entity_type=entity_type,
        operator=operator,
        status=status,
    )
    return paginate_or_list(logs, page=page, per_page=per_page)


@app.get("/api/orders", response_model=list[SalesOrderRead] | PaginatedResponse[SalesOrderRead], dependencies=[Depends(require_permission("order:manage"))])
def list_orders(
    session: SessionDep,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    region: str = "",
    status: str = "",
    created_by_ai: bool | None = None,
) -> list[SalesOrderRead] | dict:
    orders = session.exec(select(SalesOrder).order_by(SalesOrder.created_at.desc())).all()
    serialized_orders = [serialize_order(order, session) for order in orders]
    serialized_orders = filter_records(
        serialized_orders,
        q=q,
        fields=("customer_name", "owner", "region", "currency", "status", "notes"),
        owner=owner,
        region=region,
        status=status,
    )
    serialized_orders = filter_bool(serialized_orders, "created_by_ai", created_by_ai)
    return paginate_or_list(serialized_orders, page=page, per_page=per_page)


@app.get("/api/orders/export.csv", dependencies=[Depends(require_permission("order:manage"))])
def export_orders_csv(session: SessionDep) -> Response:
    orders = session.exec(select(SalesOrder).order_by(SalesOrder.created_at.desc())).all()
    csv_content = build_orders_csv([serialize_order(order, session) for order in orders])
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="smart-crm-orders.csv"'},
    )


@app.get("/api/orders/{order_id}/inventory-movements", response_model=list[InventoryMovementRead], dependencies=[Depends(require_permission("order:manage"))])
def get_order_inventory_movements(order_id: int, session: SessionDep) -> list[InventoryMovementRead]:
    order = session.get(SalesOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    order_marker = f"订单 #{order_id} "
    movements = session.exec(
        select(InventoryMovement)
        .where(InventoryMovement.reason.contains(order_marker))
        .order_by(InventoryMovement.created_at.desc())
    ).all()
    return [serialize_inventory_movement(movement, session) for movement in movements]


@app.patch("/api/orders/{order_id}", response_model=SalesOrderRead, dependencies=[Depends(require_permission("order:manage"))])
def update_order(order_id: int, payload: SalesOrderUpdate, session: SessionDep) -> SalesOrderRead:
    order = session.get(SalesOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    before_total = order.total_amount
    updates = payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"items"})
    apply_updates(order, updates)
    if payload.items is not None:
        replace_order_items(order, payload.items, session)
    session.add(order)
    changed_fields = sorted(updates.keys())
    if payload.items is not None:
        changed_fields.append("items")
    add_business_audit(
        session,
        action="update",
        entity_type="order",
        entity_id=order.id,
        operator=order.owner,
        summary=f"更新订单 #{order.id}",
        detail=f"字段：{', '.join(changed_fields) or '无'}；金额 {before_total:.0f} -> {order.total_amount:.0f}",
    )
    session.commit()
    session.refresh(order)
    return serialize_order(order, session)


@app.post("/api/orders", response_model=SalesOrderRead, status_code=201, dependencies=[Depends(require_permission("order:manage"))])
def create_order(payload: SalesOrderCreate, session: SessionDep) -> SalesOrderRead:
    customer = session.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    product_ids = [item.product_id for item in payload.items]
    products = session.exec(select(Product).where(Product.id.in_(product_ids))).all()
    product_map = {product.id: product for product in products}
    if len(product_map) != len(product_ids):
        raise HTTPException(status_code=400, detail="存在无效商品")
    for item in payload.items:
        product = product_map[item.product_id]
        if item.quantity > product.stock:
            raise HTTPException(status_code=400, detail=f"{product.name} 库存不足，当前仅剩 {product.stock} 件")

    order = SalesOrder(
        customer_id=payload.customer_id,
        owner=payload.owner,
        region=payload.region,
        currency=payload.currency,
        status=payload.status,
        order_date=payload.order_date,
        due_date=payload.due_date,
        notes=payload.notes,
        created_by_ai=payload.created_by_ai,
        ai_confidence_score=payload.ai_confidence_score,
    )
    session.add(order)
    session.flush()

    total_amount = 0.0
    for item in payload.items:
        product = product_map[item.product_id]
        line_total = item.quantity * item.unit_price
        total_amount += line_total
        before_stock = product.stock
        product.stock = max(product.stock - item.quantity, 0)
        session.add(product)
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=line_total,
            )
        )
        session.add(
            InventoryMovement(
                product_id=product.id,
                change_quantity=-item.quantity,
                before_stock=before_stock,
                after_stock=product.stock,
                reason=f"订单 #{order.id} 创建扣减库存",
                operator=payload.owner,
                source="order_deduction",
            )
        )

    order.total_amount = total_amount
    session.add(order)
    add_business_audit(
        session,
        action="create",
        entity_type="order",
        entity_id=order.id,
        operator=payload.owner,
        summary=f"创建订单 #{order.id}",
        detail=f"客户 {customer.company}，明细 {len(payload.items)} 条，总额 {order.total_amount:.0f}",
    )
    session.commit()
    session.refresh(order)
    return serialize_order(order, session)


@app.post("/api/vision-extract", response_model=VisionExtractResponse, dependencies=[Depends(require_permission("ai:use"))])
async def vision_extract(file: Annotated[UploadFile, File(...)], session: SessionDep) -> VisionExtractResponse:
    start_time = perf_counter()
    filename = file.filename or "uploaded-file"
    content_type = file.content_type or "unknown"
    customers = session.exec(select(Customer)).all()
    products = session.exec(select(Product)).all()
    result = await vision_service.extract(file, customers=customers, products=products)
    save_ai_interaction(
        session,
        operation="vision_extract",
        model=settings.llm_vision_model or settings.llm_model,
        fallback_used=result.fallback_used,
        start_time=start_time,
        request_summary=f"{filename} / {content_type} / {len(customers)} customers / {len(products)} products",
        response_summary=f"{result.company} / {result.source} / {len(result.items)} items / {result.summary}",
    )
    return result


@app.get("/api/copilot/summary", response_model=CopilotSummaryResponse, dependencies=[Depends(require_permission("ai:use"))])
async def copilot_summary(session: SessionDep) -> CopilotSummaryResponse:
    start_time = perf_counter()
    leads = session.exec(select(SalesLead).order_by(SalesLead.due_date.asc())).all()
    result = await copilot_service.summarize(leads)
    save_ai_interaction(
        session,
        operation="copilot_summary",
        model=settings.llm_model,
        fallback_used=result.fallback_used,
        start_time=start_time,
        request_summary=f"{len(leads)} leads",
        response_summary=result.llm_summary,
        entity_type="lead",
        entity_id=result.top_opportunity.id if result.top_opportunity else None,
    )
    return result


@app.post("/api/copilot/follow-up", response_model=CopilotFollowUpResponse, dependencies=[Depends(require_permission("ai:use"))])
async def copilot_follow_up(payload: CopilotFollowUpRequest, session: SessionDep) -> CopilotFollowUpResponse:
    start_time = perf_counter()
    lead = session.get(SalesLead, payload.lead_id) if payload.lead_id else None
    if payload.lead_id and not lead:
        raise HTTPException(status_code=404, detail="商机不存在")
    result = await copilot_service.follow_up(payload, lead)
    save_ai_interaction(
        session,
        operation="copilot_follow_up",
        model=settings.llm_model,
        fallback_used=result.fallback_used,
        start_time=start_time,
        request_summary=lead.title if lead else f"{payload.customer_name} / {payload.opportunity_title}",
        response_summary=result.message_draft,
        entity_type="lead" if lead else "",
        entity_id=lead.id if lead else None,
    )
    return result


@app.post("/api/copilot/order-draft", response_model=CopilotOrderDraftResponse, dependencies=[Depends(require_permission("ai:use"))])
async def copilot_order_draft(payload: CopilotOrderDraftRequest, session: SessionDep) -> CopilotOrderDraftResponse:
    start_time = perf_counter()
    customer = session.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    if payload.product_ids:
        products = session.exec(select(Product).where(Product.id.in_(payload.product_ids))).all()
        if len(products) != len(set(payload.product_ids)):
            raise HTTPException(status_code=400, detail="存在无效商品")
    else:
        products = session.exec(select(Product).order_by(Product.created_at.desc())).all()

    if not products:
        raise HTTPException(status_code=400, detail="没有可用于生成草稿的商品")

    result = await copilot_service.order_draft(customer, products, payload.business_goal)
    save_ai_interaction(
        session,
        operation="copilot_order_draft",
        model=settings.llm_model,
        fallback_used=result.fallback_used,
        start_time=start_time,
        request_summary=f"{customer.company} / {len(products)} products / {payload.business_goal}",
        response_summary=result.llm_summary,
        entity_type="customer",
        entity_id=customer.id,
    )
    return result


@app.get("/api/dashboard", response_model=DashboardResponse, dependencies=[Depends(require_permission("dashboard:read"))])
def get_dashboard(session: SessionDep) -> DashboardResponse:
    orders = session.exec(select(SalesOrder)).all()
    leads = session.exec(select(SalesLead)).all()
    customers = session.exec(select(Customer)).all()

    total_revenue = sum(order.total_amount for order in orders)
    ai_orders = [order for order in orders if order.created_by_ai]
    pending_leads = [lead for lead in leads if lead.stage not in {"won", "lost"}]

    metrics = [
        DashboardMetric(label="本月订单额", value=f"¥{total_revenue:,.0f}", hint="含 AI 与手工录单"),
        DashboardMetric(label="AI 参与订单", value=str(len(ai_orders)), hint="支持审计追踪"),
        DashboardMetric(label="在跟进商机", value=str(len(pending_leads)), hint="待转化线索"),
        DashboardMetric(label="客户总数", value=str(len(customers)), hint="已沉淀客户资产"),
    ]

    revenue_bucket: dict[str, float] = defaultdict(float)
    for order in orders:
        month_key = order.order_date.strftime("%Y-%m")
        revenue_bucket[month_key] += order.total_amount
    revenue_trend = [
        RevenuePoint(month=month, revenue=amount)
        for month, amount in sorted(revenue_bucket.items())
    ]

    stage_counter = Counter(lead.stage.value for lead in leads)
    stage_distribution = [{"stage": stage, "count": count} for stage, count in stage_counter.items()]

    recent_orders = sorted(orders, key=lambda item: item.created_at, reverse=True)[:5]
    urgent_leads = sorted(leads, key=lambda item: item.due_date)[:5]
    ai_orders_ratio = round(len(ai_orders) / len(orders), 2) if orders else 0.0

    return DashboardResponse(
        metrics=metrics,
        revenue_trend=revenue_trend,
        stage_distribution=stage_distribution,
        ai_orders_ratio=ai_orders_ratio,
        urgent_leads=urgent_leads,
        recent_orders=[serialize_order(order, session) for order in recent_orders],
    )
