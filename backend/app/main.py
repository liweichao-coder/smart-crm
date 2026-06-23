from __future__ import annotations

import csv
import io
import json
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from math import ceil
from time import perf_counter
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from .auth import generate_session_token, hash_password, hash_session_token, verify_password
from .config import settings
from .consistency import build_consistency_payload
from .database import create_db_and_tables, engine, get_session
from .models import AIInteractionLog, AuthAuditLog, AuthSession, AuthUser, BusinessAuditLog, CaptureDraft, Contact, CopilotRecommendation, Customer, CustomerActivity, InventoryMovement, LeadStage, NotificationState, OrderApprovalRequest, OrderApprovalStatus, OrderItem, OrderStatus, Organization, Product, ReportSnapshot, SalesGoal, SalesLead, SalesOrder, SupportCase, TaskItem, UserPreference
from .schemas import (
    AIInteractionLogRead,
    AIQualityModelBreakdown,
    AIQualityOperationBreakdown,
    AIQualityRecommendationSignal,
    AIQualityReportResponse,
    AuthAuditLogRead,
    AuthLoginRequest,
    AuthLogoutResponse,
    AuthMeResponse,
    AuthOrganizationRead,
    AuthPasswordChangeRequest,
    AuthPasswordChangeResponse,
    AuthProfileUpdate,
    AuthRegisterRequest,
    AuthSessionBulkRevokeResponse,
    AuthSessionRead,
    AuthSessionResponse,
    AuthUserRead,
    ApprovalPerformanceReportResponse,
    ApprovalReportDistributionItem,
    ApprovalReviewerWorkload,
    BusinessAuditLogRead,
    CaptureDraftRead,
    CaptureDraftUpdate,
    ContactCreate,
    ContactRead,
    ContactUpdate,
    ConsistencyReportResponse,
    CopilotAskRequest,
    CopilotAskResponse,
    CopilotFollowUpRequest,
    CopilotFollowUpResponse,
    CopilotOrderDraftRequest,
    CopilotOrderDraftResponse,
    CopilotRecommendationFeedbackRequest,
    CopilotRecommendationRead,
    CopilotSummaryResponse,
    CustomerCreate,
    CustomerActivityCreate,
    CustomerActivityRead,
    CustomerActivityUpdate,
    CustomerHealthAction,
    CustomerHealthFactor,
    CustomerHealthProfile,
    CustomerRead,
    CustomerUpdate,
    CustomerTimelineItem,
    CustomerWorkspaceResponse,
    DashboardMetric,
    DashboardResponse,
    InventoryMovementRead,
    InventoryRestockAlertRead,
    LeadRead,
    OrderItemRead,
    OrderApprovalAssignmentCreate,
    OrderApprovalCreate,
    OrderApprovalDecision,
    OrderApprovalReminderCreate,
    OrderApprovalRead,
    NotificationBulkUpdateResponse,
    NotificationRead,
    NotificationStateResponse,
    NotificationStateUpdate,
    PaginatedResponse,
    ModulePermissionRead,
    PermissionCatalogItem,
    PermissionMatrixResponse,
    RolePermissionRead,
    ProductCreate,
    ProductRestockRequest,
    ProductRestockResponse,
    ProductRead,
    ProductUpdate,
    RevenuePoint,
    ReportSnapshotCreate,
    ReportSnapshotRead,
    SalesGoalCreate,
    SalesGoalRead,
    SalesGoalUpdate,
    SalesLeadCreate,
    SalesLeadUpdate,
    SalesPerformanceReportResponse,
    SalesReportAiImpact,
    SalesReportBreakdown,
    SalesReportFunnelStage,
    SalesOrderCreate,
    SalesOrderRead,
    SalesOrderUpdate,
    SupportCaseCreate,
    SupportCaseRead,
    SupportCaseUpdate,
    TaskItemCreate,
    TaskItemRead,
    TaskItemUpdate,
    TeamMemberCreate,
    TeamMemberUpdate,
    UserPreferenceRead,
    UserPreferenceUpdate,
    VisionExtractResponse,
    VisionExtractItem,
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
AUTH_LOGIN_FAILURE_LIMIT = 5
AUTH_LOGIN_LOCK_WINDOW_MINUTES = 15
ORDER_APPROVAL_AMOUNT_THRESHOLD = 100000
ORDER_APPROVAL_AI_CONFIDENCE_THRESHOLD = 0.85
ORDER_APPROVAL_FAST_DELIVERY_DAYS = 7
ORDER_APPROVAL_ITEM_COUNT_THRESHOLD = 3
ORDER_APPROVAL_REQUIRED_STATUSES = {OrderStatus.confirmed, OrderStatus.fulfilled}
ORDER_APPROVAL_RISK_SLA_HOURS = {
    "critical": 4,
    "high": 12,
    "medium": 24,
    "low": 48,
}
ORDER_APPROVAL_RISK_LABELS = {
    "critical": "关键",
    "high": "高",
    "medium": "中",
    "low": "低",
}
HEALTH_DEMO_DATA_TARGETS = [
    ("organizations", Organization, 1),
    ("users", AuthUser, 5),
    ("customers", Customer, 12),
    ("products", Product, 10),
    ("contacts", Contact, 12),
    ("customer_activities", CustomerActivity, 16),
    ("leads_opportunities", SalesLead, 15),
    ("support_cases", SupportCase, 8),
    ("tasks", TaskItem, 8),
    ("sales_goals", SalesGoal, 4),
    ("orders", SalesOrder, 12),
    ("order_items", OrderItem, 22),
    ("inventory_movements", InventoryMovement, 22),
    ("order_approvals", OrderApprovalRequest, 2),
]
ALL_PERMISSIONS = "*"
KNOWN_PERMISSIONS = {
    "approval:manage",
    "ai:use",
    "audit:read",
    "catalog:manage",
    "crm:read",
    "crm:write",
    "dashboard:read",
    "inventory:manage",
    "order:manage",
    "permissions:read",
    "reports:read",
    "team:manage",
}
ROLE_PERMISSIONS = {
    "管理员": {ALL_PERMISSIONS},
    "销售": {"crm:read", "crm:write", "order:manage", "ai:use", "dashboard:read"},
    "销售经理": {"crm:read", "crm:write", "order:manage", "approval:manage", "ai:use", "dashboard:read", "reports:read", "audit:read", "permissions:read", "team:manage"},
    "支持": {"crm:read", "case:write", "task:write", "dashboard:read"},
    "审计员": {"crm:read", "reports:read", "audit:read", "dashboard:read", "permissions:read"},
}
ROLE_DESCRIPTIONS = {
    "管理员": "系统管理员，拥有组织内所有模块和配置权限。",
    "销售": "一线销售角色，可维护客户、线索、订单并使用 AI 副驾。",
    "销售经理": "团队主管角色，可查看报表、审计和权限矩阵。",
    "支持": "实施/售后角色，可查看 CRM 基础信息和处理服务协作。",
    "审计员": "审计与管理角色，可查看报表、审计和权限矩阵。",
}
OWN_DATA_SCOPE_ROLES = {"销售"}
PERMISSION_CATALOG = {
    "approval:manage": ("审批", "订单审批", "审批或驳回订单确认申请，并推进订单状态。"),
    "ai:use": ("AI 能力", "AI 副驾与智能录单", "调用 Copilot、跟进话术、订单草稿和智能录单接口。"),
    "audit:read": ("审计", "审计读取", "查看认证审计、AI 审计和业务操作审计。"),
    "catalog:manage": ("商品", "商品目录维护", "创建、编辑和删除商品目录与 SKU。"),
    "crm:read": ("CRM", "CRM 数据读取", "查看客户、联系人、互动记录、线索、工单、任务和目标。"),
    "crm:write": ("CRM", "CRM 数据维护", "创建、编辑和删除客户、联系人、互动记录、线索、工单、任务和目标。"),
    "dashboard:read": ("BI", "仪表盘查看", "查看经营仪表盘和首页概览。"),
    "inventory:manage": ("库存", "库存补货", "执行商品补货并写入库存流水。"),
    "order:manage": ("订单", "订单管理", "创建、编辑、导出订单并查看订单库存审计。"),
    "permissions:read": ("权限", "权限矩阵查看", "查看角色、权限和模块访问矩阵。"),
    "reports:read": ("BI", "销售报表查看", "查看销售 BI 报表和聚合指标。"),
    "team:manage": ("组织", "团队成员管理", "创建成员、调整角色和停用账号。"),
}
MODULE_PERMISSIONS = [
    ("/dashboard", "仪表盘", "dashboard:read"),
    ("/reports", "销售报表", "reports:read"),
    ("/team", "团队成员", "team:manage"),
    ("/copilot", "AI 副驾", "ai:use"),
    ("/ai-audit", "AI 审计", "audit:read"),
    ("/business-audit", "操作审计", "audit:read"),
    ("/permissions", "权限矩阵", "permissions:read"),
    ("/capture", "智能录单", "ai:use"),
    ("/orders", "订单", "order:manage"),
    ("/products", "商品", "catalog:manage"),
    ("/leads", "线索", "crm:read"),
    ("/contacts", "联系人", "crm:read"),
    ("/accounts", "客户", "crm:read"),
    ("/opportunities", "商机", "crm:read"),
    ("/goals", "销售目标", "crm:read"),
    ("/cases", "工单", "crm:read"),
    ("/tasks", "任务", "crm:read"),
]
REPORT_STAGE_LABELS = {
    "new": "新线索",
    "qualified": "资格确认",
    "proposal": "方案提案",
    "negotiation": "商务谈判",
    "won": "已成交",
    "lost": "已丢单",
}

APPROVAL_STATUS_LABELS = {
    "pending": "待审批",
    "approved": "已通过",
    "rejected": "已驳回",
}
APPROVAL_SLA_LABELS = {
    "overdue": "已逾期",
    "due_soon": "临近截止",
    "on_track": "正常推进",
    "closed": "已关闭",
    "unset": "未设置",
}
AI_OPERATION_LABELS = {
    "copilot_summary": "副驾摘要",
    "copilot_follow_up": "跟进话术",
    "copilot_ask": "经营问答",
    "copilot_order_draft": "订单草稿",
    "vision_extract": "智能录单",
    "customer_account_plan": "客户经营计划",
}

COPILOT_FEEDBACK_DEFAULT_RATINGS = {
    "accepted": 5,
    "helpful": 4,
    "not_helpful": 2,
    "dismissed": 1,
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


def permissions_for_role(role: str) -> list[str]:
    permissions = ROLE_PERMISSIONS.get(role, {"crm:read"})
    if ALL_PERMISSIONS in permissions:
        return sorted(KNOWN_PERMISSIONS)
    return sorted(permissions)


def role_has_permission(role: str, permission: str) -> bool:
    permissions = ROLE_PERMISSIONS.get(role, {"crm:read"})
    return ALL_PERMISSIONS in permissions or permission in permissions


def validate_team_role(role: str, current_user: AuthUser) -> str:
    normalized_role = str(role or "").strip()
    if normalized_role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="无效角色")
    if normalized_role == "管理员" and current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="只有管理员可以授予管理员角色")
    return normalized_role


def validate_user_status(status: str) -> str:
    normalized_status = str(status or "").strip() or "active"
    if normalized_status not in {"active", "inactive"}:
        raise HTTPException(status_code=400, detail="无效账号状态")
    return normalized_status


def data_scope_for_role(role: str) -> str:
    return "own" if role in OWN_DATA_SCOPE_ROLES else "all"


def has_all_data_scope(user: AuthUser) -> bool:
    return data_scope_for_role(user.role) == "all"


def owner_matches_user(owner: str, user: AuthUser) -> bool:
    return normalize_account(owner) == normalize_account(user.full_name)


def organization_matches(record, user: AuthUser) -> bool:
    return getattr(record, "organization_id", user.organization_id) == user.organization_id


def filter_by_organization_scope(records: list, user: AuthUser) -> list:
    return [record for record in records if organization_matches(record, user)]


def require_organization_scope(user: AuthUser, record, detail: str = "数据不属于当前组织") -> None:
    if not organization_matches(record, user):
        raise HTTPException(status_code=404, detail=detail)


def filter_by_owner_scope(records: list, user: AuthUser, owner_field: str = "owner") -> list:
    if has_all_data_scope(user):
        return records
    return [record for record in records if owner_matches_user(getattr(record, owner_field, ""), user)]


def require_owner_scope(user: AuthUser, owner: str, detail: str = "当前账号没有该数据范围权限") -> None:
    if not has_all_data_scope(user) and not owner_matches_user(owner, user):
        raise HTTPException(status_code=403, detail=detail)


def require_payload_owner_scope(user: AuthUser, owner: str) -> None:
    if not has_all_data_scope(user) and owner and not owner_matches_user(owner, user):
        raise HTTPException(status_code=403, detail="只能创建或指派给自己的业务数据")


def normalize_payload_owner(owner: str | None, user: AuthUser) -> str:
    owner_text = (owner or "").strip()
    if owner_text in {"", "未分配", "待分配", "新负责人"}:
        return user.full_name
    return owner_text


def normalize_related_owner(owner: str | None, user: AuthUser, fallback_owner: str) -> str:
    owner_text = (owner or "").strip()
    if owner_text in {"", "未分配", "待分配", "新负责人"}:
        return fallback_owner if has_all_data_scope(user) else user.full_name
    return owner_text


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
        data_scope=data_scope_for_role(user.role),
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


