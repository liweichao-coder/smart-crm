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
from .database import create_db_and_tables, engine, get_session
from .models import AIInteractionLog, AuthAuditLog, AuthSession, AuthUser, BusinessAuditLog, Contact, CopilotRecommendation, Customer, InventoryMovement, LeadStage, OrderApprovalRequest, OrderApprovalStatus, OrderItem, Organization, Product, SalesGoal, SalesLead, SalesOrder, SupportCase, TaskItem
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
    CopilotRecommendationRead,
    CopilotSummaryResponse,
    CustomerCreate,
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
    OrderApprovalCreate,
    OrderApprovalDecision,
    OrderApprovalRead,
    NotificationRead,
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
}
ROLE_PERMISSIONS = {
    "管理员": {ALL_PERMISSIONS},
    "销售": {"crm:read", "crm:write", "order:manage", "ai:use", "dashboard:read"},
    "销售经理": {"crm:read", "crm:write", "order:manage", "approval:manage", "ai:use", "dashboard:read", "reports:read", "audit:read", "permissions:read"},
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
    "crm:read": ("CRM", "CRM 数据读取", "查看客户、联系人、线索、工单、任务和目标。"),
    "crm:write": ("CRM", "CRM 数据维护", "创建、编辑和删除客户、联系人、线索、工单、任务和目标。"),
    "dashboard:read": ("BI", "仪表盘查看", "查看经营仪表盘和首页概览。"),
    "inventory:manage": ("库存", "库存补货", "执行商品补货并写入库存流水。"),
    "order:manage": ("订单", "订单管理", "创建、编辑、导出订单并查看订单库存审计。"),
    "permissions:read": ("权限", "权限矩阵查看", "查看角色、权限和模块访问矩阵。"),
    "reports:read": ("BI", "销售报表查看", "查看销售 BI 报表和聚合指标。"),
}
MODULE_PERMISSIONS = [
    ("/dashboard", "仪表盘", "dashboard:read"),
    ("/reports", "销售报表", "reports:read"),
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


def data_scope_for_role(role: str) -> str:
    return "own" if role in OWN_DATA_SCOPE_ROLES else "all"


def has_all_data_scope(user: AuthUser) -> bool:
    return data_scope_for_role(user.role) == "all"


def owner_matches_user(owner: str, user: AuthUser) -> bool:
    return normalize_account(owner) == normalize_account(user.full_name)


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
        created_at=recommendation.created_at,
    )


