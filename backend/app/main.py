from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .config import settings
from .database import create_db_and_tables, engine, get_session
from .models import AIInteractionLog, Contact, Customer, InventoryMovement, OrderItem, Product, SalesGoal, SalesLead, SalesOrder, SupportCase, TaskItem
from .schemas import (
    AIInteractionLogRead,
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
    ProductRestockRequest,
    ProductRestockResponse,
    ProductRead,
    RevenuePoint,
    SalesGoalCreate,
    SalesGoalRead,
    SalesGoalUpdate,
    SalesLeadCreate,
    SalesLeadUpdate,
    SalesOrderCreate,
    SalesOrderRead,
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
RESTOCK_DANGER_THRESHOLD = 80
RESTOCK_WARNING_THRESHOLD = 300
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


@app.get("/api/customers", response_model=list[CustomerRead])
def list_customers(session: SessionDep) -> list[Customer]:
    return session.exec(select(Customer).order_by(Customer.created_at.desc())).all()


@app.post("/api/customers", response_model=CustomerRead, status_code=201)
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
    session.commit()
    session.refresh(customer)
    return customer


@app.patch("/api/customers/{customer_id}", response_model=CustomerRead)
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
    session.commit()
    session.refresh(customer)
    return customer


@app.delete("/api/customers/{customer_id}")
def delete_customer(customer_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    order = session.exec(select(SalesOrder).where(SalesOrder.customer_id == customer_id)).first()
    if order:
        raise HTTPException(status_code=400, detail="客户已有订单，不能直接删除")
    session.delete(customer)
    session.commit()
    return delete_response("customer", customer_id)


@app.get("/api/products", response_model=list[ProductRead])
def list_products(session: SessionDep) -> list[Product]:
    return session.exec(select(Product).order_by(Product.created_at.desc())).all()


@app.get("/api/inventory/restock-alerts", response_model=list[InventoryRestockAlertRead])
def get_restock_alerts(session: SessionDep) -> list[InventoryRestockAlertRead]:
    return list_restock_alerts(session)


@app.get("/api/inventory/movements", response_model=list[InventoryMovementRead])
def get_inventory_movements(session: SessionDep, limit: int = 30) -> list[InventoryMovementRead]:
    safe_limit = min(max(limit, 1), 100)
    movements = session.exec(select(InventoryMovement).order_by(InventoryMovement.created_at.desc()).limit(safe_limit)).all()
    return [serialize_inventory_movement(movement, session) for movement in movements]


@app.post("/api/products/{product_id}/restock", response_model=ProductRestockResponse)
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
    session.commit()
    session.refresh(product)
    session.refresh(movement)
    return ProductRestockResponse(
        product=product,
        movement=serialize_inventory_movement(movement, session),
        alert=build_restock_alert(product, session),
    )


@app.get("/api/contacts", response_model=list[ContactRead])
def list_contacts(session: SessionDep) -> list[Contact]:
    return session.exec(select(Contact).order_by(Contact.created_at.desc())).all()


@app.post("/api/contacts", response_model=ContactRead, status_code=201)
def create_contact(payload: ContactCreate, session: SessionDep) -> Contact:
    contact = Contact(**payload.model_dump())
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


@app.patch("/api/contacts/{contact_id}", response_model=ContactRead)
def update_contact(contact_id: int, payload: ContactUpdate, session: SessionDep) -> Contact:
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")
    apply_updates(contact, patch_values(payload))
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


@app.delete("/api/contacts/{contact_id}")
def delete_contact(contact_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="联系人不存在")
    session.delete(contact)
    session.commit()
    return delete_response("contact", contact_id)


@app.get("/api/leads", response_model=list[LeadRead])
def list_leads(session: SessionDep) -> list[SalesLead]:
    return session.exec(select(SalesLead).order_by(SalesLead.due_date.asc())).all()


@app.post("/api/leads", response_model=LeadRead, status_code=201)
def create_lead(payload: SalesLeadCreate, session: SessionDep) -> SalesLead:
    lead = SalesLead(**payload.model_dump())
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


@app.patch("/api/leads/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: int, payload: SalesLeadUpdate, session: SessionDep) -> SalesLead:
    lead = session.get(SalesLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="商机不存在")
    apply_updates(lead, patch_values(payload))
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


@app.delete("/api/leads/{lead_id}")
def delete_lead(lead_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    lead = session.get(SalesLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="商机不存在")
    session.delete(lead)
    session.commit()
    return delete_response("lead", lead_id)


@app.get("/api/cases", response_model=list[SupportCaseRead])
def list_cases(session: SessionDep) -> list[SupportCase]:
    return session.exec(select(SupportCase).order_by(SupportCase.due_date.asc())).all()


@app.post("/api/cases", response_model=SupportCaseRead, status_code=201)
def create_case(payload: SupportCaseCreate, session: SessionDep) -> SupportCase:
    support_case = SupportCase(**payload.model_dump())
    session.add(support_case)
    session.commit()
    session.refresh(support_case)
    return support_case


@app.patch("/api/cases/{case_id}", response_model=SupportCaseRead)
def update_case(case_id: int, payload: SupportCaseUpdate, session: SessionDep) -> SupportCase:
    support_case = session.get(SupportCase, case_id)
    if not support_case:
        raise HTTPException(status_code=404, detail="工单不存在")
    apply_updates(support_case, patch_values(payload))
    session.add(support_case)
    session.commit()
    session.refresh(support_case)
    return support_case


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    support_case = session.get(SupportCase, case_id)
    if not support_case:
        raise HTTPException(status_code=404, detail="工单不存在")
    session.delete(support_case)
    session.commit()
    return delete_response("case", case_id)


@app.get("/api/tasks", response_model=list[TaskItemRead])
def list_tasks(session: SessionDep) -> list[TaskItem]:
    return session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()


@app.post("/api/tasks", response_model=TaskItemRead, status_code=201)
def create_task(payload: TaskItemCreate, session: SessionDep) -> TaskItem:
    task = TaskItem(**payload.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}", response_model=TaskItemRead)
def update_task(task_id: int, payload: TaskItemUpdate, session: SessionDep) -> TaskItem:
    task = session.get(TaskItem, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    apply_updates(task, patch_values(payload))
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    task = session.get(TaskItem, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    session.delete(task)
    session.commit()
    return delete_response("task", task_id)


@app.get("/api/goals", response_model=list[SalesGoalRead])
def list_goals(session: SessionDep) -> list[SalesGoal]:
    return session.exec(select(SalesGoal).order_by(SalesGoal.created_at.desc())).all()


@app.post("/api/goals", response_model=SalesGoalRead, status_code=201)
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
    session.commit()
    session.refresh(goal)
    return goal


@app.patch("/api/goals/{goal_id}", response_model=SalesGoalRead)
def update_goal(goal_id: int, payload: SalesGoalUpdate, session: SessionDep) -> SalesGoal:
    goal = session.get(SalesGoal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")
    updates = patch_values(payload)
    apply_updates(goal, updates)
    if "progress" not in updates and goal.target:
        goal.progress = min(max(round(goal.current / goal.target * 100), 0), 100)
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: int, session: SessionDep) -> dict[str, bool | int | str]:
    goal = session.get(SalesGoal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")
    session.delete(goal)
    session.commit()
    return delete_response("goal", goal_id)


@app.get("/api/ai-audit-logs", response_model=list[AIInteractionLogRead])
def list_ai_audit_logs(session: SessionDep, limit: int = 30) -> list[AIInteractionLog]:
    safe_limit = min(max(limit, 1), 100)
    return session.exec(select(AIInteractionLog).order_by(AIInteractionLog.created_at.desc()).limit(safe_limit)).all()


@app.get("/api/orders", response_model=list[SalesOrderRead])
def list_orders(session: SessionDep) -> list[SalesOrderRead]:
    orders = session.exec(select(SalesOrder).order_by(SalesOrder.created_at.desc())).all()
    return [serialize_order(order, session) for order in orders]


@app.post("/api/orders", response_model=SalesOrderRead, status_code=201)
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
    session.commit()
    session.refresh(order)
    return serialize_order(order, session)


@app.post("/api/vision-extract", response_model=VisionExtractResponse)
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


@app.post("/api/copilot/follow-up", response_model=CopilotFollowUpResponse)
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


@app.post("/api/copilot/order-draft", response_model=CopilotOrderDraftResponse)
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


@app.get("/api/dashboard", response_model=DashboardResponse)
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