def serialize_auth_session(auth_session: AuthSession, current_session: AuthSession) -> AuthSessionRead:
    now = datetime.utcnow()
    if auth_session.revoked_at is not None:
        status = "revoked"
    elif auth_session.expires_at <= now:
        status = "expired"
    else:
        status = "active"
    return AuthSessionRead(
        id=auth_session.id,
        current=auth_session.id == current_session.id,
        status=status,
        created_at=auth_session.created_at,
        expires_at=auth_session.expires_at,
        revoked_at=auth_session.revoked_at,
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


def recent_failed_login_count(session: Session, account: str) -> int:
    cutoff = datetime.utcnow() - timedelta(minutes=AUTH_LOGIN_LOCK_WINDOW_MINUTES)
    logs = session.exec(
        select(AuthAuditLog).where(
            AuthAuditLog.event == "login",
            AuthAuditLog.account == summarize_text(account, limit=120),
            AuthAuditLog.status == "failed",
            AuthAuditLog.created_at >= cutoff,
        )
    ).all()
    return len(logs)


def ensure_login_not_throttled(session: Session, account: str, user: AuthUser | None = None) -> None:
    failed_count = recent_failed_login_count(session, account)
    if failed_count < AUTH_LOGIN_FAILURE_LIMIT:
        return
    detail = f"{AUTH_LOGIN_LOCK_WINDOW_MINUTES} 分钟内登录失败 {failed_count} 次，已临时锁定登录。"
    record_auth_audit(session, event="login", account=account, status="blocked", detail=detail, user=user)
    session.commit()
    raise HTTPException(status_code=429, detail=f"登录失败次数过多，请 {AUTH_LOGIN_LOCK_WINDOW_MINUTES} 分钟后再试")


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


def list_restock_alerts(session: Session, organization_id: int | None = None) -> list[InventoryRestockAlertRead]:
    products = session.exec(select(Product)).all()
    if organization_id is not None:
        products = [product for product in products if product.organization_id == organization_id]
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
    organization_id: int = 1,
) -> None:
    latency_ms = max(0, round((perf_counter() - start_time) * 1000))
    log = AIInteractionLog(
        organization_id=organization_id,
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


def normalize_stage_value(stage) -> str:
    if stage is None:
        return ""
    if hasattr(stage, "value"):
        return str(stage.value)
    return str(stage)


def encode_score_reasons(reasons: list[str]) -> str:
    return json.dumps([str(reason) for reason in reasons if str(reason).strip()], ensure_ascii=False)


def decode_score_reasons(raw: str) -> list[str]:
    try:
        payload = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [str(item) for item in payload if str(item).strip()]


def validate_preference_namespace(namespace: str) -> str:
    normalized = namespace.strip()
    if len(normalized) < 2 or len(normalized) > 120:
        raise HTTPException(status_code=400, detail="偏好命名空间长度需为 2-120 个字符")
    return normalized


def encode_preference_value(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False)


def decode_preference_value(raw: str) -> dict:
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def encode_json_object(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def decode_json_object(raw: str) -> dict:
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def encode_json_list(value: list) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def decode_json_list(raw: str) -> list:
    try:
        payload = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


REPORT_SNAPSHOT_LABELS = {
    "sales_performance": "销售绩效",
    "approval_performance": "审批 SLA",
}
COPILOT_SUMMARY_DEDUPE_WINDOW = timedelta(minutes=10)


def parse_snapshot_date_filter(filters: dict, key: str) -> date | None:
    value = str(filters.get(key) or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"{key} 日期格式无效") from exc


def normalize_report_snapshot_filters(filters: dict) -> dict[str, str]:
    normalized_filters = {
        "date_from": str(filters.get("date_from") or "").strip(),
        "date_to": str(filters.get("date_to") or "").strip(),
        "owner": str(filters.get("owner") or "").strip(),
        "region": str(filters.get("region") or "").strip(),
    }
    date_from = parse_snapshot_date_filter(normalized_filters, "date_from")
    date_to = parse_snapshot_date_filter(normalized_filters, "date_to")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")
    return normalized_filters


def build_report_snapshot_payload(session: Session, report_type: str, filters: dict[str, str], current_user: AuthUser) -> dict:
    date_from = parse_snapshot_date_filter(filters, "date_from")
    date_to = parse_snapshot_date_filter(filters, "date_to")
    if report_type == "sales_performance":
        report = get_sales_performance_report(
            session,
            date_from=date_from,
            date_to=date_to,
            owner=filters.get("owner", ""),
            region=filters.get("region", ""),
            current_user=current_user,
        )
    else:
        report = get_approval_performance_report(
            session,
            date_from=date_from,
            date_to=date_to,
            owner=filters.get("owner", ""),
            region=filters.get("region", ""),
            current_user=current_user,
        )
    return report.model_dump(mode="json")


def build_report_snapshot_summary(payload: dict, report_type: str) -> str:
    metrics = payload.get("metrics")
    if isinstance(metrics, list) and metrics:
        metric_parts = []
        for metric in metrics[:3]:
            if isinstance(metric, dict):
                label = str(metric.get("label") or "").strip()
                value = str(metric.get("value") or "").strip()
                if label and value:
                    metric_parts.append(f"{label} {value}")
        if metric_parts:
            return "；".join(metric_parts)
    return f"{REPORT_SNAPSHOT_LABELS.get(report_type, report_type)} 报表快照已保存"


def serialize_report_snapshot(snapshot: ReportSnapshot) -> ReportSnapshotRead:
    payload = decode_json_object(snapshot.payload_json)
    metrics = payload.get("metrics")
    metric_count = len(metrics) if isinstance(metrics, list) else 0
    return ReportSnapshotRead(
        id=snapshot.id or 0,
        report_type=snapshot.report_type,
        report_type_label=REPORT_SNAPSHOT_LABELS.get(snapshot.report_type, snapshot.report_type),
        title=snapshot.title,
        filters=decode_json_object(snapshot.filters_json),
        payload=payload,
        summary=snapshot.summary,
        metric_count=metric_count,
        created_by=snapshot.created_by,
        created_at=snapshot.created_at,
    )


def serialize_capture_draft(draft: CaptureDraft) -> CaptureDraftRead:
    items: list[VisionExtractItem] = []
    for raw_item in decode_json_list(draft.items_json):
        if not isinstance(raw_item, dict):
            continue
        try:
            items.append(VisionExtractItem.model_validate(raw_item))
        except Exception:
            continue
    return CaptureDraftRead(
        id=draft.id or 0,
        customer_id=draft.customer_id,
        customer_name=draft.customer_name,
        company=draft.company,
        confidence=draft.confidence,
        summary=draft.summary,
        items=items,
        suggested_notes=draft.suggested_notes,
        fallback_used=draft.fallback_used,
        source=draft.source,
        raw_text_excerpt=draft.raw_text_excerpt,
        status=draft.status,
        submitted_order_id=draft.submitted_order_id,
        filename=draft.filename,
        content_type=draft.content_type,
        created_by=draft.created_by,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


def serialize_user_preference(preference: UserPreference | None, namespace: str) -> UserPreferenceRead:
    if not preference:
        return UserPreferenceRead(namespace=namespace, value={})
    return UserPreferenceRead(
        id=preference.id,
        namespace=preference.namespace,
        value=decode_preference_value(preference.value_json),
        updated_at=preference.updated_at,
    )


def serialize_copilot_recommendation(recommendation: CopilotRecommendation) -> CopilotRecommendationRead:
    return CopilotRecommendationRead(
        id=recommendation.id or 0,
        source=recommendation.source,
        lead_id=recommendation.lead_id,
        lead_title=recommendation.lead_title,
        customer_name=recommendation.customer_name,
        owner=recommendation.owner,
        region=recommendation.region,
        stage=recommendation.stage,
        grade=recommendation.grade,
        rule_score=recommendation.rule_score,
        win_rate=recommendation.win_rate,
        expected_amount=recommendation.expected_amount,
        next_best_action=recommendation.next_best_action,
        score_reasons=decode_score_reasons(recommendation.score_reasons_json),
        llm_summary=recommendation.llm_summary,
        message_draft=recommendation.message_draft,
        fallback_used=recommendation.fallback_used,
        model=recommendation.model,
        feedback_status=recommendation.feedback_status,
        feedback_rating=recommendation.feedback_rating,
        feedback_note=recommendation.feedback_note,
        feedback_by=recommendation.feedback_by,
        feedback_at=recommendation.feedback_at,
        created_at=recommendation.created_at,
    )


def has_recent_copilot_summary_recommendation(session: Session, insight, organization_id: int) -> bool:
    if not insight.id:
        return False
    cutoff = datetime.utcnow() - COPILOT_SUMMARY_DEDUPE_WINDOW
    existing = session.exec(
        select(CopilotRecommendation).where(
            CopilotRecommendation.source == "summary",
            CopilotRecommendation.organization_id == organization_id,
            CopilotRecommendation.lead_id == insight.id,
            CopilotRecommendation.owner == insight.owner,
            CopilotRecommendation.created_at >= cutoff,
        )
    ).first()
    return existing is not None


def add_copilot_summary_history(session: Session, result: CopilotSummaryResponse, organization_id: int) -> None:
    for insight in result.insights[:5]:
        if has_recent_copilot_summary_recommendation(session, insight, organization_id):
            continue
        session.add(
            CopilotRecommendation(
                organization_id=organization_id,
                source="summary",
                lead_id=insight.id,
                lead_title=summarize_text(insight.title, limit=180),
                customer_name=summarize_text(insight.customer_name, limit=180),
                owner=insight.owner,
                region=insight.region,
                stage=normalize_stage_value(insight.stage),
                grade=insight.grade,
                rule_score=insight.rule_score,
                win_rate=insight.win_rate,
                expected_amount=insight.expected_amount,
                next_best_action=summarize_text(insight.next_best_action, limit=360),
                score_reasons_json=encode_score_reasons(insight.score_reasons),
                llm_summary=summarize_text(result.llm_summary, limit=600),
                fallback_used=result.fallback_used,
                model=settings.llm_model,
            )
        )


def add_copilot_follow_up_history(
    session: Session,
    payload: CopilotFollowUpRequest,
    result: CopilotFollowUpResponse,
    lead: SalesLead | None,
    organization_id: int,
) -> None:
    lead_title = lead.title if lead else payload.opportunity_title
    customer_name = lead.customer_name if lead else payload.customer_name
    stage = normalize_stage_value(lead.stage if lead else payload.stage)
    expected_amount = lead.expected_amount if lead else payload.expected_amount
    score_reasons = [
        "匹配已有商机上下文生成跟进话术。" if lead else "根据手动输入的客户与商机上下文生成跟进话术。",
        f"当前评分 {result.rule_score} 分，建议动作：{result.next_best_action}",
    ]
    session.add(
        CopilotRecommendation(
            organization_id=organization_id,
            source="follow_up",
            lead_id=lead.id if lead else payload.lead_id,
            lead_title=summarize_text(lead_title, limit=180),
            customer_name=summarize_text(customer_name, limit=180),
            owner=lead.owner if lead else "",
            region=lead.region if lead else "",
            stage=stage,
            grade=result.grade,
            rule_score=result.rule_score,
            win_rate=max(0, min(result.rule_score / 100, 1)),
            expected_amount=expected_amount,
            next_best_action=summarize_text(result.next_best_action, limit=360),
            score_reasons_json=encode_score_reasons(score_reasons),
            llm_summary=summarize_text(result.llm_summary, limit=600),
            message_draft=summarize_text(result.message_draft, limit=900),
            fallback_used=result.fallback_used,
            model=settings.llm_model,
        )
    )


def build_copilot_task(recommendation: CopilotRecommendation) -> TaskItem:
    title_subject = recommendation.lead_title or recommendation.customer_name or "未命名商机"
    title = summarize_text(f"跟进 {recommendation.customer_name or title_subject}：{title_subject}", limit=120)
    reasons = "；".join(decode_score_reasons(recommendation.score_reasons_json))
    message = recommendation.message_draft or recommendation.llm_summary
    description_parts = [
        f"来源：CopilotRecommendation#{recommendation.id}",
        f"客户：{recommendation.customer_name or '未记录'}",
        f"商机：{recommendation.lead_title or '未关联商机'}",
        f"建议动作：{recommendation.next_best_action or '待销售确认下一步动作'}",
    ]
    if message:
        description_parts.append(f"话术/摘要：{message}")
    if reasons:
        description_parts.append(f"评分原因：{reasons}")

    grade = recommendation.grade.upper()
    priority = "hot" if grade in {"A", "B"} else "warm" if grade == "C" else "cold"
    status = "today" if grade == "A" else "week"
    status_label = "今天" if status == "today" else "本周"
    due_date = "今天 18:00" if grade == "A" else "明天 18:00" if grade == "B" else "本周五 18:00"
    return TaskItem(
        organization_id=recommendation.organization_id,
        title=title,
        description=summarize_text("\n".join(description_parts), limit=900),
        owner=recommendation.owner or "李伟超",
        due_date=due_date,
        priority=priority,
        status=status,
        status_label=status_label,
    )


def find_task_for_copilot_recommendation(session: Session, recommendation_id: int, organization_id: int | None = None) -> TaskItem | None:
    marker = f"CopilotRecommendation#{recommendation_id}"
    tasks = session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()
    if organization_id is not None:
        tasks = [task for task in tasks if task.organization_id == organization_id]
    return next((task for task in tasks if marker in task.description), None)


def build_customer_activity_task(activity: CustomerActivity) -> TaskItem:
    subject = activity.next_action or activity.subject or "确认客户下一步动作"
    title = summarize_text(f"跟进 {activity.customer_name}：{subject}", limit=120)
    description_parts = [
        f"来源：CustomerActivity#{activity.id}",
        f"客户：{activity.customer_name}",
        f"互动：{activity.subject}",
        f"互动摘要：{activity.summary}",
        f"结果：{activity.outcome or '待补充'}",
        f"建议动作：{activity.next_action or '待销售确认下一步动作'}",
    ]

    sentiment = (activity.sentiment or "").lower()
    if sentiment in {"risk", "negative"}:
        priority = "hot"
        status = "today"
        status_label = "今天"
        due_date = "今天 18:00"
    elif sentiment == "positive":
        priority = "warm"
        status = "week"
        status_label = "本周"
        due_date = "明天 18:00"
    else:
        priority = "cold"
        status = "week"
        status_label = "本周"
        due_date = "本周五 18:00"

    return TaskItem(
        organization_id=activity.organization_id,
        title=title,
        description=summarize_text("\n".join(description_parts), limit=900),
        owner=activity.owner,
        due_date=due_date,
        priority=priority,
        status=status,
        status_label=status_label,
    )


def find_task_for_customer_activity(session: Session, activity_id: int, organization_id: int | None = None) -> TaskItem | None:
    marker = f"CustomerActivity#{activity_id}"
    tasks = session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()
    if organization_id is not None:
        tasks = [task for task in tasks if task.organization_id == organization_id]
    return next((task for task in tasks if marker in task.description), None)


def make_notification(
    *,
    notification_id: str,
    category: str,
    severity: str,
    title: str,
    message: str,
    href: str,
    action_label: str,
    entity_type: str,
    entity_id: int | None,
    created_at: datetime,
) -> NotificationRead:
    return NotificationRead(
        id=notification_id,
        category=category,
        severity=severity,
        title=summarize_text(title, limit=120),
        message=summarize_text(message, limit=260),
        href=href,
        action_label=action_label,
        entity_type=entity_type,
        entity_id=entity_id,
        created_at=created_at,
    )


def collect_notifications(session: Session, current_user: AuthUser, limit: int | None = 20) -> list[NotificationRead]:
    notifications: list[NotificationRead] = []
    today = date.today()

    tasks = session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()
    tasks = filter_by_organization_scope(tasks, current_user)
    tasks = filter_by_owner_scope(tasks, current_user)
    for task in tasks:
        if task.status == "overdue":
            notifications.append(
                make_notification(
                    notification_id=f"task-overdue-{task.id}",
                    category="任务",
                    severity="critical",
                    title=f"逾期任务：{task.title}",
                    message=f"{task.owner} 负责，原计划 {task.due_date} 完成。",
                    href="/tasks",
                    action_label="查看任务",
                    entity_type="task",
                    entity_id=task.id,
                    created_at=task.created_at,
                )
            )
        elif task.status == "today" and task.priority in {"hot", "warm"}:
            notifications.append(
                make_notification(
                    notification_id=f"task-today-{task.id}",
                    category="任务",
                    severity="warning" if task.priority == "hot" else "info",
                    title=f"今日待办：{task.title}",
                    message=f"{task.owner} 负责，截止 {task.due_date}。",
                    href="/tasks",
                    action_label="查看任务",
                    entity_type="task",
                    entity_id=task.id,
                    created_at=task.created_at,
                )
            )

    for alert in list_restock_alerts(session, current_user.organization_id)[:5]:
        notifications.append(
            make_notification(
                notification_id=f"stock-{alert.product_id}",
                category="库存",
                severity="critical" if alert.priority == "critical" else "warning",
                title=f"库存预警：{alert.name}",
                message=f"当前库存 {alert.current_stock} 件，建议补货 {alert.recommended_restock} 件。",
                href="/orders",
                action_label="处理补货",
                entity_type="product",
                entity_id=alert.product_id,
                created_at=datetime.utcnow(),
            )
        )

    approvals = session.exec(
        select(OrderApprovalRequest)
        .where(OrderApprovalRequest.status == OrderApprovalStatus.pending)
        .order_by(OrderApprovalRequest.created_at.desc())
    ).all()
    approvals = filter_by_organization_scope(approvals, current_user)
    approvals = filter_by_owner_scope(approvals, current_user)[:6]
    for approval in approvals:
        risk_level = normalize_order_approval_risk_level(approval.risk_level)
        risk_label = ORDER_APPROVAL_RISK_LABELS[risk_level]
        sla_status, sla_hours_remaining = get_order_approval_sla_details(approval)
        if sla_status == "overdue":
            severity = "critical"
            sla_message = f"SLA 已逾期 {abs(sla_hours_remaining or 0)} 小时"
        elif risk_level == "critical":
            severity = "critical"
            sla_message = f"SLA 剩余 {sla_hours_remaining} 小时" if sla_hours_remaining is not None else "SLA 待补充"
        elif risk_level == "high" or sla_status == "due_soon":
            severity = "warning"
            sla_message = f"SLA 剩余 {sla_hours_remaining} 小时" if sla_hours_remaining is not None else "SLA 待补充"
        else:
            severity = "warning" if approval.requested_total >= 100000 else "info"
            sla_message = f"SLA 剩余 {sla_hours_remaining} 小时" if sla_hours_remaining is not None else "SLA 待补充"
        notifications.append(
            make_notification(
                notification_id=f"order-approval-{approval.id}",
                category="审批",
                severity=severity,
                title=f"订单审批：#{approval.order_id}（{risk_label}风险）",
                message=f"{approval.owner} 提交，金额 {approval.requested_total:.0f} 元，{sla_message}，待 {approval.reviewer or '销售经理'} 处理。",
                href="/orders",
                action_label="查看审批",
                entity_type="order_approval",
                entity_id=approval.id,
                created_at=approval.sla_due_at if sla_status == "overdue" and approval.sla_due_at else approval.created_at,
            )
        )

    leads = session.exec(select(SalesLead).order_by(SalesLead.due_date.asc(), SalesLead.expected_amount.desc())).all()
    leads = filter_by_organization_scope(leads, current_user)
    leads = filter_by_owner_scope(leads, current_user)
    for lead in leads:
        stage = normalize_stage_value(lead.stage)
        if stage in {"won", "lost"}:
            continue
        days_left = (lead.due_date - today).days
        if lead.expected_amount < 100000 and days_left > 3:
            continue
        severity = "critical" if days_left < 0 else "warning" if days_left <= 2 else "info"
        notifications.append(
            make_notification(
                notification_id=f"lead-{lead.id}",
                category="商机",
                severity=severity,
                title=f"重点商机：{lead.title}",
                message=f"{lead.customer_name} / {stage} / {lead.expected_amount:.0f} 元，预计 {lead.due_date} 截止。",
                href="/opportunities",
                action_label="查看商机",
                entity_type="lead",
                entity_id=lead.id,
                created_at=datetime.combine(lead.due_date, datetime.min.time()),
            )
        )

    recommendations = session.exec(select(CopilotRecommendation).order_by(CopilotRecommendation.created_at.desc())).all()
    recommendations = filter_by_organization_scope(recommendations, current_user)
    recommendations = filter_by_owner_scope(recommendations, current_user)[:8]
    for recommendation in recommendations:
        if recommendation.id and find_task_for_copilot_recommendation(session, recommendation.id, current_user.organization_id):
            continue
        notifications.append(
            make_notification(
                notification_id=f"copilot-{recommendation.id}",
                category="AI",
                severity="info" if recommendation.grade not in {"A", "B"} else "warning",
                title=f"Copilot 建议待执行：{recommendation.lead_title or recommendation.customer_name}",
                message=recommendation.next_best_action or recommendation.llm_summary or "请查看 AI 副驾推荐历史。",
                href="/copilot",
                action_label="转为任务",
                entity_type="copilot_recommendation",
                entity_id=recommendation.id,
                created_at=recommendation.created_at,
            )
        )

    fallback_logs = session.exec(
        select(AIInteractionLog)
        .where(AIInteractionLog.fallback_used == True, AIInteractionLog.organization_id == current_user.organization_id)  # noqa: E712
        .order_by(AIInteractionLog.created_at.desc())
        .limit(3)
    ).all()
    for log in fallback_logs:
        notifications.append(
            make_notification(
                notification_id=f"ai-fallback-{log.id}",
                category="AI",
                severity="warning",
                title=f"AI 兜底调用：{log.operation}",
                message=f"模型 {log.model or '未配置'} 使用兜底结果，耗时 {log.latency_ms} ms。",
                href="/ai-audit",
                action_label="查看审计",
                entity_type="ai_interaction",
                entity_id=log.id,
                created_at=log.created_at,
            )
        )

    severity_rank = {"critical": 0, "warning": 1, "info": 2}
    notifications.sort(key=lambda item: (severity_rank.get(item.severity, 9), -item.created_at.timestamp(), item.id))
    if limit is None:
        return notifications
    return notifications[: max(1, min(limit, 50))]


def get_notification_state_map(session: Session, current_user: AuthUser) -> dict[str, NotificationState]:
    states = session.exec(
        select(NotificationState).where(
            NotificationState.user_id == current_user.id,
            NotificationState.organization_id == current_user.organization_id,
        )
    ).all()
    return {state.notification_id: state for state in states}


def apply_notification_states(
    notifications: list[NotificationRead],
    states: dict[str, NotificationState],
    *,
    include_dismissed: bool = False,
    unread_only: bool = False,
) -> list[NotificationRead]:
    enriched: list[NotificationRead] = []
    for notification in notifications:
        state = states.get(notification.id)
        is_read = state.status == "read" if state else False
        dismissed = state.status == "dismissed" if state else False
        if dismissed and not include_dismissed:
            continue
        if unread_only and (is_read or dismissed):
            continue
        enriched.append(
            notification.model_copy(
                update={
                    "is_read": is_read,
                    "dismissed": dismissed,
                    "state_updated_at": state.updated_at if state else None,
                }
            )
        )
    return enriched


def get_or_create_notification_state(session: Session, current_user: AuthUser, notification_id: str) -> NotificationState:
    state = session.exec(
        select(NotificationState).where(
            NotificationState.user_id == current_user.id,
            NotificationState.organization_id == current_user.organization_id,
            NotificationState.notification_id == notification_id,
        )
    ).first()
    if state:
        return state
    state = NotificationState(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        notification_id=notification_id,
    )
    session.add(state)
    session.flush()
    return state


def update_notification_state_record(state: NotificationState, action: str) -> NotificationState:
    now = datetime.utcnow()
    if action == "read":
        state.status = "read"
        state.read_at = state.read_at or now
        state.dismissed_at = None
    elif action == "unread":
        state.status = "unread"
        state.read_at = None
        state.dismissed_at = None
    elif action == "dismiss":
        state.status = "dismissed"
        state.read_at = state.read_at or now
        state.dismissed_at = now
    state.updated_at = now
    return state


def serialize_notification_state(state: NotificationState) -> NotificationStateResponse:
    return NotificationStateResponse(
        notification_id=state.notification_id,
        status=state.status,
        is_read=state.status == "read",
        dismissed=state.status == "dismissed",
        read_at=state.read_at,
        dismissed_at=state.dismissed_at,
        updated_at=state.updated_at,
    )


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
    organization_id: int | None = None,
) -> None:
    if organization_id is None:
        operator_user = session.exec(select(AuthUser).where(AuthUser.full_name == operator)).first()
        organization_id = operator_user.organization_id if operator_user else 1
    session.add(
        BusinessAuditLog(
            organization_id=organization_id,
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


def customer_aliases(customer: Customer) -> set[str]:
    return {value for value in {customer.company, customer.name, customer.contact_person} if value}


def clamp_int(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return round(max(minimum, min(maximum, value)))


def customer_health_level(score: int) -> str:
    if score >= 80:
        return "strong"
    if score >= 65:
        return "stable"
    if score >= 45:
        return "watch"
    return "risk"


def build_customer_health_profile(
    customer: Customer,
    contacts: list[Contact],
    activities: list[CustomerActivity],
    leads: list[SalesLead],
    orders: list[SalesOrder],
    cases: list[SupportCase],
    recommendations: list[CopilotRecommendation],
    tasks: list[TaskItem],
) -> CustomerHealthProfile:
    now = datetime.utcnow()
    recent_since = now - timedelta(days=30)
    open_leads = [lead for lead in leads if lead.stage not in {LeadStage.won, LeadStage.lost}]
    won_leads = [lead for lead in leads if lead.stage == LeadStage.won]
    active_cases = [support_case for support_case in cases if support_case.status not in {"resolved", "closed"}]
    hot_cases = [support_case for support_case in active_cases if support_case.priority == "hot"]
    recent_activities = [activity for activity in activities if activity.occurred_at >= recent_since]
    positive_activities = [activity for activity in recent_activities if activity.sentiment == "positive"]
    risk_activities = [activity for activity in recent_activities if activity.sentiment in {"risk", "negative"}]
    overdue_tasks = [task for task in tasks if task.status == "overdue"]
    pending_tasks = [task for task in tasks if task.status not in {"completed", "cancelled"}]
    total_revenue = sum(order.total_amount for order in orders)
    pipeline_amount = sum(lead.expected_amount for lead in open_leads)

    latest_touch: datetime | None = None
    touch_points = [activity.occurred_at for activity in activities]
    touch_points.extend(datetime.combine(order.order_date, datetime.min.time()) for order in orders)
    if touch_points:
        latest_touch = max(touch_points)
    days_since_touch = (now - latest_touch).days if latest_touch else 999

    revenue_score = clamp_int(total_revenue / 180000 * 100) if total_revenue else 28
    pipeline_score = clamp_int(35 + min(pipeline_amount / 120000 * 55, 55) + min(len(open_leads) * 5, 10)) if open_leads else (45 if won_leads else 22)
    relationship_score = clamp_int(
        min(len(contacts) * 22, 58)
        + min(len(recent_activities) * 7, 24)
        + min(len(positive_activities) * 8, 18)
        - len(risk_activities) * 12
    )
    service_score = clamp_int(92 - len(active_cases) * 18 - len(hot_cases) * 12 - len(overdue_tasks) * 10)
    if days_since_touch <= 7:
        engagement_base = 92
    elif days_since_touch <= 30:
        engagement_base = 78
    elif days_since_touch <= 60:
        engagement_base = 58
    else:
        engagement_base = 35
    engagement_score = clamp_int(engagement_base + min(len(pending_tasks) * 3, 9) - len(overdue_tasks) * 12)
    if recommendations:
        average_recommendation_score = sum(item.rule_score for item in recommendations) / len(recommendations)
        positive_feedback = len([item for item in recommendations if item.feedback_status in {"accepted", "helpful"}])
        ai_execution_score = clamp_int(average_recommendation_score + positive_feedback * 5 - len([item for item in recommendations if item.feedback_status == "dismissed"]) * 8)
    else:
        ai_execution_score = 55

    factors = [
        CustomerHealthFactor(key="revenue", label="收入贡献", score=revenue_score, weight=0.20, level=customer_health_level(revenue_score), detail=f"累计订单 {len(orders)} 张，收入 {total_revenue:.0f} 元。"),
        CustomerHealthFactor(key="pipeline", label="增长管道", score=pipeline_score, weight=0.20, level=customer_health_level(pipeline_score), detail=f"在管商机 {len(open_leads)} 个，预计金额 {pipeline_amount:.0f} 元。"),
        CustomerHealthFactor(key="relationship", label="关系覆盖", score=relationship_score, weight=0.18, level=customer_health_level(relationship_score), detail=f"联系人 {len(contacts)} 位，近30天互动 {len(recent_activities)} 条。"),
        CustomerHealthFactor(key="service", label="服务风险", score=service_score, weight=0.18, level=customer_health_level(service_score), detail=f"未关闭工单 {len(active_cases)} 条，逾期任务 {len(overdue_tasks)} 条。"),
        CustomerHealthFactor(key="engagement", label="跟进活跃", score=engagement_score, weight=0.14, level=customer_health_level(engagement_score), detail=f"最近触达距今 {days_since_touch if latest_touch else '无'} 天，待办任务 {len(pending_tasks)} 条。"),
        CustomerHealthFactor(key="ai_execution", label="AI 建议落地", score=ai_execution_score, weight=0.10, level=customer_health_level(ai_execution_score), detail=f"沉淀 Copilot 推荐 {len(recommendations)} 条。"),
    ]
    score = clamp_int(sum(factor.score * factor.weight for factor in factors))

    if score >= 85:
        grade, grade_label = "excellent", "高价值稳健客户"
    elif score >= 70:
        grade, grade_label = "healthy", "健康增长客户"
    elif score >= 55:
        grade, grade_label = "watch", "需关注客户"
    else:
        grade, grade_label = "risk", "流失高风险客户"

    trend_signal = len(positive_activities) * 2 + len(open_leads) + len(won_leads) - len(risk_activities) * 2 - len(active_cases) - len(overdue_tasks)
    trend = "up" if trend_signal >= 3 else "down" if trend_signal <= -2 else "stable"
    churn_probability = round(max(0.05, min(0.95, (100 - score) / 100 * 0.72 + len(risk_activities) * 0.04 + len(hot_cases) * 0.05 + (0.08 if not open_leads else 0))), 2)

    risk_flags: list[str] = []
    if active_cases:
        risk_flags.append(f"{len(active_cases)} 个未关闭工单可能影响续约或增购。")
    if risk_activities:
        risk_flags.append(f"近30天出现 {len(risk_activities)} 条风险/负向互动。")
    if not open_leads:
        risk_flags.append("当前缺少在管商机，增长路径不足。")
    if len(contacts) < 2:
        risk_flags.append("关键联系人覆盖不足，单点关系风险较高。")
    if overdue_tasks:
        risk_flags.append(f"{len(overdue_tasks)} 个关联任务已逾期。")
    if not risk_flags:
        risk_flags.append("暂无明显流失信号，重点维持跟进节奏。")

    strengths: list[str] = []
    if total_revenue > 0:
        strengths.append(f"已有 {total_revenue:.0f} 元真实订单收入，可做复购经营。")
    if open_leads:
        strengths.append(f"存在 {len(open_leads)} 个在管商机，具备继续扩展空间。")
    if positive_activities:
        strengths.append(f"近30天有 {len(positive_activities)} 条正向互动信号。")
    if recommendations:
        strengths.append("已有 Copilot 推荐沉淀，可继续转任务和收集反馈。")
    if not strengths:
        strengths.append("客户档案已入库，可从联系人补全和首个商机创建开始经营。")

    actions: list[CustomerHealthAction] = []
    if active_cases:
        first_case = active_cases[0]
        actions.append(CustomerHealthAction(title=f"先处理服务阻塞：{first_case.title}", detail="关闭高优先级工单后再推进商务沟通，降低成交阻力。", priority="hot" if first_case.priority == "hot" else "warm", source="support_case"))
    if risk_activities:
        first_activity = risk_activities[0]
        actions.append(CustomerHealthAction(title=f"复盘风险互动：{first_activity.subject}", detail=first_activity.next_action or first_activity.summary, priority="hot", source="customer_activity"))
    if open_leads:
        top_lead = max(open_leads, key=lambda item: item.expected_amount)
        actions.append(CustomerHealthAction(title=f"推进商机：{top_lead.title}", detail=top_lead.next_action or "确认预算、决策人和下一步时间点。", priority="warm", source="sales_lead"))
    if overdue_tasks:
        first_task = overdue_tasks[0]
        actions.append(CustomerHealthAction(title=f"补救逾期任务：{first_task.title}", detail=first_task.description, priority="hot", source="task"))
    if len(contacts) < 2:
        actions.append(CustomerHealthAction(title="补齐多联系人关系", detail="至少沉淀采购、业务、技术三个角色，降低单点沟通风险。", priority="warm", source="contact"))
    for recommendation in recommendations:
        if recommendation.next_best_action and len(actions) < 5:
            actions.append(CustomerHealthAction(title="执行 Copilot 建议", detail=recommendation.next_best_action, priority="warm", source=f"copilot_recommendation:{recommendation.id}"))
            break
    if not actions:
        actions.append(CustomerHealthAction(title="安排月度客户复盘", detail="确认业务目标、使用反馈和下一阶段增购机会。", priority="cold", source="account_plan"))

    evidence_summary = (
        f"基于 {len(contacts)} 位联系人、{len(recent_activities)} 条近30天互动、{len(open_leads)} 个在管商机、"
        f"{len(orders)} 张订单、{len(active_cases)} 个未关闭工单和 {len(recommendations)} 条 Copilot 推荐实时计算。"
    )

    return CustomerHealthProfile(
        score=score,
        grade=grade,
        grade_label=grade_label,
        trend=trend,
        churn_probability=churn_probability,
        evidence_summary=evidence_summary,
        factors=factors,
        risk_flags=risk_flags[:5],
        strengths=strengths[:5],
        recommended_actions=actions[:5],
    )


def build_customer_workspace_metrics(
    contacts: list[Contact],
    leads: list[SalesLead],
    orders: list[SalesOrder],
    cases: list[SupportCase],
    health_score: int | None = None,
) -> list[DashboardMetric]:
    open_leads = [lead for lead in leads if lead.stage not in {LeadStage.won, LeadStage.lost}]
    active_cases = [support_case for support_case in cases if support_case.status not in {"resolved", "closed"}]
    total_revenue = sum(order.total_amount for order in orders)
    pipeline_amount = sum(lead.expected_amount for lead in open_leads)
    if health_score is None:
        health_score = clamp_int(50 + min(total_revenue / 50000, 20) + min(pipeline_amount / 50000, 20) + min(len(contacts) * 3, 12) - len(active_cases) * 8)

    return [
        DashboardMetric(label="客户健康分", value=str(health_score), hint="由收入、管道、联系人和服务风险综合计算"),
        DashboardMetric(label="累计收入", value=f"{total_revenue:.0f}", hint=f"{len(orders)} 张订单"),
        DashboardMetric(label="在管商机", value=f"{pipeline_amount:.0f}", hint=f"{len(open_leads)} 个未关闭机会"),
        DashboardMetric(label="服务风险", value=str(len(active_cases)), hint="未关闭工单数量"),
    ]


def build_customer_timeline(
    customer: Customer,
    activities: list[CustomerActivity],
    leads: list[SalesLead],
    orders: list[SalesOrder],
    cases: list[SupportCase],
    recommendations: list[CopilotRecommendation],
) -> list[CustomerTimelineItem]:
    items: list[CustomerTimelineItem] = [
        CustomerTimelineItem(
            id=f"customer-{customer.id}",
            category="客户",
            title=f"客户档案创建：{customer.company}",
            description=f"行业 {customer.industry}，等级 {customer.level}，负责人 {customer.owner}。",
            timestamp=customer.created_at,
            href="/accounts",
            severity="info",
        )
    ]

    sentiment_tone = {"positive": "success", "risk": "danger", "negative": "danger", "neutral": "info"}
    for activity in activities:
        items.append(
            CustomerTimelineItem(
                id=f"activity-{activity.id}",
                category="互动",
                title=activity.subject,
                description=f"{activity.outcome or activity.summary} 下一步：{activity.next_action or '待跟进'}",
                timestamp=activity.occurred_at,
                href=f"/accounts/{customer.id}",
                severity=sentiment_tone.get(activity.sentiment, "info"),
            )
        )

    for order in orders:
        tone = "success" if order.status.value in {"confirmed", "fulfilled"} else "warning"
        items.append(
            CustomerTimelineItem(
                id=f"order-{order.id}",
                category="订单",
                title=f"订单 #{order.id} {order.status.value}",
                description=f"{'AI 创建' if order.created_by_ai else '人工创建'}，金额 {order.total_amount:.0f} 元，交付日 {order.due_date.isoformat()}。",
                timestamp=order.created_at,
                href="/orders",
                severity=tone,
            )
        )

    for lead in leads:
        tone = "success" if lead.stage == LeadStage.won else "danger" if lead.stage == LeadStage.lost else "info"
        items.append(
            CustomerTimelineItem(
                id=f"lead-{lead.id}",
                category="商机",
                title=lead.title,
                description=f"阶段 {lead.stage.value}，金额 {lead.expected_amount:.0f} 元，下一步：{lead.next_action}",
                timestamp=lead.created_at,
                href="/opportunities",
                severity=tone,
            )
        )

    for support_case in cases:
        tone = "danger" if support_case.priority == "hot" else "warning" if support_case.status not in {"resolved", "closed"} else "success"
        items.append(
            CustomerTimelineItem(
                id=f"case-{support_case.id}",
                category="工单",
                title=support_case.title,
                description=f"{support_case.status_label}，优先级 {support_case.priority}，截止 {support_case.due_date.isoformat()}。",
                timestamp=support_case.created_at,
                href="/cases",
                severity=tone,
            )
        )

    for recommendation in recommendations[:6]:
        items.append(
            CustomerTimelineItem(
                id=f"recommendation-{recommendation.id}",
                category="AI 建议",
                title=recommendation.lead_title or recommendation.customer_name,
                description=recommendation.next_best_action or recommendation.llm_summary or "Copilot 已生成客户经营建议。",
                timestamp=recommendation.created_at,
                href="/copilot",
                severity="warning" if recommendation.grade in {"A", "B"} else "info",
            )
        )

    return sorted(items, key=lambda item: item.timestamp, reverse=True)[:16]


def normalize_order_status(value: OrderStatus | str) -> OrderStatus:
    return value if isinstance(value, OrderStatus) else OrderStatus(value)


def count_order_items(order: SalesOrder, session: Session | None = None) -> int:
    if session is None or order.id is None:
        return 0
    return len(session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all())


def build_order_approval_policy_reasons(
    order: SalesOrder,
    session: Session | None = None,
    target_order_status: OrderStatus | str | None = None,
) -> list[str]:
    target_status = normalize_order_status(target_order_status or order.status)
    reasons: list[str] = []
    if target_status not in ORDER_APPROVAL_REQUIRED_STATUSES:
        return reasons

    if order.total_amount >= ORDER_APPROVAL_AMOUNT_THRESHOLD:
        reasons.append(f"高价值订单 {order.total_amount:.0f} 元达到经理复核阈值")
    if order.created_by_ai and order.ai_confidence_score < ORDER_APPROVAL_AI_CONFIDENCE_THRESHOLD:
        reasons.append(f"AI 录单置信度 {order.ai_confidence_score:.0%}，需要人工核对客户、商品和数量")
    delivery_window_days = (order.due_date - order.order_date).days
    if delivery_window_days <= ORDER_APPROVAL_FAST_DELIVERY_DAYS:
        reasons.append(f"交付周期 {delivery_window_days} 天，需确认库存与实施排期")
    item_count = count_order_items(order, session)
    if item_count >= ORDER_APPROVAL_ITEM_COUNT_THRESHOLD:
        reasons.append(f"订单明细达到 {item_count} 条，需复核组合报价")
    if target_status == OrderStatus.fulfilled:
        reasons.append("目标状态为已履约，需经理确认交付闭环")
    return reasons


def build_order_approval_risk_summary(
    order: SalesOrder,
    session: Session | None = None,
    target_order_status: OrderStatus | str | None = None,
) -> str:
    risk_flags: list[str] = []
    risk_flags.extend(build_order_approval_policy_reasons(order, session, target_order_status))
    if order.total_amount >= ORDER_APPROVAL_AMOUNT_THRESHOLD and not any("高价值订单" in flag for flag in risk_flags):
        risk_flags.append(f"订单金额 {order.total_amount:.0f} 元，建议经理复核商务条款")
    if order.created_by_ai:
        if not any("AI" in flag for flag in risk_flags):
            risk_flags.append("订单由 AI 智能录单生成，需要确认客户、商品和数量")
        if order.ai_confidence_score < ORDER_APPROVAL_AI_CONFIDENCE_THRESHOLD and not any("置信度" in flag for flag in risk_flags):
            risk_flags.append(f"AI 置信度 {order.ai_confidence_score:.0%}，建议人工复核原始材料")
    days_to_delivery = (order.due_date - date.today()).days
    if days_to_delivery <= ORDER_APPROVAL_FAST_DELIVERY_DAYS and not any("交付" in flag for flag in risk_flags):
        risk_flags.append(f"交付窗口 {days_to_delivery} 天，需确认库存和实施排期")
    target_status = normalize_order_status(target_order_status or order.status)
    if order.status != OrderStatus.draft or target_status != order.status:
        risk_flags.append(f"当前订单状态为 {order.status.value}，审批后将推进到 {target_status.value}")
    return "；".join(risk_flags) or "订单金额、交付周期和 AI 置信度均未触发高风险规则。"


def normalize_order_approval_risk_level(value: str | None) -> str:
    normalized = (value or "medium").strip().lower()
    return normalized if normalized in ORDER_APPROVAL_RISK_SLA_HOURS else "medium"


def evaluate_order_approval_risk_level(
    order: SalesOrder,
    session: Session | None = None,
    target_order_status: OrderStatus | str | None = None,
) -> str:
    target_status = normalize_order_status(target_order_status or order.status)
    risk_score = 0

    if order.total_amount >= ORDER_APPROVAL_AMOUNT_THRESHOLD * 3:
        risk_score += 3
    elif order.total_amount >= ORDER_APPROVAL_AMOUNT_THRESHOLD:
        risk_score += 2

    if order.created_by_ai:
        risk_score += 1
        if order.ai_confidence_score < 0.65:
            risk_score += 2
        elif order.ai_confidence_score < ORDER_APPROVAL_AI_CONFIDENCE_THRESHOLD:
            risk_score += 1

    delivery_window_days = (order.due_date - order.order_date).days
    if delivery_window_days <= 3:
        risk_score += 2
    elif delivery_window_days <= ORDER_APPROVAL_FAST_DELIVERY_DAYS:
        risk_score += 1

    item_count = count_order_items(order, session)
    if item_count >= ORDER_APPROVAL_ITEM_COUNT_THRESHOLD + 2:
        risk_score += 2
    elif item_count >= ORDER_APPROVAL_ITEM_COUNT_THRESHOLD:
        risk_score += 1

    if target_status == OrderStatus.fulfilled:
        risk_score += 2
    if order.status != OrderStatus.draft:
        risk_score += 1

    if risk_score >= 7:
        return "critical"
    if risk_score >= 4:
        return "high"
    if risk_score >= 2:
        return "medium"
    return "low"


def calculate_order_approval_sla_due_at(created_at: datetime, risk_level: str) -> datetime:
    normalized_level = normalize_order_approval_risk_level(risk_level)
    return created_at + timedelta(hours=ORDER_APPROVAL_RISK_SLA_HOURS[normalized_level])


def get_order_approval_sla_details(
    approval: OrderApprovalRequest,
    now: datetime | None = None,
) -> tuple[str, int | None]:
    if approval.status != OrderApprovalStatus.pending:
        return "closed", None
    if not approval.sla_due_at:
        return "unset", None

    current_time = now or datetime.utcnow()
    seconds_remaining = (approval.sla_due_at - current_time).total_seconds()
    if seconds_remaining < 0:
        hours_remaining = -ceil(abs(seconds_remaining) / 3600)
        return "overdue", hours_remaining

    hours_remaining = ceil(seconds_remaining / 3600)
    if hours_remaining <= 4:
        return "due_soon", hours_remaining
    return "on_track", hours_remaining


def ensure_order_status_transition_allowed(
    order: SalesOrder,
    session: Session,
    current_user: AuthUser,
    target_order_status: OrderStatus | str,
    previous_order_status: OrderStatus | str | None = None,
) -> None:
    target_status = normalize_order_status(target_order_status)
    previous_status = normalize_order_status(previous_order_status or order.status)
    if target_status == previous_status or target_status not in ORDER_APPROVAL_REQUIRED_STATUSES:
        return
    if has_permission(current_user, "approval:manage"):
        return

    policy_reasons = build_order_approval_policy_reasons(order, session, target_status)
    if not policy_reasons:
        return
    if find_pending_order_approval(session, order.id or 0):
        raise HTTPException(status_code=403, detail="订单已触发审批策略并存在待审批申请，需经理审批后推进状态")
    raise HTTPException(status_code=403, detail=f"订单触发审批策略，需提交经理审批：{'；'.join(policy_reasons)}")


def serialize_order_approval(approval: OrderApprovalRequest, session: Session) -> OrderApprovalRead:
    order = session.get(SalesOrder, approval.order_id)
    customer = session.get(Customer, order.customer_id) if order else None
    sla_status, sla_hours_remaining = get_order_approval_sla_details(approval)
    return OrderApprovalRead(
        id=approval.id or 0,
        order_id=approval.order_id,
        customer_name=customer.company if customer else "未知客户",
        owner=approval.owner,
        requester=approval.requester,
        reviewer=approval.reviewer,
        status=approval.status,
        reason=approval.reason,
        risk_summary=approval.risk_summary,
        risk_level=normalize_order_approval_risk_level(approval.risk_level),
        requested_total=approval.requested_total,
        previous_order_status=approval.previous_order_status,
        target_order_status=approval.target_order_status,
        decision_comment=approval.decision_comment,
        sla_due_at=approval.sla_due_at,
        sla_status=sla_status,
        sla_hours_remaining=sla_hours_remaining,
        decided_at=approval.decided_at,
        created_at=approval.created_at,
    )


def find_pending_order_approval(session: Session, order_id: int) -> OrderApprovalRequest | None:
    return session.exec(
        select(OrderApprovalRequest)
        .where(OrderApprovalRequest.order_id == order_id)
        .where(OrderApprovalRequest.status == OrderApprovalStatus.pending)
    ).first()


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
    products = (
        session.exec(
            select(Product).where(
                Product.id.in_(all_product_ids),
                Product.organization_id == order.organization_id,
            )
        ).all()
        if all_product_ids
        else []
    )
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
                organization_id=order.organization_id,
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


def build_auth_audit_csv(logs: list[AuthAuditLog]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日志ID", "时间", "事件", "状态", "账号", "用户ID", "组织ID", "详情"])
    for log in logs:
        writer.writerow(
            [
                log.id,
                log.created_at.isoformat(timespec="seconds"),
                log.event,
                log.status,
                log.account,
                log.user_id or "",
                log.organization_id or "",
                log.detail,
            ]
        )
    return "\ufeff" + output.getvalue()


def build_ai_audit_csv(logs: list[AIInteractionLog]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日志ID", "时间", "操作", "状态", "供应商", "模型", "是否兜底", "耗时ms", "对象类型", "对象ID", "请求摘要", "响应摘要"])
    for log in logs:
        writer.writerow(
            [
                log.id,
                log.created_at.isoformat(timespec="seconds"),
                log.operation,
                log.status,
                log.provider,
                log.model,
                "是" if log.fallback_used else "否",
                log.latency_ms,
                log.entity_type,
                log.entity_id or "",
                log.request_summary,
                log.response_summary,
            ]
        )
    return "\ufeff" + output.getvalue()


def build_business_audit_csv(logs: list[BusinessAuditLog]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日志ID", "时间", "动作", "对象类型", "对象ID", "操作人", "状态", "摘要", "详情"])
    for log in logs:
        writer.writerow(
            [
                log.id,
                log.created_at.isoformat(timespec="seconds"),
                log.action,
                log.entity_type,
                log.entity_id or "",
                log.operator,
                log.status,
                log.summary,
                log.detail,
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


def build_health_payload(session: Session) -> dict[str, object]:
    demo_data = {}
    demo_ready = True
    for label, model, target in HEALTH_DEMO_DATA_TARGETS:
        count = len(session.exec(select(model)).all())
        ready = count >= target
        demo_ready = demo_ready and ready
        demo_data[label] = {
            "count": count,
            "target": target,
            "status": "ok" if ready else "low",
        }

    consistency = build_consistency_payload(session)
    consistency_ready = consistency["issue_count"] == 0
    overall_status = "ok" if demo_ready and consistency_ready else "degraded"

    return {
        "status": overall_status,
        "database": {
            "connected": True,
            "driver": engine.url.get_backend_name(),
        },
        "llm": {
            "base_url": settings.llm_base_url,
            "model": settings.llm_model,
            "api_key_configured": bool(settings.llm_api_key),
        },
        "demo_data": demo_data,
        "consistency": {
            "status": consistency["overall_status"],
            "issue_count": consistency["issue_count"],
            "critical_count": consistency["critical_count"],
            "warning_count": consistency["warning_count"],
        },
    }


@app.get("/api/health")
def api_health(session: SessionDep) -> dict[str, object]:
    return build_health_payload(session)


@app.post("/api/auth/login", response_model=AuthSessionResponse)
def login(payload: AuthLoginRequest, session: SessionDep) -> AuthSessionResponse:
    account = normalize_account(payload.account)
    user = find_user_by_account(session, account)
    ensure_login_not_throttled(session, account, user)
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


@app.patch("/api/auth/profile", response_model=AuthMeResponse)
def update_auth_profile(
    payload: AuthProfileUpdate,
    current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)],
    session: SessionDep,
) -> AuthMeResponse:
    user, auth_session = current
    organization = session.get(Organization, user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="组织不存在")

    updates = patch_values(payload)
    if "email" in updates:
        email = normalize_account(updates["email"])
        existing = session.exec(select(AuthUser).where(AuthUser.email == email)).first()
        if existing and existing.id != user.id:
            record_auth_audit(session, event="profile_update", account=user.email, status="failed", detail="邮箱已被其他账号使用", user=user)
            session.commit()
            raise HTTPException(status_code=400, detail="邮箱已被其他账号使用")
        updates["email"] = email
    if "phone" in updates:
        updates["phone"] = updates["phone"] or ""
    if "full_name" in updates and len(updates["full_name"]) < 2:
        raise HTTPException(status_code=400, detail="姓名至少需要 2 个字符")

    apply_updates(user, updates)
    session.add(user)
    record_auth_audit(
        session,
        event="profile_update",
        account=user.email,
        status="success",
        detail=f"更新个人资料：{', '.join(sorted(updates.keys())) or '无字段变化'}",
        user=user,
    )
    session.commit()
    session.refresh(user)
    return AuthMeResponse(
        expires_at=auth_session.expires_at,
        user=serialize_auth_user(user, organization),
        organizations=[serialize_auth_organization(user, organization)],
    )


@app.post("/api/auth/password", response_model=AuthPasswordChangeResponse)
def change_auth_password(
    payload: AuthPasswordChangeRequest,
    current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)],
    session: SessionDep,
) -> AuthPasswordChangeResponse:
    user, auth_session = current
    if not verify_password(payload.current_password, user.password_hash):
        record_auth_audit(session, event="password_change", account=user.email, status="failed", detail="当前密码错误", user=user)
        session.commit()
        raise HTTPException(status_code=400, detail="当前密码错误")
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=400, detail="新密码不能与当前密码一致")

    user.password_hash = hash_password(payload.new_password)
    revoked_sessions = 0
    active_sessions = session.exec(
        select(AuthSession).where(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at == None,  # noqa: E711
            AuthSession.id != auth_session.id,
        )
    ).all()
    for other_session in active_sessions:
        other_session.revoked_at = datetime.utcnow()
        session.add(other_session)
        revoked_sessions += 1

    session.add(user)
    record_auth_audit(
        session,
        event="password_change",
        account=user.email,
        status="success",
        detail=f"修改密码并撤销其他会话 {revoked_sessions} 个",
        user=user,
    )
    session.commit()
    return AuthPasswordChangeResponse(changed=True, revoked_sessions=revoked_sessions)


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


@app.get("/api/auth/sessions", response_model=list[AuthSessionRead])
def list_auth_sessions(
    current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)],
    session: SessionDep,
) -> list[AuthSessionRead]:
    user, auth_session = current
    sessions = session.exec(
        select(AuthSession)
        .where(AuthSession.user_id == user.id)
        .order_by(AuthSession.created_at.desc())
    ).all()
    return [serialize_auth_session(item, auth_session) for item in sessions]


@app.post("/api/auth/sessions/revoke-others", response_model=AuthSessionBulkRevokeResponse)
def revoke_other_auth_sessions(
    current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)],
    session: SessionDep,
) -> AuthSessionBulkRevokeResponse:
    user, auth_session = current
    active_sessions = session.exec(
        select(AuthSession).where(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at == None,  # noqa: E711
            AuthSession.expires_at > datetime.utcnow(),
            AuthSession.id != auth_session.id,
        )
    ).all()
    for other_session in active_sessions:
        other_session.revoked_at = datetime.utcnow()
        session.add(other_session)
    record_auth_audit(
        session,
        event="session_revoke",
        account=user.email,
        status="success",
        detail=f"批量撤销其他会话 {len(active_sessions)} 个",
        user=user,
    )
    session.commit()
    return AuthSessionBulkRevokeResponse(revoked_sessions=len(active_sessions))


@app.delete("/api/auth/sessions/{session_id}", response_model=AuthSessionRead)
def revoke_auth_session(
    session_id: int,
    current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)],
    session: SessionDep,
) -> AuthSessionRead:
    user, auth_session = current
    target_session = session.get(AuthSession, session_id)
    if not target_session or target_session.user_id != user.id:
        record_auth_audit(session, event="session_revoke", account=user.email, status="failed", detail=f"会话 {session_id} 不存在或不属于当前账号", user=user)
        session.commit()
        raise HTTPException(status_code=404, detail="会话不存在")
    if target_session.id == auth_session.id:
        record_auth_audit(session, event="session_revoke", account=user.email, status="failed", detail="尝试撤销当前会话", user=user)
        session.commit()
        raise HTTPException(status_code=400, detail="当前会话请使用退出登录")
    if target_session.revoked_at is None:
        target_session.revoked_at = datetime.utcnow()
        session.add(target_session)
    record_auth_audit(session, event="session_revoke", account=user.email, status="success", detail=f"撤销会话 {target_session.id}", user=user)
    session.commit()
    session.refresh(target_session)
    return serialize_auth_session(target_session, auth_session)