def add_copilot_summary_history(session: Session, result: CopilotSummaryResponse) -> None:
    for insight in result.insights[:5]:
        session.add(
            CopilotRecommendation(
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
        title=title,
        description=summarize_text("\n".join(description_parts), limit=900),
        owner=recommendation.owner or "李伟超",
        due_date=due_date,
        priority=priority,
        status=status,
        status_label=status_label,
    )


def find_task_for_copilot_recommendation(session: Session, recommendation_id: int) -> TaskItem | None:
    marker = f"CopilotRecommendation#{recommendation_id}"
    tasks = session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()
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


def collect_notifications(session: Session, current_user: AuthUser, limit: int = 20) -> list[NotificationRead]:
    notifications: list[NotificationRead] = []
    today = date.today()

    tasks = session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()
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

    for alert in list_restock_alerts(session)[:5]:
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
    approvals = filter_by_owner_scope(approvals, current_user)[:6]
    for approval in approvals:
        notifications.append(
            make_notification(
                notification_id=f"order-approval-{approval.id}",
                category="审批",
                severity="warning" if approval.requested_total >= 100000 else "info",
                title=f"订单审批：#{approval.order_id}",
                message=f"{approval.owner} 提交，金额 {approval.requested_total:.0f} 元，待 {approval.reviewer or '销售经理'} 处理。",
                href="/orders",
                action_label="查看审批",
                entity_type="order_approval",
                entity_id=approval.id,
                created_at=approval.created_at,
            )
        )

    leads = session.exec(select(SalesLead).order_by(SalesLead.due_date.asc(), SalesLead.expected_amount.desc())).all()
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
    recommendations = filter_by_owner_scope(recommendations, current_user)[:8]
    for recommendation in recommendations:
        if recommendation.id and find_task_for_copilot_recommendation(session, recommendation.id):
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

    fallback_logs = session.exec(select(AIInteractionLog).where(AIInteractionLog.fallback_used == True).order_by(AIInteractionLog.created_at.desc()).limit(3)).all()  # noqa: E712
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
    return notifications[: max(1, min(limit, 50))]


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


def customer_aliases(customer: Customer) -> set[str]:
    return {value for value in {customer.company, customer.name, customer.contact_person} if value}


def build_customer_workspace_metrics(
    contacts: list[Contact],
    leads: list[SalesLead],
    orders: list[SalesOrder],
    cases: list[SupportCase],
) -> list[DashboardMetric]:
    open_leads = [lead for lead in leads if lead.stage not in {LeadStage.won, LeadStage.lost}]
    active_cases = [support_case for support_case in cases if support_case.status not in {"resolved", "closed"}]
    total_revenue = sum(order.total_amount for order in orders)
    pipeline_amount = sum(lead.expected_amount for lead in open_leads)
    health_score = round(
        max(
            0,
            min(
                100,
                50
                + min(total_revenue / 50000, 20)
                + min(pipeline_amount / 50000, 20)
                + min(len(contacts) * 3, 12)
                - len(active_cases) * 8,
            ),
        )
    )

    return [
        DashboardMetric(label="客户健康分", value=str(health_score), hint="由收入、管道、联系人和服务风险综合计算"),
        DashboardMetric(label="累计收入", value=f"{total_revenue:.0f}", hint=f"{len(orders)} 张订单"),
        DashboardMetric(label="在管商机", value=f"{pipeline_amount:.0f}", hint=f"{len(open_leads)} 个未关闭机会"),
        DashboardMetric(label="服务风险", value=str(len(active_cases)), hint="未关闭工单数量"),
    ]


def build_customer_timeline(
    customer: Customer,
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


def build_order_approval_risk_summary(order: SalesOrder) -> str:
    risk_flags: list[str] = []
    if order.total_amount >= 100000:
        risk_flags.append(f"订单金额 {order.total_amount:.0f} 元，建议经理复核商务条款")
    if order.created_by_ai:
        risk_flags.append("订单由 AI 智能录单生成，需要确认客户、商品和数量")
        if order.ai_confidence_score < 0.85:
            risk_flags.append(f"AI 置信度 {order.ai_confidence_score:.0%}，建议人工复核原始材料")
    days_to_delivery = (order.due_date - date.today()).days
    if days_to_delivery <= 7:
        risk_flags.append(f"交付窗口 {days_to_delivery} 天，需确认库存和实施排期")
    if order.status != "draft":
        risk_flags.append(f"当前订单状态为 {order.status.value}，审批后将推进到目标状态")
    return "；".join(risk_flags) or "订单金额、交付周期和 AI 置信度均未触发高风险规则。"


def serialize_order_approval(approval: OrderApprovalRequest, session: Session) -> OrderApprovalRead:
    order = session.get(SalesOrder, approval.order_id)
    customer = session.get(Customer, order.customer_id) if order else None
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
        requested_total=approval.requested_total,
        previous_order_status=approval.previous_order_status,
        target_order_status=approval.target_order_status,
        decision_comment=approval.decision_comment,
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


@app.get("/api/notifications", response_model=list[NotificationRead])
def list_notifications(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("dashboard:read"))],
    limit: int = Query(default=20, ge=1, le=50),
) -> list[NotificationRead]:
    return collect_notifications(session, current_user=current_user, limit=limit)


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
    if not customer:
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
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)
    order = session.exec(select(SalesOrder).where(SalesOrder.customer_id == customer_id)).first()
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