@app.get("/api/preferences/{namespace}", response_model=UserPreferenceRead)
def get_user_preference(
    namespace: str,
    current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)],
    session: SessionDep,
) -> UserPreferenceRead:
    user, _ = current
    normalized_namespace = validate_preference_namespace(namespace)
    preference = session.exec(
        select(UserPreference).where(
            UserPreference.user_id == user.id,
            UserPreference.namespace == normalized_namespace,
        )
    ).first()
    return serialize_user_preference(preference, normalized_namespace)


@app.put("/api/preferences/{namespace}", response_model=UserPreferenceRead)
def update_user_preference(
    namespace: str,
    payload: UserPreferenceUpdate,
    current: Annotated[tuple[AuthUser, AuthSession], Depends(require_current_auth)],
    session: SessionDep,
) -> UserPreferenceRead:
    user, _ = current
    normalized_namespace = validate_preference_namespace(namespace)
    preference = session.exec(
        select(UserPreference).where(
            UserPreference.user_id == user.id,
            UserPreference.namespace == normalized_namespace,
        )
    ).first()
    if not preference:
        preference = UserPreference(user_id=user.id or 0, namespace=normalized_namespace)
    preference.value_json = encode_preference_value(payload.value)
    preference.updated_at = datetime.utcnow()
    session.add(preference)
    session.commit()
    session.refresh(preference)
    return serialize_user_preference(preference, normalized_namespace)


@app.get("/api/admin/permission-matrix", response_model=PermissionMatrixResponse)
def get_permission_matrix(
    current_user: Annotated[AuthUser, Depends(require_permission("permissions:read"))],
) -> PermissionMatrixResponse:
    permission_catalog = [
        PermissionCatalogItem(
            key=key,
            category=category,
            label=label,
            description=description,
        )
        for key, (category, label, description) in sorted(PERMISSION_CATALOG.items())
    ]
    roles = [
        RolePermissionRead(
            role=role,
            description=ROLE_DESCRIPTIONS.get(role, ""),
            data_scope=data_scope_for_role(role),
            permissions=permissions_for_role(role),
            granted_count=len(permissions_for_role(role)),
            all_permissions=ALL_PERMISSIONS in permissions,
        )
        for role, permissions in ROLE_PERMISSIONS.items()
    ]
    modules = [
        ModulePermissionRead(
            path=path,
            label=label,
            permission=permission,
            roles=[role for role in ROLE_PERMISSIONS if role_has_permission(role, permission)],
        )
        for path, label, permission in MODULE_PERMISSIONS
    ]
    return PermissionMatrixResponse(
        generated_at=datetime.utcnow(),
        current_role=current_user.role,
        permission_catalog=permission_catalog,
        roles=roles,
        modules=modules,
    )


@app.get("/api/admin/users", response_model=list[AuthUserRead] | PaginatedResponse[AuthUserRead])
def list_team_members(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("team:manage"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    role: str = "",
    status: str = "",
) -> list[AuthUserRead] | dict:
    organization = session.get(Organization, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="组织不存在")
    users = session.exec(select(AuthUser).where(AuthUser.organization_id == current_user.organization_id).order_by(AuthUser.created_at.desc())).all()
    users = filter_records(
        users,
        q=q,
        fields=("full_name", "email", "phone", "role", "position", "department", "location", "status"),
        role=role,
        status=status,
    )
    payload = [serialize_auth_user(user, organization) for user in users]
    return paginate_or_list(payload, page=page, per_page=per_page)


@app.post("/api/admin/users", response_model=AuthUserRead, status_code=201)
def create_team_member(
    payload: TeamMemberCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("team:manage"))],
) -> AuthUserRead:
    organization = session.get(Organization, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="组织不存在")
    email = normalize_account(payload.email)
    if "@" not in email:
        raise HTTPException(status_code=400, detail="请输入有效邮箱")
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    if session.exec(select(AuthUser).where(AuthUser.email == email)).first():
        record_auth_audit(session, event="team_create", account=email, status="failed", detail="邮箱已注册", user=current_user)
        session.commit()
        raise HTTPException(status_code=400, detail="邮箱已注册")

    role = validate_team_role(payload.role, current_user)
    status = validate_user_status(payload.status)
    user = AuthUser(
        organization_id=current_user.organization_id,
        full_name=payload.full_name.strip(),
        email=email,
        phone=normalize_account(payload.phone),
        role=role,
        position=payload.position.strip() or ROLE_DESCRIPTIONS.get(role, "团队成员"),
        department=payload.department.strip() or "客户增长中心",
        location=payload.location.strip() or "深圳 · 南山",
        status=status,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    session.flush()
    record_auth_audit(session, event="team_create", account=email, status="success", detail=f"{current_user.full_name} 创建团队成员，角色 {role}", user=user)
    session.commit()
    session.refresh(user)
    return serialize_auth_user(user, organization)


@app.patch("/api/admin/users/{user_id}", response_model=AuthUserRead)
def update_team_member(
    user_id: int,
    payload: TeamMemberUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("team:manage"))],
) -> AuthUserRead:
    organization = session.get(Organization, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="组织不存在")
    user = session.get(AuthUser, user_id)
    if not user or user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="成员不存在")
    if user.role == "管理员" and current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="只有管理员可以维护管理员账号")

    updates = patch_values(payload)
    if user.id == current_user.id and (
        ("role" in updates and updates["role"] != user.role)
        or ("status" in updates and updates["status"] != user.status)
    ):
        raise HTTPException(status_code=400, detail="不能修改自己的角色或状态")
    if "email" in updates:
        email = normalize_account(updates["email"])
        if "@" not in email:
            raise HTTPException(status_code=400, detail="请输入有效邮箱")
        existing = session.exec(select(AuthUser).where(AuthUser.email == email)).first()
        if existing and existing.id != user.id:
            raise HTTPException(status_code=400, detail="邮箱已注册")
        updates["email"] = email
    if "phone" in updates:
        updates["phone"] = normalize_account(updates["phone"])
    if "role" in updates:
        updates["role"] = validate_team_role(updates["role"], current_user)
    if "status" in updates:
        updates["status"] = validate_user_status(updates["status"])
    if "password" in updates or "confirm_password" in updates:
        password = updates.pop("password", None)
        confirm_password = updates.pop("confirm_password", None)
        if not password or password != confirm_password:
            raise HTTPException(status_code=400, detail="两次输入的密码不一致")
        updates["password_hash"] = hash_password(password)

    for field in ("full_name", "position", "department", "location"):
        if field in updates:
            updates[field] = str(updates[field] or "").strip()
    apply_updates(user, updates)
    session.add(user)
    record_auth_audit(session, event="team_update", account=user.email, status="success", detail=f"{current_user.full_name} 更新团队成员：{', '.join(sorted(updates.keys())) or '成员资料'}", user=user)
    session.commit()
    session.refresh(user)
    return serialize_auth_user(user, organization)


@app.get("/api/notifications", response_model=list[NotificationRead])
def list_notifications(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("dashboard:read"))],
    limit: int = Query(default=20, ge=1, le=50),
    include_dismissed: bool = False,
    unread_only: bool = False,
) -> list[NotificationRead]:
    notifications = collect_notifications(session, current_user=current_user, limit=None)
    states = get_notification_state_map(session, current_user)
    notifications = apply_notification_states(
        notifications,
        states,
        include_dismissed=include_dismissed,
        unread_only=unread_only,
    )
    return notifications[:limit]


@app.post("/api/notifications/read-all", response_model=NotificationBulkUpdateResponse)
def mark_all_notifications_read(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("dashboard:read"))],
) -> NotificationBulkUpdateResponse:
    notifications = collect_notifications(session, current_user=current_user, limit=None)
    states = get_notification_state_map(session, current_user)
    visible_notifications = apply_notification_states(notifications, states)
    updated_count = 0
    for notification in visible_notifications:
        if notification.is_read:
            continue
        state = get_or_create_notification_state(session, current_user, notification.id)
        update_notification_state_record(state, "read")
        session.add(state)
        updated_count += 1
    session.commit()
    return NotificationBulkUpdateResponse(updated_count=updated_count)


@app.patch("/api/notifications/{notification_id}", response_model=NotificationStateResponse)
def update_notification_state(
    notification_id: str,
    payload: NotificationStateUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("dashboard:read"))],
) -> NotificationStateResponse:
    notification_ids = {notification.id for notification in collect_notifications(session, current_user=current_user, limit=None)}
    if notification_id not in notification_ids:
        raise HTTPException(status_code=404, detail="通知不存在或无权操作")
    state = get_or_create_notification_state(session, current_user, notification_id)
    update_notification_state_record(state, payload.action)
    session.add(state)
    session.commit()
    session.refresh(state)
    return serialize_notification_state(state)


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


@app.get("/api/auth/audit-logs/export.csv", dependencies=[Depends(require_permission("audit:read"))])
def export_auth_audit_logs_csv(
    session: SessionDep,
    q: str = "",
    event: str = "",
    status: str = "",
) -> Response:
    logs = session.exec(select(AuthAuditLog).order_by(AuthAuditLog.created_at.desc())).all()
    logs = filter_records(logs, q=q, fields=("event", "account", "status", "detail"), event=event, status=status)
    return Response(
        content=build_auth_audit_csv(logs),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="smart-crm-auth-audit.csv"'},
    )