@app.get("/api/customers/{customer_id}/workspace", response_model=CustomerWorkspaceResponse)
async def get_customer_workspace(
    customer_id: int,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("crm:read"))],
) -> CustomerWorkspaceResponse:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)

    aliases = customer_aliases(customer)
    contacts = [
        contact
        for contact in session.exec(select(Contact).order_by(Contact.created_at.desc())).all()
        if contact.company in aliases
    ]
    contacts = filter_by_owner_scope(contacts, current_user)

    leads = [
        lead
        for lead in session.exec(select(SalesLead).order_by(SalesLead.created_at.desc())).all()
        if lead.customer_name in aliases
    ]
    leads = filter_by_owner_scope(leads, current_user)

    orders = session.exec(select(SalesOrder).where(SalesOrder.customer_id == customer.id).order_by(SalesOrder.created_at.desc())).all()
    orders = filter_by_owner_scope(orders, current_user)

    cases = [
        support_case
        for support_case in session.exec(select(SupportCase).order_by(SupportCase.created_at.desc())).all()
        if support_case.account in aliases
    ]
    cases = filter_by_owner_scope(cases, current_user)

    recommendations = [
        recommendation
        for recommendation in session.exec(select(CopilotRecommendation).order_by(CopilotRecommendation.created_at.desc())).all()
        if recommendation.customer_name in aliases
    ]
    recommendations = filter_by_owner_scope(recommendations, current_user)

    start_time = perf_counter()
    account_plan = await copilot_service.account_plan(customer, contacts, leads, orders, cases, recommendations)
    save_ai_interaction(
        session,
        operation="customer_account_plan",
        model=account_plan.model,
        fallback_used=account_plan.fallback_used,
        start_time=start_time,
        request_summary=f"{customer.company} / {len(contacts)} contacts / {len(leads)} leads / {len(orders)} orders",
        response_summary=account_plan.summary,
        entity_type="customer",
        entity_id=customer.id,
    )

    return CustomerWorkspaceResponse(
        customer=customer,
        metrics=build_customer_workspace_metrics(contacts, leads, orders, cases),
        contacts=contacts,
        leads=leads,
        orders=[serialize_order(order, session) for order in orders],
        cases=cases,
        recommendations=[serialize_copilot_recommendation(recommendation) for recommendation in recommendations[:8]],
        timeline=build_customer_timeline(customer, leads, orders, cases, recommendations),
        account_plan=account_plan,
    )


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
    contact = Contact(**{**payload.model_dump(), "owner": owner})
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
    if not contact:
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
    if not contact:
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
    lead = SalesLead(**{**payload.model_dump(), "owner": owner})
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
    if not lead:
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
    if not lead:
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
    support_case = SupportCase(**{**payload.model_dump(), "owner": owner})
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
    if not support_case:
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
    if not support_case:
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
    task = TaskItem(**{**payload.model_dump(), "owner": owner})
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
    if not task:
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
    if not task:
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
) -> list[OrderApprovalRead] | dict:
    approvals = session.exec(select(OrderApprovalRequest).order_by(OrderApprovalRequest.created_at.desc())).all()
    approvals = filter_by_owner_scope(approvals, current_user)
    serialized_approvals = [serialize_order_approval(approval, session) for approval in approvals]
    serialized_approvals = filter_records(
        serialized_approvals,
        q=q,
        fields=("customer_name", "owner", "requester", "reviewer", "status", "reason", "risk_summary", "decision_comment"),
        owner=owner,
        status=status,
        reviewer=reviewer,
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
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    require_owner_scope(current_user, order.owner)
    if order.status == "fulfilled":
        raise HTTPException(status_code=400, detail="已履约订单不需要提交审批")
    if payload.target_order_status == order.status:
        raise HTTPException(status_code=400, detail="目标状态与当前订单状态一致")
    if find_pending_order_approval(session, order_id):
        raise HTTPException(status_code=400, detail="该订单已有待审批申请")

    reason = payload.reason.strip() or "订单确认前需要经理复核商务条款、库存和交付风险。"
    approval = OrderApprovalRequest(
        order_id=order.id or order_id,
        owner=order.owner,
        requester=current_user.full_name,
        reviewer=payload.reviewer.strip() or "销售经理",
        status=OrderApprovalStatus.pending,
        reason=summarize_text(reason, limit=360),
        risk_summary=summarize_text(build_order_approval_risk_summary(order), limit=500),
        requested_total=order.total_amount,
        previous_order_status=order.status,
        target_order_status=payload.target_order_status,
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
        detail=f"目标状态 {payload.target_order_status.value}；{approval.risk_summary}",
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
    if not approval:
        raise HTTPException(status_code=404, detail="审批申请不存在")
    if approval.status != OrderApprovalStatus.pending:
        raise HTTPException(status_code=400, detail="审批申请已处理")
    order = session.get(SalesOrder, approval.order_id)
    if not order:
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
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    require_owner_scope(current_user, order.owner)
    order_marker = f"订单 #{order_id} "
    movements = session.exec(
        select(InventoryMovement)
        .where(InventoryMovement.reason.contains(order_marker))
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
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    require_owner_scope(current_user, order.owner)
    before_total = order.total_amount
    updates = payload.model_dump(exclude_unset=True, exclude_none=True, exclude={"items"})
    if "owner" in updates:
        updates["owner"] = normalize_payload_owner(updates["owner"], current_user)
        require_payload_owner_scope(current_user, updates["owner"])
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


@app.post("/api/orders", response_model=SalesOrderRead, status_code=201)
def create_order(
    payload: SalesOrderCreate,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("order:manage"))],
) -> SalesOrderRead:
    owner = normalize_payload_owner(payload.owner, current_user)
    require_payload_owner_scope(current_user, owner)
    customer = session.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)

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