@app.get("/api/customers", response_model=list[CustomerRead] | PaginatedResponse[CustomerRead])
def list_customers(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    status: str = "",
    level: str = "",
    city: str = "",
    industry: str = "",
) -> list[Customer] | dict:
    customers = session.exec(select(Customer).order_by(Customer.created_at.desc())).all()
    customers = filter_by_organization_scope(customers, current_user)
    customers = filter_by_owner_scope(customers, current_user)
    customers = filter_records(
        customers,
        q=q,
        fields=("name", "company", "owner", "industry", "city", "contact_person", "phone", "email", "source"),
        owner=owner,
        status=status,
        level=level,
        city=city,
        industry=industry,
    )
    return paginate_or_list(customers, page=page, per_page=per_page)


@app.post("/api/customers", response_model=CustomerRead, status_code=201)
def create_customer(
    payload: CustomerCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> Customer:
    owner = normalize_payload_owner(payload.owner, current_user)
    require_payload_owner_scope(current_user, owner)
    contact_person = payload.contact_person or payload.name or payload.company
    customer = Customer(
        organization_id=current_user.organization_id,
        name=payload.name or contact_person,
        company=payload.company,
        owner=owner,
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
        operator=customer.owner,
        summary=f"新建客户 {customer.company}",
        detail=f"行业 {customer.industry}，城市 {customer.city}，等级 {customer.level}",
    )
    session.commit()
    session.refresh(customer)
    return customer


@app.patch("/api/customers/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> Customer:
    customer = session.get(Customer, customer_id)
    if not customer or not organization_matches(customer, current_user):
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)
    updates = patch_values(payload)
    if "owner" in updates:
        updates["owner"] = normalize_payload_owner(updates["owner"], current_user)
        require_payload_owner_scope(current_user, updates["owner"])
    apply_updates(customer, updates)
    if not customer.contact_person:
        customer.contact_person = customer.name or customer.company
    if not customer.name:
        customer.name = customer.contact_person or customer.company
    if not customer.owner:
        customer.owner = customer.contact_person or customer.name or customer.company
    session.add(customer)
    add_business_audit(
        session,
        action="update",
        entity_type="customer",
        entity_id=customer.id,
        operator=customer.owner,
        summary=f"更新客户 {customer.company}",
        detail=", ".join(sorted(updates.keys())) or "更新客户资料",
    )
    session.commit()
    session.refresh(customer)
    return customer


@app.delete("/api/customers/{customer_id}")
def delete_customer(
    customer_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> dict[str, bool | int | str]:
    customer = session.get(Customer, customer_id)
    if not customer or not organization_matches(customer, current_user):
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)
    order = session.exec(
        select(SalesOrder).where(
            SalesOrder.customer_id == customer_id,
            SalesOrder.organization_id == current_user.organization_id,
        )
    ).first()
    if order:
        raise HTTPException(status_code=400, detail="客户已有订单，不能直接删除")
    add_business_audit(
        session,
        action="delete",
        entity_type="customer",
        entity_id=customer_id,
        operator=customer.owner,
        summary=f"删除客户 {customer.company}",
        detail=f"客户 ID {customer_id}",
    )
    session.delete(customer)
    session.commit()
    return delete_response("customer", customer_id)


@app.get("/api/customer-activities", response_model=list[CustomerActivityRead] | PaginatedResponse[CustomerActivityRead])
def list_customer_activities(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    customer_id: int | None = None,
    owner: str = "",
    activity_type: str = "",
    sentiment: str = "",
) -> list[CustomerActivity] | dict:
    activities = session.exec(select(CustomerActivity).order_by(CustomerActivity.occurred_at.desc())).all()
    activities = filter_by_organization_scope(activities, current_user)
    activities = filter_by_owner_scope(activities, current_user)
    if customer_id is not None:
        activities = [activity for activity in activities if activity.customer_id == customer_id]
    activities = filter_records(
        activities,
        q=q,
        fields=("customer_name", "owner", "activity_type", "subject", "summary", "outcome", "next_action", "sentiment"),
        owner=owner,
        activity_type=activity_type,
        sentiment=sentiment,
    )
    return paginate_or_list(activities, page=page, per_page=per_page)


@app.post("/api/customers/{customer_id}/activities", response_model=CustomerActivityRead, status_code=201)
def create_customer_activity(
    customer_id: int,
    payload: CustomerActivityCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> CustomerActivity:
    customer = session.get(Customer, customer_id)
    if not customer or not organization_matches(customer, current_user):
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)
    owner = normalize_related_owner(payload.owner, current_user, customer.owner)
    require_payload_owner_scope(current_user, owner)
    activity = CustomerActivity(
        organization_id=current_user.organization_id,
        customer_id=customer.id or 0,
        customer_name=customer.company,
        owner=owner,
        activity_type=payload.activity_type,
        subject=payload.subject,
        summary=payload.summary,
        outcome=payload.outcome,
        next_action=payload.next_action,
        sentiment=payload.sentiment,
        occurred_at=payload.occurred_at or datetime.utcnow(),
    )
    session.add(activity)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="customer_activity",
        entity_id=activity.id,
        operator=activity.owner,
        summary=f"新增客户互动 {activity.subject}",
        detail=f"客户 {activity.customer_name}，类型 {activity.activity_type}，情绪 {activity.sentiment}",
    )
    session.commit()
    session.refresh(activity)
    return activity


@app.patch("/api/customer-activities/{activity_id}", response_model=CustomerActivityRead)
def update_customer_activity(
    activity_id: int,
    payload: CustomerActivityUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> CustomerActivity:
    activity = session.get(CustomerActivity, activity_id)
    if not activity or not organization_matches(activity, current_user):
        raise HTTPException(status_code=404, detail="客户互动不存在")
    require_owner_scope(current_user, activity.owner)
    updates = patch_values(payload)
    if "owner" in updates:
        updates["owner"] = normalize_payload_owner(updates["owner"], current_user)
        require_payload_owner_scope(current_user, updates["owner"])
    apply_updates(activity, updates)
    session.add(activity)
    add_business_audit(
        session,
        action="update",
        entity_type="customer_activity",
        entity_id=activity.id,
        operator=activity.owner,
        summary=f"更新客户互动 {activity.subject}",
        detail=", ".join(sorted(updates.keys())) or "更新互动记录",
    )
    session.commit()
    session.refresh(activity)
    return activity


@app.post("/api/customer-activities/{activity_id}/task", response_model=TaskItemRead, status_code=201)
def create_task_from_customer_activity(
    activity_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> TaskItem:
    activity = session.get(CustomerActivity, activity_id)
    if not activity or not organization_matches(activity, current_user):
        raise HTTPException(status_code=404, detail="客户互动不存在")
    require_owner_scope(current_user, activity.owner)

    existing_task = find_task_for_customer_activity(session, activity_id, current_user.organization_id)
    if existing_task:
        require_owner_scope(current_user, existing_task.owner)
        return existing_task

    task = build_customer_activity_task(activity)
    session.add(task)
    session.flush()
    add_business_audit(
        session,
        action="convert",
        entity_type="task",
        entity_id=task.id,
        operator=task.owner,
        summary=f"客户互动转任务 {task.title}",
        detail=f"来源 CustomerActivity #{activity_id}，客户 {activity.customer_name}",
    )
    session.commit()
    session.refresh(task)
    return task


@app.get("/api/customers/{customer_id}/workspace", response_model=CustomerWorkspaceResponse)
async def get_customer_workspace(
    customer_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
) -> CustomerWorkspaceResponse:
    customer = session.get(Customer, customer_id)
    if not customer or not organization_matches(customer, current_user):
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)

    aliases = customer_aliases(customer)
    contacts = [
        contact
        for contact in session.exec(select(Contact).order_by(Contact.created_at.desc())).all()
        if contact.organization_id == current_user.organization_id and contact.company in aliases
    ]
    contacts = filter_by_owner_scope(contacts, current_user)

    activities = session.exec(
        select(CustomerActivity)
        .where(CustomerActivity.customer_id == customer.id, CustomerActivity.organization_id == current_user.organization_id)
        .order_by(CustomerActivity.occurred_at.desc())
    ).all()
    activities = filter_by_owner_scope(activities, current_user)

    leads = [
        lead
        for lead in session.exec(select(SalesLead).order_by(SalesLead.created_at.desc())).all()
        if lead.organization_id == current_user.organization_id and lead.customer_name in aliases
    ]
    leads = filter_by_owner_scope(leads, current_user)

    orders = session.exec(
        select(SalesOrder)
        .where(SalesOrder.customer_id == customer.id, SalesOrder.organization_id == current_user.organization_id)
        .order_by(SalesOrder.created_at.desc())
    ).all()
    orders = filter_by_owner_scope(orders, current_user)

    cases = [
        support_case
        for support_case in session.exec(select(SupportCase).order_by(SupportCase.created_at.desc())).all()
        if support_case.organization_id == current_user.organization_id and support_case.account in aliases
    ]
    cases = filter_by_owner_scope(cases, current_user)

    recommendations = [
        recommendation
        for recommendation in session.exec(select(CopilotRecommendation).order_by(CopilotRecommendation.created_at.desc())).all()
        if recommendation.organization_id == current_user.organization_id and recommendation.customer_name in aliases
    ]
    recommendations = filter_by_owner_scope(recommendations, current_user)

    tasks = [
        task
        for task in session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()
        if task.organization_id == current_user.organization_id and any(alias in f"{task.title} {task.description}" for alias in aliases)
    ]
    tasks = filter_by_owner_scope(tasks, current_user)

    start_time = perf_counter()
    account_plan = await copilot_service.account_plan(customer, contacts, activities, leads, orders, cases, recommendations)
    save_ai_interaction(
        session,
        operation="customer_account_plan",
        model=account_plan.model,
        fallback_used=account_plan.fallback_used,
        start_time=start_time,
        request_summary=f"{customer.company} / {len(contacts)} contacts / {len(activities)} activities / {len(leads)} leads / {len(orders)} orders",
        response_summary=account_plan.summary,
        entity_type="customer",
        entity_id=customer.id,
        organization_id=current_user.organization_id,
    )
    health_profile = build_customer_health_profile(customer, contacts, activities, leads, orders, cases, recommendations, tasks)

    return CustomerWorkspaceResponse(
        customer=customer,
        metrics=build_customer_workspace_metrics(contacts, leads, orders, cases, health_profile.score),
        contacts=contacts,
        activities=activities[:10],
        leads=leads,
        orders=[serialize_order(order, session) for order in orders],
        cases=cases,
        recommendations=[serialize_copilot_recommendation(recommendation) for recommendation in recommendations[:8]],
        timeline=build_customer_timeline(customer, activities, leads, orders, cases, recommendations),
        account_plan=account_plan,
        health_profile=health_profile,
    )


@app.get("/api/products", response_model=list[ProductRead] | PaginatedResponse[ProductRead])
def list_products(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    category: str = "",
) -> list[Product] | dict:
    products = session.exec(select(Product).order_by(Product.created_at.desc())).all()
    products = filter_by_organization_scope(products, current_user)
    products = filter_records(products, q=q, fields=("name", "sku", "category"), category=category)
    return paginate_or_list(products, page=page, per_page=per_page)


@app.post("/api/products", response_model=ProductRead, status_code=201)
def create_product(
    payload: ProductCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("catalog:manage"))],
) -> Product:
    existing = session.exec(
        select(Product).where(Product.sku == payload.sku, Product.organization_id == current_user.organization_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU 已存在")
    product = Product(**payload.model_dump(), organization_id=current_user.organization_id)
    session.add(product)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="product",
        entity_id=product.id,
        operator=current_user.full_name,
        summary=f"新建商品 {product.name}",
        detail=f"SKU {product.sku}，库存 {product.stock}，单价 {product.unit_price}",
        organization_id=current_user.organization_id,
    )
    session.commit()
    session.refresh(product)
    return product


@app.patch("/api/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("catalog:manage"))],
) -> Product:
    product = session.get(Product, product_id)
    if not product or not organization_matches(product, current_user):
        raise HTTPException(status_code=404, detail="商品不存在")
    updates = patch_values(payload)
    next_sku = updates.get("sku")
    if next_sku and next_sku != product.sku:
        existing = session.exec(
            select(Product).where(Product.sku == next_sku, Product.organization_id == current_user.organization_id)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU 已存在")
    apply_updates(product, updates)
    session.add(product)
    add_business_audit(
        session,
        action="update",
        entity_type="product",
        entity_id=product.id,
        operator=current_user.full_name,
        summary=f"更新商品 {product.name}",
        detail=", ".join(sorted(updates.keys())) or "更新商品资料",
        organization_id=current_user.organization_id,
    )
    session.commit()
    session.refresh(product)
    return product


@app.delete("/api/products/{product_id}")
def delete_product(
    product_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("catalog:manage"))],
) -> dict[str, bool | int | str]:
    product = session.get(Product, product_id)
    if not product or not organization_matches(product, current_user):
        raise HTTPException(status_code=404, detail="商品不存在")
    order_item = session.exec(select(OrderItem).where(OrderItem.product_id == product_id)).first()
    movement = session.exec(
        select(InventoryMovement).where(
            InventoryMovement.product_id == product_id,
            InventoryMovement.organization_id == current_user.organization_id,
        )
    ).first()
    if order_item or movement:
        raise HTTPException(status_code=400, detail="商品已有订单或库存流水，不能直接删除")
    add_business_audit(
        session,
        action="delete",
        entity_type="product",
        entity_id=product_id,
        operator=current_user.full_name,
        summary=f"删除商品 {product.name}",
        detail=f"SKU {product.sku}",
        organization_id=current_user.organization_id,
    )
    session.delete(product)
    session.commit()
    return delete_response("product", product_id)


@app.get("/api/inventory/restock-alerts", response_model=list[InventoryRestockAlertRead])
def get_restock_alerts(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
) -> list[InventoryRestockAlertRead]:
    return list_restock_alerts(session, current_user.organization_id)


@app.get("/api/inventory/movements", response_model=list[InventoryMovementRead] | PaginatedResponse[InventoryMovementRead])
def get_inventory_movements(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
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
    raw_movements = filter_by_organization_scope(session.exec(statement).all(), current_user)
    movements = [serialize_inventory_movement(movement, session) for movement in raw_movements]
    movements = filter_records(movements, q=q, fields=("product_name", "sku", "reason", "operator", "source"), source=source)
    return paginate_or_list(movements, page=page, per_page=per_page)


@app.post("/api/products/{product_id}/restock", response_model=ProductRestockResponse)
def restock_product(
    product_id: int,
    payload: ProductRestockRequest,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("inventory:manage"))],
) -> ProductRestockResponse:
    product = session.get(Product, product_id)
    if not product or not organization_matches(product, current_user):
        raise HTTPException(status_code=404, detail="商品不存在")

    before_stock = product.stock
    product.stock += payload.quantity
    movement = InventoryMovement(
        organization_id=current_user.organization_id,
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
        organization_id=current_user.organization_id,
    )
    session.commit()
    session.refresh(product)
    session.refresh(movement)
    return ProductRestockResponse(
        product=product,
        movement=serialize_inventory_movement(movement, session),
        alert=build_restock_alert(product, session),
    )


@app.get("/api/contacts", response_model=list[ContactRead] | PaginatedResponse[ContactRead])
def list_contacts(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    status: str = "",
) -> list[Contact] | dict:
    contacts = session.exec(select(Contact).order_by(Contact.created_at.desc())).all()
    contacts = filter_by_organization_scope(contacts, current_user)
    contacts = filter_by_owner_scope(contacts, current_user)
    contacts = filter_records(
        contacts,
        q=q,
        fields=("name", "company", "role", "email", "phone", "owner"),
        owner=owner,
        status=status,
    )
    return paginate_or_list(contacts, page=page, per_page=per_page)


@app.post("/api/contacts", response_model=ContactRead, status_code=201)
def create_contact(
    payload: ContactCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> Contact:
    owner = normalize_payload_owner(payload.owner, current_user)
    require_payload_owner_scope(current_user, owner)
    contact = Contact(**{**payload.model_dump(), "owner": owner, "organization_id": current_user.organization_id})
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


@app.patch("/api/contacts/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> Contact:
    contact = session.get(Contact, contact_id)
    if not contact or not organization_matches(contact, current_user):
        raise HTTPException(status_code=404, detail="联系人不存在")
    require_owner_scope(current_user, contact.owner)
    updates = patch_values(payload)
    if "owner" in updates:
        updates["owner"] = normalize_payload_owner(updates["owner"], current_user)
        require_payload_owner_scope(current_user, updates["owner"])
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


@app.delete("/api/contacts/{contact_id}")
def delete_contact(
    contact_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> dict[str, bool | int | str]:
    contact = session.get(Contact, contact_id)
    if not contact or not organization_matches(contact, current_user):
        raise HTTPException(status_code=404, detail="联系人不存在")
    require_owner_scope(current_user, contact.owner)
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


@app.get("/api/leads", response_model=list[LeadRead] | PaginatedResponse[LeadRead])
def list_leads(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    stage: str = "",
    owner: str = "",
    region: str = "",
    ai_assisted: bool | None = None,
) -> list[SalesLead] | dict:
    leads = session.exec(select(SalesLead).order_by(SalesLead.due_date.asc())).all()
    leads = filter_by_organization_scope(leads, current_user)
    leads = filter_by_owner_scope(leads, current_user)
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


@app.post("/api/leads", response_model=LeadRead, status_code=201)
def create_lead(
    payload: SalesLeadCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> SalesLead:
    owner = normalize_payload_owner(payload.owner, current_user)
    require_payload_owner_scope(current_user, owner)
    lead = SalesLead(**{**payload.model_dump(), "owner": owner, "organization_id": current_user.organization_id})
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


@app.patch("/api/leads/{lead_id}", response_model=LeadRead)
def update_lead(
    lead_id: int,
    payload: SalesLeadUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> SalesLead:
    lead = session.get(SalesLead, lead_id)
    if not lead or not organization_matches(lead, current_user):
        raise HTTPException(status_code=404, detail="商机不存在")
    require_owner_scope(current_user, lead.owner)
    updates = patch_values(payload)
    if "owner" in updates:
        updates["owner"] = normalize_payload_owner(updates["owner"], current_user)
        require_payload_owner_scope(current_user, updates["owner"])
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


@app.delete("/api/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> dict[str, bool | int | str]:
    lead = session.get(SalesLead, lead_id)
    if not lead or not organization_matches(lead, current_user):
        raise HTTPException(status_code=404, detail="商机不存在")
    require_owner_scope(current_user, lead.owner)
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


@app.get("/api/cases", response_model=list[SupportCaseRead] | PaginatedResponse[SupportCaseRead])
def list_cases(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    priority: str = "",
    status: str = "",
) -> list[SupportCase] | dict:
    cases = session.exec(select(SupportCase).order_by(SupportCase.due_date.asc())).all()
    cases = filter_by_organization_scope(cases, current_user)
    cases = filter_by_owner_scope(cases, current_user)
    cases = filter_records(
        cases,
        q=q,
        fields=("title", "account", "owner", "priority", "status", "status_label"),
        owner=owner,
        priority=priority,
        status=status,
    )
    return paginate_or_list(cases, page=page, per_page=per_page)


@app.post("/api/cases", response_model=SupportCaseRead, status_code=201)
def create_case(
    payload: SupportCaseCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> SupportCase:
    owner = normalize_payload_owner(payload.owner, current_user)
    require_payload_owner_scope(current_user, owner)
    support_case = SupportCase(**{**payload.model_dump(), "owner": owner, "organization_id": current_user.organization_id})
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


@app.patch("/api/cases/{case_id}", response_model=SupportCaseRead)
def update_case(
    case_id: int,
    payload: SupportCaseUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> SupportCase:
    support_case = session.get(SupportCase, case_id)
    if not support_case or not organization_matches(support_case, current_user):
        raise HTTPException(status_code=404, detail="工单不存在")
    require_owner_scope(current_user, support_case.owner)
    updates = patch_values(payload)
    if "owner" in updates:
        updates["owner"] = normalize_payload_owner(updates["owner"], current_user)
        require_payload_owner_scope(current_user, updates["owner"])
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


@app.delete("/api/cases/{case_id}")
def delete_case(
    case_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> dict[str, bool | int | str]:
    support_case = session.get(SupportCase, case_id)
    if not support_case or not organization_matches(support_case, current_user):
        raise HTTPException(status_code=404, detail="工单不存在")
    require_owner_scope(current_user, support_case.owner)
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


@app.get("/api/tasks", response_model=list[TaskItemRead] | PaginatedResponse[TaskItemRead])
def list_tasks(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    priority: str = "",
    status: str = "",
) -> list[TaskItem] | dict:
    tasks = session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()
    tasks = filter_by_organization_scope(tasks, current_user)
    tasks = filter_by_owner_scope(tasks, current_user)
    tasks = filter_records(
        tasks,
        q=q,
        fields=("title", "description", "owner", "due_date", "priority", "status", "status_label"),
        owner=owner,
        priority=priority,
        status=status,
    )
    return paginate_or_list(tasks, page=page, per_page=per_page)


@app.post("/api/tasks", response_model=TaskItemRead, status_code=201)
def create_task(
    payload: TaskItemCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> TaskItem:
    owner = normalize_payload_owner(payload.owner, current_user)
    require_payload_owner_scope(current_user, owner)
    task = TaskItem(**{**payload.model_dump(), "owner": owner, "organization_id": current_user.organization_id})
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


@app.patch("/api/tasks/{task_id}", response_model=TaskItemRead)
def update_task(
    task_id: int,
    payload: TaskItemUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> TaskItem:
    task = session.get(TaskItem, task_id)
    if not task or not organization_matches(task, current_user):
        raise HTTPException(status_code=404, detail="任务不存在")
    require_owner_scope(current_user, task.owner)
    updates = patch_values(payload)
    if "owner" in updates:
        updates["owner"] = normalize_payload_owner(updates["owner"], current_user)
        require_payload_owner_scope(current_user, updates["owner"])
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


@app.delete("/api/tasks/{task_id}")
def delete_task(
    task_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> dict[str, bool | int | str]:
    task = session.get(TaskItem, task_id)
    if not task or not organization_matches(task, current_user):
        raise HTTPException(status_code=404, detail="任务不存在")
    require_owner_scope(current_user, task.owner)
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


@app.get("/api/goals", response_model=list[SalesGoalRead] | PaginatedResponse[SalesGoalRead])
def list_goals(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    period: str = "",
    owner: str = "",
) -> list[SalesGoal] | dict:
    goals = session.exec(select(SalesGoal).order_by(SalesGoal.created_at.desc())).all()
    goals = filter_by_organization_scope(goals, current_user)
    goals = filter_by_owner_scope(goals, current_user)
    goals = filter_records(goals, q=q, fields=("name", "period", "owner", "note"), period=period, owner=owner)
    return paginate_or_list(goals, page=page, per_page=per_page)


@app.post("/api/goals", response_model=SalesGoalRead, status_code=201)
def create_goal(
    payload: SalesGoalCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> SalesGoal:
    progress = payload.progress
    if progress is None:
        progress = round(payload.current / payload.target * 100) if payload.target else 0
    owner = normalize_payload_owner(payload.owner, current_user)
    require_payload_owner_scope(current_user, owner)
    goal = SalesGoal(
        organization_id=current_user.organization_id,
        name=payload.name,
        period=payload.period,
        owner=owner,
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
        operator=goal.owner,
        summary=f"新建销售目标 {goal.name}",
        detail=f"周期 {goal.period}，负责人 {goal.owner}，进度 {goal.progress}%",
    )
    session.commit()
    session.refresh(goal)
    return goal


@app.patch("/api/goals/{goal_id}", response_model=SalesGoalRead)
def update_goal(
    goal_id: int,
    payload: SalesGoalUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> SalesGoal:
    goal = session.get(SalesGoal, goal_id)
    if not goal or not organization_matches(goal, current_user):
        raise HTTPException(status_code=404, detail="目标不存在")
    require_owner_scope(current_user, goal.owner)
    updates = patch_values(payload)
    if "owner" in updates:
        updates["owner"] = normalize_payload_owner(updates["owner"], current_user)
        require_payload_owner_scope(current_user, updates["owner"])
    apply_updates(goal, updates)
    if "progress" not in updates and goal.target:
        goal.progress = min(max(round(goal.current / goal.target * 100), 0), 100)
    session.add(goal)
    add_business_audit(
        session,
        action="update",
        entity_type="goal",
        entity_id=goal.id,
        operator=goal.owner,
        summary=f"更新销售目标 {goal.name}",
        detail=", ".join(sorted(updates.keys())) or "更新目标资料",
    )
    session.commit()
    session.refresh(goal)
    return goal


@app.delete("/api/goals/{goal_id}")
def delete_goal(
    goal_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
) -> dict[str, bool | int | str]:
    goal = session.get(SalesGoal, goal_id)
    if not goal or not organization_matches(goal, current_user):
        raise HTTPException(status_code=404, detail="目标不存在")
    require_owner_scope(current_user, goal.owner)
    add_business_audit(
        session,
        action="delete",
        entity_type="goal",
        entity_id=goal_id,
        operator=goal.owner,
        summary=f"删除销售目标 {goal.name}",
        detail=f"周期 {goal.period}，负责人 {goal.owner}",
    )
    session.delete(goal)
    session.commit()
    return delete_response("goal", goal_id)


@app.get("/api/ai-audit-logs", response_model=list[AIInteractionLogRead] | PaginatedResponse[AIInteractionLogRead])
def list_ai_audit_logs(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("audit:read"))],
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
    logs = filter_by_organization_scope(logs, current_user)
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


@app.get("/api/ai-audit-logs/export.csv")
def export_ai_audit_logs_csv(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("audit:read"))],
    q: str = "",
    operation: str = "",
    status: str = "",
    entity_type: str = "",
    fallback_used: bool | None = None,
) -> Response:
    logs = session.exec(select(AIInteractionLog).order_by(AIInteractionLog.created_at.desc())).all()
    logs = filter_by_organization_scope(logs, current_user)
    logs = filter_records(
        logs,
        q=q,
        fields=("operation", "provider", "model", "status", "entity_type", "request_summary", "response_summary"),
        operation=operation,
        status=status,
        entity_type=entity_type,
    )
    logs = filter_bool(logs, "fallback_used", fallback_used)
    return Response(
        content=build_ai_audit_csv(logs),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="smart-crm-ai-audit.csv"'},
    )


def matches_ai_quality_filters(
    log: AIInteractionLog,
    date_from: date | None,
    date_to: date | None,
    operation: str,
    model: str,
) -> bool:
    log_date = log.created_at.date()
    if date_from and log_date < date_from:
        return False
    if date_to and log_date > date_to:
        return False
    if operation and log.operation != operation:
        return False
    if model and log.model != model:
        return False
    return True


def average_latency(logs: list[AIInteractionLog]) -> int:
    return round(sum(log.latency_ms for log in logs) / len(logs)) if logs else 0


@app.get("/api/reports/ai-quality", response_model=AIQualityReportResponse)
def get_ai_quality_report(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("audit:read"))],
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    operation: str = "",
    model: str = "",
) -> AIQualityReportResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    all_logs = filter_by_organization_scope(
        session.exec(select(AIInteractionLog).order_by(AIInteractionLog.created_at.desc())).all(),
        current_user,
    )
    logs = [log for log in all_logs if matches_ai_quality_filters(log, date_from, date_to, operation, model)]
    total_count = len(logs)
    llm_logs = [log for log in logs if not log.fallback_used]
    fallback_logs = [log for log in logs if log.fallback_used]

    recommendations = filter_by_organization_scope(
        session.exec(select(CopilotRecommendation).order_by(CopilotRecommendation.created_at.desc())).all(),
        current_user,
    )
    converted_task_count = len([
        recommendation
        for recommendation in recommendations
        if recommendation.id is not None and find_task_for_copilot_recommendation(session, recommendation.id, current_user.organization_id)
    ])
    recommendation_count = len(recommendations)
    recommendation_fallback_count = len([recommendation for recommendation in recommendations if recommendation.fallback_used])
    feedback_recommendations = [recommendation for recommendation in recommendations if recommendation.feedback_status]
    positive_feedback_count = len([
        recommendation
        for recommendation in feedback_recommendations
        if recommendation.feedback_status in {"accepted", "helpful"} or recommendation.feedback_rating >= 4
    ])
    negative_feedback_count = len([
        recommendation
        for recommendation in feedback_recommendations
        if recommendation.feedback_status in {"not_helpful", "dismissed"} or recommendation.feedback_rating <= 2
    ])
    recommendation_signal = AIQualityRecommendationSignal(
        total_recommendations=recommendation_count,
        average_rule_score=round(sum(recommendation.rule_score for recommendation in recommendations) / recommendation_count, 1) if recommendation_count else 0,
        average_win_rate=round(sum(recommendation.win_rate for recommendation in recommendations) / recommendation_count, 2) if recommendation_count else 0,
        fallback_count=recommendation_fallback_count,
        fallback_rate=round(recommendation_fallback_count / recommendation_count, 2) if recommendation_count else 0,
        converted_task_count=converted_task_count,
        conversion_rate=round(converted_task_count / recommendation_count, 2) if recommendation_count else 0,
        feedback_count=len(feedback_recommendations),
        positive_feedback_count=positive_feedback_count,
        negative_feedback_count=negative_feedback_count,
        positive_feedback_rate=round(positive_feedback_count / len(feedback_recommendations), 2) if feedback_recommendations else 0,
        average_feedback_rating=round(sum(recommendation.feedback_rating for recommendation in feedback_recommendations) / len(feedback_recommendations), 1) if feedback_recommendations else 0,
    )

    operation_names = sorted({log.operation for log in logs})
    operation_breakdown = []
    for operation_name in operation_names:
        operation_logs = [log for log in logs if log.operation == operation_name]
        operation_fallback_count = len([log for log in operation_logs if log.fallback_used])
        operation_breakdown.append(
            AIQualityOperationBreakdown(
                operation=operation_name,
                label=AI_OPERATION_LABELS.get(operation_name, operation_name),
                total_count=len(operation_logs),
                llm_count=len(operation_logs) - operation_fallback_count,
                fallback_count=operation_fallback_count,
                fallback_rate=round(operation_fallback_count / len(operation_logs), 2) if operation_logs else 0,
                average_latency_ms=average_latency(operation_logs),
            )
        )
    operation_breakdown = sorted(operation_breakdown, key=lambda item: (item.fallback_rate, item.total_count), reverse=True)

    model_names = sorted({log.model or "未配置" for log in logs})
    model_breakdown = []
    for model_name in model_names:
        model_logs = [log for log in logs if (log.model or "未配置") == model_name]
        model_fallback_count = len([log for log in model_logs if log.fallback_used])
        model_breakdown.append(
            AIQualityModelBreakdown(
                model=model_name,
                total_count=len(model_logs),
                llm_count=len(model_logs) - model_fallback_count,
                fallback_count=model_fallback_count,
                fallback_rate=round(model_fallback_count / len(model_logs), 2) if model_logs else 0,
                average_latency_ms=average_latency(model_logs),
            )
        )
    model_breakdown = sorted(model_breakdown, key=lambda item: (item.fallback_rate, item.total_count), reverse=True)

    metrics = [
        DashboardMetric(label="AI 调用总量", value=str(total_count), hint="按 AIInteractionLog 实时统计"),
        DashboardMetric(label="LLM 成功率", value=f"{round(len(llm_logs) / total_count * 100) if total_count else 0}%", hint=f"{len(llm_logs)} 次模型增强"),
        DashboardMetric(label="兜底率", value=f"{round(len(fallback_logs) / total_count * 100) if total_count else 0}%", hint=f"{len(fallback_logs)} 次规则兜底"),
        DashboardMetric(label="平均耗时", value=f"{average_latency(logs)}ms", hint="端点级平均耗时"),
        DashboardMetric(label="场景覆盖", value=str(len(operation_names)), hint="已记录 AI 操作类型"),
        DashboardMetric(label="推荐转任务率", value=f"{round(recommendation_signal.conversion_rate * 100)}%", hint=f"{converted_task_count}/{recommendation_count} 条推荐"),
        DashboardMetric(label="人工好评率", value=f"{round(recommendation_signal.positive_feedback_rate * 100)}%", hint=f"{positive_feedback_count}/{len(feedback_recommendations)} 条反馈"),
    ]

    applied_filters = {
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
        "operation": operation,
        "model": model,
    }

    return AIQualityReportResponse(
        generated_at=datetime.utcnow(),
        metrics=metrics,
        operation_breakdown=operation_breakdown,
        model_breakdown=model_breakdown,
        recommendation_signal=recommendation_signal,
        recent_fallbacks=fallback_logs[:6],
        applied_filters=applied_filters,
    )


@app.get("/api/business-audit-logs", response_model=list[BusinessAuditLogRead] | PaginatedResponse[BusinessAuditLogRead])
def list_business_audit_logs(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("audit:read"))],
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
    logs = filter_by_organization_scope(logs, current_user)
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


@app.get("/api/business-audit-logs/export.csv")
def export_business_audit_logs_csv(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("audit:read"))],
    q: str = "",
    action: str = "",
    entity_type: str = "",
    operator: str = "",
    status: str = "",
) -> Response:
    logs = session.exec(select(BusinessAuditLog).order_by(BusinessAuditLog.created_at.desc())).all()
    logs = filter_by_organization_scope(logs, current_user)
    logs = filter_records(
        logs,
        q=q,
        fields=("action", "entity_type", "operator", "status", "summary", "detail"),
        action=action,
        entity_type=entity_type,
        operator=operator,
        status=status,
    )
    return Response(
        content=build_business_audit_csv(logs),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="smart-crm-business-audit.csv"'},
    )


@app.get("/api/system/consistency-checks", response_model=ConsistencyReportResponse, dependencies=[Depends(require_permission("audit:read"))])
def get_system_consistency_checks(session: SessionDep) -> dict:
    return build_consistency_payload(session)


@app.get("/api/orders", response_model=list[SalesOrderRead] | PaginatedResponse[SalesOrderRead])
def list_orders(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("order:manage"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    region: str = "",
    status: str = "",
    created_by_ai: bool | None = None,
) -> list[SalesOrderRead] | dict:
    orders = session.exec(select(SalesOrder).order_by(SalesOrder.created_at.desc())).all()
    orders = filter_by_organization_scope(orders, current_user)
    serialized_orders = [serialize_order(order, session) for order in orders]
    serialized_orders = filter_by_owner_scope(serialized_orders, current_user)
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


@app.get("/api/order-approvals", response_model=list[OrderApprovalRead] | PaginatedResponse[OrderApprovalRead])
def list_order_approvals(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("order:manage"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    owner: str = "",
    status: str = "",
    reviewer: str = "",
    risk_level: str = "",
    sla_status: str = "",
) -> list[OrderApprovalRead] | dict:
    approvals = session.exec(select(OrderApprovalRequest).order_by(OrderApprovalRequest.created_at.desc())).all()
    approvals = filter_by_organization_scope(approvals, current_user)
    approvals = filter_by_owner_scope(approvals, current_user)
    serialized_approvals = [serialize_order_approval(approval, session) for approval in approvals]
    serialized_approvals = filter_records(
        serialized_approvals,
        q=q,
        fields=("customer_name", "owner", "requester", "reviewer", "status", "reason", "risk_summary", "risk_level", "sla_status", "decision_comment"),
        owner=owner,
        status=status,
        reviewer=reviewer,
        risk_level=risk_level,
        sla_status=sla_status,
    )
    return paginate_or_list(serialized_approvals, page=page, per_page=per_page)


@app.post("/api/orders/{order_id}/approval-requests", response_model=OrderApprovalRead, status_code=201)
def submit_order_approval_request(
    order_id: int,
    payload: OrderApprovalCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("order:manage"))],
) -> OrderApprovalRead:
    order = session.get(SalesOrder, order_id)
    if not order or not organization_matches(order, current_user):
        raise HTTPException(status_code=404, detail="订单不存在")
    require_owner_scope(current_user, order.owner)
    if order.status == "fulfilled":
        raise HTTPException(status_code=400, detail="已履约订单不需要提交审批")
    if payload.target_order_status not in ORDER_APPROVAL_REQUIRED_STATUSES:
        raise HTTPException(status_code=400, detail="审批目标状态必须为已确认或已履约")
    if payload.target_order_status == order.status:
        raise HTTPException(status_code=400, detail="目标状态与当前订单状态一致")
    if find_pending_order_approval(session, order_id):
        raise HTTPException(status_code=400, detail="该订单已有待审批申请")

    reason = payload.reason.strip() or "订单确认前需要经理复核商务条款、库存和交付风险。"
    requested_at = datetime.utcnow()
    risk_level = evaluate_order_approval_risk_level(order, session, payload.target_order_status)
    approval = OrderApprovalRequest(
        organization_id=current_user.organization_id,
        order_id=order.id or order_id,
        owner=order.owner,
        requester=current_user.full_name,
        reviewer=payload.reviewer.strip() or "销售经理",
        status=OrderApprovalStatus.pending,
        reason=summarize_text(reason, limit=360),
        risk_summary=summarize_text(build_order_approval_risk_summary(order, session, payload.target_order_status), limit=500),
        risk_level=risk_level,
        sla_due_at=calculate_order_approval_sla_due_at(requested_at, risk_level),
        requested_total=order.total_amount,
        previous_order_status=order.status,
        target_order_status=payload.target_order_status,
        created_at=requested_at,
    )
    session.add(approval)
    session.flush()
    add_business_audit(
        session,
        action="submit_approval",
        entity_type="order_approval",
        entity_id=approval.id,
        operator=current_user.full_name,
        summary=f"提交订单 #{order.id} 审批",
        detail=f"目标状态 {payload.target_order_status.value}；风险等级 {approval.risk_level}；SLA {approval.sla_due_at}；{approval.risk_summary}",
    )
    session.commit()
    session.refresh(approval)
    return serialize_order_approval(approval, session)


@app.post("/api/order-approvals/{approval_id}/reminders", response_model=OrderApprovalRead)
def remind_order_approval_request(
    approval_id: int,
    payload: OrderApprovalReminderCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("order:manage"))],
) -> OrderApprovalRead:
    approval = session.get(OrderApprovalRequest, approval_id)
    if not approval or not organization_matches(approval, current_user):
        raise HTTPException(status_code=404, detail="审批申请不存在")
    if approval.status != OrderApprovalStatus.pending:
        raise HTTPException(status_code=400, detail="审批申请已处理，不能催办")
    require_owner_scope(current_user, approval.owner)

    sla_status, sla_hours_remaining = get_order_approval_sla_details(approval)
    message = payload.message.strip() or "请尽快处理待审批订单。"
    add_business_audit(
        session,
        action="remind_approval",
        entity_type="order_approval",
        entity_id=approval.id,
        operator=current_user.full_name,
        summary=f"催办订单 #{approval.order_id} 审批",
        detail=f"目标审批人 {approval.reviewer or '销售经理'}；SLA 状态 {sla_status}；剩余小时 {sla_hours_remaining}；{message}",
    )
    session.commit()
    session.refresh(approval)
    return serialize_order_approval(approval, session)


@app.post("/api/order-approvals/{approval_id}/assignment", response_model=OrderApprovalRead)
def assign_order_approval_request(
    approval_id: int,
    payload: OrderApprovalAssignmentCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("approval:manage"))],
) -> OrderApprovalRead:
    approval = session.get(OrderApprovalRequest, approval_id)
    if not approval or not organization_matches(approval, current_user):
        raise HTTPException(status_code=404, detail="审批申请不存在")
    if approval.status != OrderApprovalStatus.pending:
        raise HTTPException(status_code=400, detail="审批申请已处理，不能转派")

    previous_reviewer = approval.reviewer or "销售经理"
    next_reviewer = payload.reviewer.strip()
    if not next_reviewer:
        raise HTTPException(status_code=422, detail="审批人不能为空")
    approval.reviewer = summarize_text(next_reviewer, limit=64)
    session.add(approval)
    add_business_audit(
        session,
        action="assign_approval",
        entity_type="order_approval",
        entity_id=approval.id,
        operator=current_user.full_name,
        summary=f"转派订单 #{approval.order_id} 审批",
        detail=f"原审批人 {previous_reviewer}；新审批人 {approval.reviewer}；{payload.comment.strip() or '无补充说明'}",
    )
    session.commit()
    session.refresh(approval)
    return serialize_order_approval(approval, session)


@app.post("/api/order-approvals/{approval_id}/decision", response_model=OrderApprovalRead)
def decide_order_approval_request(
    approval_id: int,
    payload: OrderApprovalDecision,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("approval:manage"))],
) -> OrderApprovalRead:
    approval = session.get(OrderApprovalRequest, approval_id)
    if not approval or not organization_matches(approval, current_user):
        raise HTTPException(status_code=404, detail="审批申请不存在")
    if approval.status != OrderApprovalStatus.pending:
        raise HTTPException(status_code=400, detail="审批申请已处理")
    order = session.get(SalesOrder, approval.order_id)
    if not order or not organization_matches(order, current_user):
        raise HTTPException(status_code=404, detail="关联订单不存在")

    decision_status = OrderApprovalStatus.approved if payload.decision == "approved" else OrderApprovalStatus.rejected
    approval.status = decision_status
    approval.reviewer = payload.reviewer.strip() or current_user.full_name
    approval.decision_comment = summarize_text(payload.comment.strip() or ("审批通过" if decision_status == OrderApprovalStatus.approved else "审批驳回"), limit=360)
    approval.decided_at = datetime.utcnow()
    if decision_status == OrderApprovalStatus.approved:
        order.status = approval.target_order_status
        session.add(order)

    session.add(approval)
    add_business_audit(
        session,
        action="approve" if decision_status == OrderApprovalStatus.approved else "reject",
        entity_type="order_approval",
        entity_id=approval.id,
        operator=approval.reviewer,
        summary=f"{'通过' if decision_status == OrderApprovalStatus.approved else '驳回'}订单 #{approval.order_id} 审批",
        detail=approval.decision_comment,
    )
    session.commit()
    session.refresh(approval)
    return serialize_order_approval(approval, session)