@app.get("/api/copilot/summary", response_model=CopilotSummaryResponse)
async def copilot_summary(
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> CopilotSummaryResponse:
    start_time = perf_counter()
    leads = session.exec(select(SalesLead).order_by(SalesLead.due_date.asc())).all()
    leads = filter_by_owner_scope(leads, current_user)
    result = await copilot_service.summarize(leads)
    add_copilot_summary_history(session, result)
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
    recommendations = [serialize_copilot_recommendation(item) for item in session.exec(statement).all()]
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
    if not recommendation:
        raise HTTPException(status_code=404, detail="Copilot 推荐不存在")
    require_owner_scope(current_user, recommendation.owner)

    existing_task = find_task_for_copilot_recommendation(session, recommendation_id)
    if existing_task:
        require_owner_scope(current_user, existing_task.owner)
        return existing_task

    task = build_copilot_task(recommendation)
    session.add(task)
    session.flush()

    lead = session.get(SalesLead, recommendation.lead_id) if recommendation.lead_id else None
    if lead and recommendation.next_best_action:
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
    if payload.lead_id and not lead:
        raise HTTPException(status_code=404, detail="商机不存在")
    if lead:
        require_owner_scope(current_user, lead.owner)
    result = await copilot_service.follow_up(payload, lead)
    add_copilot_follow_up_history(session, payload, result, lead)
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


@app.post("/api/copilot/order-draft", response_model=CopilotOrderDraftResponse)
async def copilot_order_draft(
    payload: CopilotOrderDraftRequest,
    session: SessionDep,
    current_user: Annotated[AuthUser, Depends(require_permission("ai:use"))],
) -> CopilotOrderDraftResponse:
    start_time = perf_counter()
    customer = session.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    require_owner_scope(current_user, customer.owner)

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


@app.get("/api/reports/sales-performance", response_model=SalesPerformanceReportResponse, dependencies=[Depends(require_permission("reports:read"))])
def get_sales_performance_report(
    session: SessionDep,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    owner: str = "",
    region: str = "",
) -> SalesPerformanceReportResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    all_orders = session.exec(select(SalesOrder)).all()
    all_leads = session.exec(select(SalesLead)).all()
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
        DashboardMetric(label="库存风险", value=str(len(list_restock_alerts(session))), hint="低库存补货建议项"),
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
        inventory_risks=list_restock_alerts(session)[:6],
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