@app.get("/api/orders/export.csv")
def export_orders_csv(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("order:manage"))],
) -> Response:
    orders = session.exec(select(SalesOrder).order_by(SalesOrder.created_at.desc())).all()
    orders = filter_by_organization_scope(orders, current_user)
    serialized_orders = [serialize_order(order, session) for order in orders]
    serialized_orders = filter_by_owner_scope(serialized_orders, current_user)
    csv_content = build_orders_csv(serialized_orders)
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="smart-crm-orders.csv"'},
    )


@app.get("/api/orders/{order_id}/inventory-movements", response_model=list[InventoryMovementRead])
def get_order_inventory_movements(
    order_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("order:manage"))],
) -> list[InventoryMovementRead]:
    order = session.get(SalesOrder, order_id)
    if not order or not organization_matches(order, current_user):
        raise HTTPException(status_code=404, detail="订单不存在")
    require_owner_scope(current_user, order.owner)
    order_marker = f"订单 #{order_id} "
    movements = session.exec(
        select(InventoryMovement)
        .where(
            InventoryMovement.reason.contains(order_marker),
            InventoryMovement.organization_id == current_user.organization_id,
        )
        .order_by(InventoryMovement.created_at.desc())
    ).all()
    return [serialize_inventory_movement(movement, session) for movement in movements]


@app.patch("/api/orders/{order_id}", response_model=SalesOrderRead)
def update_order(
    order_id: int,
    payload: SalesOrderUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("order:manage"))],
) -> SalesOrderRead:
    order = session.get(SalesOrder, order_id)
    if not order or not organization_matches(order, current_user):
        raise HTTPException(status_code=404, detail="订单不存在")
    require_owner_scope(current_user, order.owner)
    before_total = order.total_amount
    previous_status = order.status
    if "due_date" in payload.model_fields_set and payload.due_date is None:
        raise HTTPException(status_code=422, detail="交付日期不能为空")
    updates = payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"items"})
    requested_status = updates.pop("status", None)
    if "owner" in updates:
        updates["owner"] = normalize_payload_owner(updates["owner"], current_user)
        require_payload_owner_scope(current_user, updates["owner"])
    if "due_date" in updates and updates["due_date"] < order.order_date:
        raise HTTPException(status_code=422, detail="交付日期不能早于下单日期")
    apply_updates(order, updates)
    if payload.items is not None:
        replace_order_items(order, payload.items, session)
    if requested_status is not None:
        ensure_order_status_transition_allowed(order, session, current_user, requested_status, previous_status)
        order.status = requested_status
    session.add(order)
    changed_fields = sorted(updates.keys())
    if requested_status is not None:
        changed_fields.append("status")
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


@app.post("/api/orders", response_model=SalesOrderRead, status_code=201)
def create_order(
    payload: SalesOrderCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("order:manage"))],
) -> SalesOrderRead:
    owner = normalize_payload_owner(payload.owner, current_user)
    require_payload_owner_scope(current_user, owner)
    customer = session.get(Customer, payload.customer_id)
    if not customer or not organization_matches(customer, current_user):
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)

    product_ids = [item.product_id for item in payload.items]
    products = session.exec(
        select(Product).where(
            Product.id.in_(product_ids),
            Product.organization_id == current_user.organization_id,
        )
    ).all()
    product_map = {product.id: product for product in products}
    if len(product_map) != len(product_ids):
        raise HTTPException(status_code=400, detail="存在无效商品")
    for item in payload.items:
        product = product_map[item.product_id]
        if item.quantity > product.stock:
            raise HTTPException(status_code=400, detail=f"{product.name} 库存不足，当前仅剩 {product.stock} 件")

    order = SalesOrder(
        organization_id=current_user.organization_id,
        customer_id=payload.customer_id,
        owner=owner,
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
                organization_id=current_user.organization_id,
                product_id=product.id,
                change_quantity=-item.quantity,
                before_stock=before_stock,
                after_stock=product.stock,
                reason=f"订单 #{order.id} 创建扣减库存",
                operator=owner,
                source="order_deduction",
            )
        )

    order.total_amount = total_amount
    ensure_order_status_transition_allowed(order, session, current_user, order.status, OrderStatus.draft)
    session.add(order)
    add_business_audit(
        session,
        action="create",
        entity_type="order",
        entity_id=order.id,
        operator=owner,
        summary=f"创建订单 #{order.id}",
        detail=f"客户 {customer.company}，明细 {len(payload.items)} 条，总额 {order.total_amount:.0f}",
    )
    session.commit()
    session.refresh(order)
    return serialize_order(order, session)


@app.get("/api/vision-extract/drafts", response_model=list[CaptureDraftRead] | PaginatedResponse[CaptureDraftRead])
def list_capture_drafts(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    status: str = "",
) -> list[CaptureDraftRead] | dict:
    statement = (
        select(CaptureDraft)
        .where(CaptureDraft.organization_id == current_user.organization_id)
        .order_by(CaptureDraft.created_at.desc())
    )
    drafts = session.exec(statement).all()
    if not has_all_data_scope(current_user):
        drafts = [draft for draft in drafts if owner_matches_user(draft.created_by, current_user)]
    if status.strip():
        drafts = [draft for draft in drafts if draft.status == status.strip()]
    serialized = [serialize_capture_draft(draft) for draft in drafts]
    return paginate_or_list(serialized, page=page, per_page=per_page)


@app.patch("/api/vision-extract/drafts/{draft_id}", response_model=CaptureDraftRead)
def update_capture_draft(
    draft_id: int,
    payload: CaptureDraftUpdate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> CaptureDraftRead:
    draft = session.get(CaptureDraft, draft_id)
    if not draft or draft.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="智能录单草稿不存在")
    require_owner_scope(current_user, draft.created_by)
    submitted_order = None
    if payload.submitted_order_id is not None:
        submitted_order = session.get(SalesOrder, payload.submitted_order_id)
        if not submitted_order or not organization_matches(submitted_order, current_user):
            raise HTTPException(status_code=404, detail="关联订单不存在")
        require_owner_scope(current_user, submitted_order.owner)
    if payload.status == "submitted" and submitted_order is None:
        raise HTTPException(status_code=422, detail="提交状态必须关联订单")
    draft.status = payload.status
    draft.submitted_order_id = payload.submitted_order_id if payload.status == "submitted" else None
    draft.updated_at = datetime.utcnow()
    session.add(draft)
    add_business_audit(
        session,
        action="update",
        entity_type="capture_draft",
        entity_id=draft.id,
        operator=current_user.full_name,
        summary=f"更新智能录单草稿 #{draft.id}",
        detail=f"状态 {draft.status}，订单 {draft.submitted_order_id or '未关联'}",
    )
    session.commit()
    session.refresh(draft)
    return serialize_capture_draft(draft)


@app.post("/api/vision-extract", response_model=VisionExtractResponse)
async def vision_extract(
    file: Annotated[UploadFile, File(...)],
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> VisionExtractResponse:
    start_time = perf_counter()
    filename = file.filename or "uploaded-file"
    content_type = file.content_type or "unknown"
    customers = filter_by_organization_scope(session.exec(select(Customer)).all(), current_user)
    customers = filter_by_owner_scope(customers, current_user)
    products = filter_by_organization_scope(session.exec(select(Product)).all(), current_user)
    result = await vision_service.extract(file, customers=customers, products=products)
    draft = CaptureDraft(
        organization_id=current_user.organization_id,
        created_by=current_user.full_name,
        filename=filename,
        content_type=content_type,
        customer_id=result.customer_id,
        customer_name=result.customer_name,
        company=result.company,
        confidence=result.confidence,
        source=result.source,
        fallback_used=result.fallback_used,
        summary=result.summary,
        suggested_notes=result.suggested_notes,
        raw_text_excerpt=result.raw_text_excerpt,
        items_json=encode_json_list([item.model_dump() for item in result.items]),
        status="draft",
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    result.capture_draft_id = draft.id
    save_ai_interaction(
        session,
        operation="vision_extract",
        model=settings.llm_vision_model or settings.llm_model,
        fallback_used=result.fallback_used,
        start_time=start_time,
        request_summary=f"{filename} / {content_type} / {len(customers)} customers / {len(products)} products",
        response_summary=f"{result.company} / {result.source} / {len(result.items)} items / {result.summary}",
        entity_type="capture_draft",
        entity_id=draft.id,
        organization_id=current_user.organization_id,
    )
    return result


@app.get("/api/copilot/summary", response_model=CopilotSummaryResponse)
async def copilot_summary(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> CopilotSummaryResponse:
    start_time = perf_counter()
    leads = session.exec(select(SalesLead).order_by(SalesLead.due_date.asc())).all()
    leads = filter_by_organization_scope(leads, current_user)
    leads = filter_by_owner_scope(leads, current_user)
    customers = filter_by_owner_scope(filter_by_organization_scope(session.exec(select(Customer)).all(), current_user), current_user)
    contacts = filter_by_owner_scope(filter_by_organization_scope(session.exec(select(Contact)).all(), current_user), current_user)
    activities = filter_by_owner_scope(filter_by_organization_scope(session.exec(select(CustomerActivity)).all(), current_user), current_user)
    orders = filter_by_owner_scope(filter_by_organization_scope(session.exec(select(SalesOrder)).all(), current_user), current_user)
    cases = filter_by_owner_scope(filter_by_organization_scope(session.exec(select(SupportCase)).all(), current_user), current_user)
    recommendations = filter_by_owner_scope(filter_by_organization_scope(session.exec(select(CopilotRecommendation)).all(), current_user), current_user)
    tasks = filter_by_owner_scope(filter_by_organization_scope(session.exec(select(TaskItem)).all(), current_user), current_user)

    health_profiles_by_customer = {}
    for customer in customers:
        aliases = customer_aliases(customer)
        profile = build_customer_health_profile(
            customer,
            contacts=[contact for contact in contacts if contact.company in aliases],
            activities=[activity for activity in activities if activity.customer_id == customer.id or activity.customer_name in aliases],
            leads=[lead for lead in leads if lead.customer_name in aliases],
            orders=[order for order in orders if order.customer_id == customer.id],
            cases=[support_case for support_case in cases if support_case.account in aliases],
            recommendations=[recommendation for recommendation in recommendations if recommendation.customer_name in aliases],
            tasks=[task for task in tasks if any(alias in f"{task.title} {task.description}" for alias in aliases)],
        )
        for alias in aliases:
            health_profiles_by_customer[alias] = profile

    result = await copilot_service.summarize(leads, health_profiles_by_customer=health_profiles_by_customer)
    add_copilot_summary_history(session, result, current_user.organization_id)
    save_ai_interaction(
        session,
        operation="copilot_summary",
        model=settings.llm_model,
        fallback_used=result.fallback_used,
        start_time=start_time,
        request_summary=f"{len(leads)} leads / {len(health_profiles_by_customer)} health aliases",
        response_summary=result.llm_summary,
        entity_type="lead",
        entity_id=result.top_opportunity.id if result.top_opportunity else None,
        organization_id=current_user.organization_id,
    )
    return result


@app.post("/api/copilot/ask", response_model=CopilotAskResponse)
async def copilot_ask(
    payload: CopilotAskRequest,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> CopilotAskResponse:
    start_time = perf_counter()
    customers = filter_by_organization_scope(session.exec(select(Customer).order_by(Customer.created_at.desc())).all(), current_user)
    activities = filter_by_organization_scope(session.exec(select(CustomerActivity).order_by(CustomerActivity.occurred_at.desc())).all(), current_user)
    leads = filter_by_organization_scope(session.exec(select(SalesLead).order_by(SalesLead.due_date.asc())).all(), current_user)
    orders = filter_by_organization_scope(session.exec(select(SalesOrder).order_by(SalesOrder.created_at.desc())).all(), current_user)
    tasks = filter_by_organization_scope(session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all(), current_user)
    cases = filter_by_organization_scope(session.exec(select(SupportCase).order_by(SupportCase.created_at.desc())).all(), current_user)
    recommendations = filter_by_organization_scope(session.exec(select(CopilotRecommendation).order_by(CopilotRecommendation.created_at.desc())).all(), current_user)

    if payload.customer_id is not None:
        customer = session.get(Customer, payload.customer_id)
        if not customer or not organization_matches(customer, current_user):
            raise HTTPException(status_code=404, detail="客户不存在")
        require_owner_scope(current_user, customer.owner)
        customers = [customer]
        activities = [activity for activity in activities if activity.customer_id == customer.id]
        leads = [lead for lead in leads if lead.customer_name == customer.company]
        orders = [order for order in orders if order.customer_id == customer.id]
        cases = [case for case in cases if case.account == customer.company]
        recommendations = [item for item in recommendations if item.customer_name == customer.company]
    else:
        customers = filter_by_owner_scope(customers, current_user)
        activities = filter_by_owner_scope(activities, current_user)
        leads = filter_by_owner_scope(leads, current_user)
        orders = filter_by_owner_scope(orders, current_user)
        cases = filter_by_owner_scope(cases, current_user)
        recommendations = filter_by_owner_scope(recommendations, current_user)

    tasks = filter_by_owner_scope(tasks, current_user)
    result = await copilot_service.ask(
        payload.question,
        customers=customers,
        activities=activities,
        leads=leads,
        orders=orders,
        tasks=tasks,
        cases=cases,
        recommendations=recommendations,
    )
    save_ai_interaction(
        session,
        operation="copilot_ask",
        model=result.model,
        fallback_used=result.fallback_used,
        start_time=start_time,
        request_summary=f"{payload.question} / {len(customers)} customers / {len(leads)} leads / {len(orders)} orders",
        response_summary=result.answer,
        entity_type="customer" if payload.customer_id is not None else "crm",
        entity_id=payload.customer_id,
        organization_id=current_user.organization_id,
    )
    return result


@app.get("/api/copilot/recommendations", response_model=list[CopilotRecommendationRead] | PaginatedResponse[CopilotRecommendationRead])
def list_copilot_recommendations(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
    limit: int = 30,
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    q: str = "",
    source: str = "",
    grade: str = "",
    stage: str = "",
    fallback_used: bool | None = None,
) -> list[CopilotRecommendationRead] | dict:
    safe_limit = min(max(limit, 1), 100)
    has_filter = bool(q.strip() or source.strip() or grade.strip() or stage.strip() or fallback_used is not None)
    query_limit = None if page is not None or per_page is not None or has_filter else safe_limit
    statement = select(CopilotRecommendation).order_by(CopilotRecommendation.created_at.desc())
    if query_limit is not None and has_all_data_scope(current_user):
        statement = statement.limit(query_limit)
    raw_recommendations = filter_by_organization_scope(session.exec(statement).all(), current_user)
    recommendations = [serialize_copilot_recommendation(item) for item in raw_recommendations]
    recommendations = filter_by_owner_scope(recommendations, current_user)
    recommendations = filter_records(
        recommendations,
        q=q,
        fields=(
            "source",
            "lead_title",
            "customer_name",
            "owner",
            "region",
            "stage",
            "grade",
            "next_best_action",
            "message_draft",
            "llm_summary",
        ),
        source=source,
        grade=grade,
        stage=stage,
    )
    recommendations = filter_bool(recommendations, "fallback_used", fallback_used)
    if query_limit is not None and not has_all_data_scope(current_user):
        recommendations = recommendations[:safe_limit]
    return paginate_or_list(recommendations, page=page, per_page=per_page)


@app.patch("/api/copilot/recommendations/{recommendation_id}/feedback", response_model=CopilotRecommendationRead)
def update_copilot_recommendation_feedback(
    recommendation_id: int,
    payload: CopilotRecommendationFeedbackRequest,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> CopilotRecommendationRead:
    recommendation = session.get(CopilotRecommendation, recommendation_id)
    if not recommendation or not organization_matches(recommendation, current_user):
        raise HTTPException(status_code=404, detail="Copilot 推荐不存在")
    require_owner_scope(current_user, recommendation.owner)

    recommendation.feedback_status = payload.feedback_status
    recommendation.feedback_rating = payload.feedback_rating or COPILOT_FEEDBACK_DEFAULT_RATINGS[payload.feedback_status]
    recommendation.feedback_note = summarize_text(payload.feedback_note, limit=360)
    recommendation.feedback_by = current_user.full_name or current_user.email
    recommendation.feedback_at = datetime.utcnow()
    session.add(recommendation)
    add_business_audit(
        session,
        action="feedback",
        entity_type="copilot_recommendation",
        entity_id=recommendation.id,
        operator=recommendation.feedback_by,
        summary=f"Copilot 推荐反馈：{payload.feedback_status}",
        detail=f"评分 {recommendation.feedback_rating}，客户 {recommendation.customer_name or '未记录'}",
    )
    session.commit()
    session.refresh(recommendation)
    return serialize_copilot_recommendation(recommendation)


@app.post(
    "/api/copilot/recommendations/{recommendation_id}/task",
    response_model=TaskItemRead,
    status_code=201,
)
def create_task_from_copilot_recommendation(
    recommendation_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:write"))],
    _ai_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> TaskItem:
    recommendation = session.get(CopilotRecommendation, recommendation_id)
    if not recommendation or not organization_matches(recommendation, current_user):
        raise HTTPException(status_code=404, detail="Copilot 推荐不存在")
    require_owner_scope(current_user, recommendation.owner)

    existing_task = find_task_for_copilot_recommendation(session, recommendation_id, current_user.organization_id)
    if existing_task:
        require_owner_scope(current_user, existing_task.owner)
        return existing_task

    task = build_copilot_task(recommendation)
    session.add(task)
    session.flush()

    lead = session.get(SalesLead, recommendation.lead_id) if recommendation.lead_id else None
    if lead and recommendation.next_best_action:
        require_organization_scope(current_user, lead)
        lead.next_action = recommendation.next_best_action
        lead.ai_assisted = True
        session.add(lead)
        add_business_audit(
            session,
            action="update",
            entity_type="lead",
            entity_id=lead.id,
            operator=task.owner,
            summary=f"同步 Copilot 下一步动作到商机 {lead.title}",
            detail=f"来源 CopilotRecommendation #{recommendation_id}",
        )

    add_business_audit(
        session,
        action="convert",
        entity_type="task",
        entity_id=task.id,
        operator=task.owner,
        summary=f"Copilot 推荐转任务 {task.title}",
        detail=f"来源 CopilotRecommendation #{recommendation_id}，客户 {recommendation.customer_name}",
    )
    session.commit()
    session.refresh(task)
    return task


@app.post("/api/copilot/follow-up", response_model=CopilotFollowUpResponse)
async def copilot_follow_up(
    payload: CopilotFollowUpRequest,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> CopilotFollowUpResponse:
    start_time = perf_counter()
    lead = session.get(SalesLead, payload.lead_id) if payload.lead_id else None
    if payload.lead_id and (not lead or not organization_matches(lead, current_user)):
        raise HTTPException(status_code=404, detail="商机不存在")
    if lead:
        require_owner_scope(current_user, lead.owner)
    result = await copilot_service.follow_up(payload, lead)
    add_copilot_follow_up_history(session, payload, result, lead, current_user.organization_id)
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
        organization_id=current_user.organization_id,
    )
    return result


@app.post("/api/copilot/order-draft", response_model=CopilotOrderDraftResponse)
async def copilot_order_draft(
    payload: CopilotOrderDraftRequest,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> CopilotOrderDraftResponse:
    start_time = perf_counter()
    customer = session.get(Customer, payload.customer_id)
    if not customer or not organization_matches(customer, current_user):
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)

    if payload.product_ids:
        products = session.exec(
            select(Product).where(
                Product.id.in_(payload.product_ids),
                Product.organization_id == current_user.organization_id,
            )
        ).all()
        if len(products) != len(set(payload.product_ids)):
            raise HTTPException(status_code=400, detail="存在无效商品")
    else:
        products = session.exec(
            select(Product)
            .where(Product.organization_id == current_user.organization_id)
            .order_by(Product.created_at.desc())
        ).all()

    if not products:
        raise HTTPException(status_code=400, detail="没有可用于生成草稿的商品")
    available_products = [product for product in products if product.stock > 0]
    if not available_products:
        raise HTTPException(status_code=400, detail="可选商品均无库存，无法生成可提交订单草稿")

    result = await copilot_service.order_draft(customer, available_products, payload.business_goal, selected_by_user=bool(payload.product_ids))
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
        organization_id=current_user.organization_id,
    )
    return result


def matches_report_filters(item, date_field: str, date_from: date | None, date_to: date | None, owner: str, region: str) -> bool:
    item_date = getattr(item, date_field)
    if date_from and item_date < date_from:
        return False
    if date_to and item_date > date_to:
        return False
    if owner and getattr(item, "owner", "") != owner:
        return False
    if region and getattr(item, "region", "") != region:
        return False
    return True


def build_sales_breakdown(orders: list[SalesOrder], leads: list[SalesLead], group_field: str) -> list[SalesReportBreakdown]:
    group_names = {getattr(order, group_field) for order in orders} | {getattr(lead, group_field) for lead in leads}
    breakdowns: list[SalesReportBreakdown] = []
    for name in sorted(group_names):
        group_orders = [order for order in orders if getattr(order, group_field) == name]
        group_leads = [lead for lead in leads if getattr(lead, group_field) == name]
        revenue = sum(order.total_amount for order in group_orders)
        open_leads = [lead for lead in group_leads if lead.stage.value not in {"won", "lost"}]
        breakdowns.append(
            SalesReportBreakdown(
                name=name,
                revenue=revenue,
                order_count=len(group_orders),
                ai_order_count=len([order for order in group_orders if order.created_by_ai]),
                average_order_value=round(revenue / len(group_orders), 2) if group_orders else 0,
                pipeline_amount=sum(lead.expected_amount for lead in open_leads),
                open_leads=len(open_leads),
            )
        )
    return sorted(breakdowns, key=lambda item: (item.revenue, item.pipeline_amount), reverse=True)


def matches_approval_report_filters(
    approval: OrderApprovalRequest,
    orders_by_id: dict[int, SalesOrder],
    date_from: date | None,
    date_to: date | None,
    owner: str,
    region: str,
) -> bool:
    approval_date = approval.created_at.date()
    if date_from and approval_date < date_from:
        return False
    if date_to and approval_date > date_to:
        return False
    if owner and approval.owner != owner:
        return False
    if region:
        order = orders_by_id.get(approval.order_id)
        if not order or order.region != region:
            return False
    return True


@app.get("/api/reports/snapshots", response_model=list[ReportSnapshotRead] | PaginatedResponse[ReportSnapshotRead], dependencies=[Depends(require_permission("reports:read"))])
def list_report_snapshots(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("reports:read"))],
    page: int | None = Query(default=None, ge=1),
    per_page: int | None = Query(default=None, ge=1, le=100),
    report_type: str = "",
    q: str = "",
    limit: int = 12,
) -> list[ReportSnapshotRead] | dict:
    safe_limit = min(max(limit, 1), 80)
    statement = (
        select(ReportSnapshot)
        .where(ReportSnapshot.organization_id == current_user.organization_id)
        .order_by(ReportSnapshot.created_at.desc())
    )
    if page is None and per_page is None and not q.strip() and not report_type.strip():
        statement = statement.limit(safe_limit)
    snapshots = [serialize_report_snapshot(snapshot) for snapshot in session.exec(statement).all()]
    snapshots = filter_records(
        snapshots,
        q=q,
        fields=("title", "summary", "created_by", "report_type_label"),
        report_type=report_type,
    )
    return paginate_or_list(snapshots, page=page, per_page=per_page)


@app.post("/api/reports/snapshots", response_model=ReportSnapshotRead, status_code=201)
def create_report_snapshot(
    payload: ReportSnapshotCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("reports:read"))],
) -> ReportSnapshotRead:
    report_label = REPORT_SNAPSHOT_LABELS[payload.report_type]
    filters = normalize_report_snapshot_filters(payload.filters)
    report_payload = build_report_snapshot_payload(session, payload.report_type, filters, current_user)
    title = payload.title or f"{report_label}快照 {datetime.utcnow().strftime('%m-%d %H:%M')}"
    summary = payload.summary or build_report_snapshot_summary(report_payload, payload.report_type)
    snapshot = ReportSnapshot(
        organization_id=current_user.organization_id,
        report_type=payload.report_type,
        title=summarize_text(title, limit=120),
        filters_json=encode_json_object(filters),
        payload_json=encode_json_object(report_payload),
        summary=summarize_text(summary, limit=500),
        created_by=current_user.full_name,
    )
    session.add(snapshot)
    session.flush()
    add_business_audit(
        session,
        action="create",
        entity_type="report_snapshot",
        entity_id=snapshot.id,
        operator=current_user.full_name,
        summary=f"保存{report_label}报表快照 {snapshot.title}",
        detail=snapshot.summary,
    )
    session.commit()
    session.refresh(snapshot)
    return serialize_report_snapshot(snapshot)


@app.delete("/api/reports/snapshots/{snapshot_id}")
def delete_report_snapshot(
    snapshot_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("reports:read"))],
) -> dict[str, bool | int | str]:
    snapshot = session.get(ReportSnapshot, snapshot_id)
    if not snapshot or snapshot.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="报表快照不存在")
    if snapshot.created_by != current_user.full_name and not has_all_data_scope(current_user):
        raise HTTPException(status_code=403, detail="只能删除自己保存的报表快照")
    title = snapshot.title
    session.delete(snapshot)
    add_business_audit(
        session,
        action="delete",
        entity_type="report_snapshot",
        entity_id=snapshot_id,
        operator=current_user.full_name,
        summary=f"删除报表快照 {title}",
        detail=f"快照 ID {snapshot_id}",
    )
    session.commit()
    return delete_response("report_snapshot", snapshot_id)


@app.get("/api/reports/approval-performance", response_model=ApprovalPerformanceReportResponse)
def get_approval_performance_report(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("reports:read"))],
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    owner: str = "",
    region: str = "",
) -> ApprovalPerformanceReportResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    scoped_orders = filter_by_organization_scope(session.exec(select(SalesOrder)).all(), current_user)
    orders_by_id = {order.id: order for order in scoped_orders if order.id is not None}
    all_approvals = filter_by_organization_scope(
        session.exec(select(OrderApprovalRequest).order_by(OrderApprovalRequest.created_at.desc())).all(),
        current_user,
    )
    approvals = [
        approval
        for approval in all_approvals
        if matches_approval_report_filters(approval, orders_by_id, date_from, date_to, owner, region)
    ]

    now = datetime.utcnow()
    total_count = len(approvals)
    pending_approvals = [approval for approval in approvals if approval.status == OrderApprovalStatus.pending]
    approved_approvals = [approval for approval in approvals if approval.status == OrderApprovalStatus.approved]
    rejected_approvals = [approval for approval in approvals if approval.status == OrderApprovalStatus.rejected]
    overdue_approvals = [approval for approval in pending_approvals if get_order_approval_sla_details(approval, now)[0] == "overdue"]
    high_risk_approvals = [approval for approval in approvals if normalize_order_approval_risk_level(approval.risk_level) in {"critical", "high"}]

    decided_approvals = [approval for approval in approvals if approval.decided_at]
    resolution_hours = [
        max((approval.decided_at - approval.created_at).total_seconds() / 3600, 0)
        for approval in decided_approvals
        if approval.decided_at is not None
    ]
    decision_count = len(approved_approvals) + len(rejected_approvals)
    approval_rate = round(len(approved_approvals) / decision_count * 100) if decision_count else 0
    average_resolution_hours = round(sum(resolution_hours) / len(resolution_hours), 1) if resolution_hours else 0

    metrics = [
        DashboardMetric(label="审批总量", value=str(total_count), hint="按提交时间和筛选条件统计"),
        DashboardMetric(label="待审批", value=str(len(pending_approvals)), hint=f"逾期 {len(overdue_approvals)} 条"),
        DashboardMetric(label="高风险审批", value=str(len(high_risk_approvals)), hint="critical/high 风险等级"),
        DashboardMetric(label="审批通过率", value=f"{approval_rate}%", hint=f"已决策 {decision_count} 条"),
        DashboardMetric(label="平均处理时长", value=f"{average_resolution_hours}h", hint="按已审批记录计算"),
        DashboardMetric(label="SLA 逾期率", value=f"{round(len(overdue_approvals) / len(pending_approvals) * 100) if pending_approvals else 0}%", hint="仅统计待审批记录"),
    ]

    risk_rows = [(key, ORDER_APPROVAL_RISK_LABELS[key]) for key in ("critical", "high", "medium", "low")]
    risk_counts = Counter(normalize_order_approval_risk_level(approval.risk_level) for approval in approvals)
    risk_distribution = [
        ApprovalReportDistributionItem(
            key=key,
            label=label,
            count=risk_counts.get(key, 0),
            share=round(risk_counts.get(key, 0) / total_count, 2) if total_count else 0,
        )
        for key, label in risk_rows
    ]

    sla_counts = Counter(get_order_approval_sla_details(approval, now)[0] for approval in approvals)
    sla_distribution = [
        ApprovalReportDistributionItem(
            key=key,
            label=APPROVAL_SLA_LABELS[key],
            count=sla_counts.get(key, 0),
            share=round(sla_counts.get(key, 0) / total_count, 2) if total_count else 0,
        )
        for key in ("overdue", "due_soon", "on_track", "closed", "unset")
    ]

    status_counts = Counter(approval.status.value for approval in approvals)
    status_distribution = [
        ApprovalReportDistributionItem(
            key=status.value,
            label=APPROVAL_STATUS_LABELS[status.value],
            count=status_counts.get(status.value, 0),
            share=round(status_counts.get(status.value, 0) / total_count, 2) if total_count else 0,
        )
        for status in OrderApprovalStatus
    ]

    reviewer_names = sorted({approval.reviewer or "未指定审批人" for approval in approvals})
    reviewer_workload: list[ApprovalReviewerWorkload] = []
    for reviewer in reviewer_names:
        reviewer_approvals = [approval for approval in approvals if (approval.reviewer or "未指定审批人") == reviewer]
        reviewer_resolution_hours = [
            max((approval.decided_at - approval.created_at).total_seconds() / 3600, 0)
            for approval in reviewer_approvals
            if approval.decided_at is not None
        ]
        reviewer_workload.append(
            ApprovalReviewerWorkload(
                name=reviewer,
                pending_count=len([approval for approval in reviewer_approvals if approval.status == OrderApprovalStatus.pending]),
                approved_count=len([approval for approval in reviewer_approvals if approval.status == OrderApprovalStatus.approved]),
                rejected_count=len([approval for approval in reviewer_approvals if approval.status == OrderApprovalStatus.rejected]),
                overdue_count=len([approval for approval in reviewer_approvals if get_order_approval_sla_details(approval, now)[0] == "overdue"]),
                average_resolution_hours=round(sum(reviewer_resolution_hours) / len(reviewer_resolution_hours), 1) if reviewer_resolution_hours else 0,
            )
        )
    reviewer_workload = sorted(reviewer_workload, key=lambda item: (item.overdue_count, item.pending_count, item.approved_count + item.rejected_count), reverse=True)

    applied_filters = {
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
        "owner": owner,
        "region": region,
    }

    return ApprovalPerformanceReportResponse(
        generated_at=datetime.utcnow(),
        metrics=metrics,
        risk_distribution=risk_distribution,
        sla_distribution=sla_distribution,
        status_distribution=status_distribution,
        reviewer_workload=reviewer_workload,
        recent_approvals=[serialize_order_approval(approval, session) for approval in approvals[:6]],
        applied_filters=applied_filters,
    )


@app.get("/api/reports/sales-performance", response_model=SalesPerformanceReportResponse)
def get_sales_performance_report(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("reports:read"))],
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    owner: str = "",
    region: str = "",
) -> SalesPerformanceReportResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    all_orders = filter_by_organization_scope(session.exec(select(SalesOrder)).all(), current_user)
    all_leads = filter_by_organization_scope(session.exec(select(SalesLead)).all(), current_user)
    orders = [order for order in all_orders if matches_report_filters(order, "order_date", date_from, date_to, owner, region)]
    leads = [lead for lead in all_leads if matches_report_filters(lead, "due_date", date_from, date_to, owner, region)]
    ai_orders = [order for order in orders if order.created_by_ai]
    manual_orders = [order for order in orders if not order.created_by_ai]
    open_leads = [lead for lead in leads if lead.stage.value not in {"won", "lost"}]

    total_revenue = sum(order.total_amount for order in orders)
    ai_revenue = sum(order.total_amount for order in ai_orders)
    manual_revenue = sum(order.total_amount for order in manual_orders)
    pipeline_amount = sum(lead.expected_amount for lead in open_leads)
    won_amount = sum(lead.expected_amount for lead in leads if lead.stage.value == "won")

    metrics = [
        DashboardMetric(label="订单收入", value=f"¥{total_revenue:,.0f}", hint=f"{len(orders)} 张订单"),
        DashboardMetric(label="平均客单价", value=f"¥{(total_revenue / len(orders) if orders else 0):,.0f}", hint="按筛选订单计算"),
        DashboardMetric(label="AI 收入占比", value=f"{round(ai_revenue / total_revenue * 100) if total_revenue else 0}%", hint=f"{len(ai_orders)} 张 AI 订单"),
        DashboardMetric(label="在管商机额", value=f"¥{pipeline_amount:,.0f}", hint=f"{len(open_leads)} 个未关闭商机"),
        DashboardMetric(label="赢单商机额", value=f"¥{won_amount:,.0f}", hint="按商机阶段统计"),
        DashboardMetric(label="库存风险", value=str(len(list_restock_alerts(session, current_user.organization_id))), hint="低库存补货建议项"),
    ]

    revenue_bucket: dict[str, float] = defaultdict(float)
    for order in orders:
        revenue_bucket[order.order_date.strftime("%Y-%m")] += order.total_amount
    revenue_trend = [RevenuePoint(month=month, revenue=amount) for month, amount in sorted(revenue_bucket.items())]

    total_leads = len(leads) or 1
    funnel: list[SalesReportFunnelStage] = []
    for stage, label in REPORT_STAGE_LABELS.items():
        stage_leads = [lead for lead in leads if lead.stage.value == stage]
        funnel.append(
            SalesReportFunnelStage(
                stage=stage,
                label=label,
                lead_count=len(stage_leads),
                expected_amount=sum(lead.expected_amount for lead in stage_leads),
                share=round(len(stage_leads) / total_leads, 2),
            )
        )

    ai_impact = SalesReportAiImpact(
        ai_order_count=len(ai_orders),
        manual_order_count=len(manual_orders),
        ai_revenue=ai_revenue,
        manual_revenue=manual_revenue,
        average_ai_confidence=round(sum(order.ai_confidence_score for order in ai_orders) / len(ai_orders), 2) if ai_orders else 0,
        ai_revenue_ratio=round(ai_revenue / total_revenue, 2) if total_revenue else 0,
    )

    applied_filters = {
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
        "owner": owner,
        "region": region,
    }

    return SalesPerformanceReportResponse(
        generated_at=datetime.utcnow(),
        metrics=metrics,
        revenue_trend=revenue_trend,
        owner_performance=build_sales_breakdown(orders, leads, "owner"),
        region_performance=build_sales_breakdown(orders, leads, "region"),
        funnel=funnel,
        ai_impact=ai_impact,
        inventory_risks=list_restock_alerts(session, current_user.organization_id)[:6],
        applied_filters=applied_filters,
    )


@app.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("dashboard:read"))],
) -> DashboardResponse:
    orders = session.exec(select(SalesOrder)).all()
    leads = session.exec(select(SalesLead)).all()
    customers = session.exec(select(Customer)).all()
    orders = filter_by_organization_scope(orders, current_user)
    leads = filter_by_organization_scope(leads, current_user)
    customers = filter_by_organization_scope(customers, current_user)
    orders = filter_by_owner_scope(orders, current_user)
    leads = filter_by_owner_scope(leads, current_user)
    customers = filter_by_owner_scope(customers, current_user)

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
