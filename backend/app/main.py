from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .config import settings
from .database import create_db_and_tables, engine, get_session
from .models import Contact, Customer, OrderItem, Product, SalesGoal, SalesLead, SalesOrder, SupportCase, TaskItem
from .schemas import (
    ContactRead,
    CopilotFollowUpRequest,
    CopilotFollowUpResponse,
    CopilotOrderDraftRequest,
    CopilotOrderDraftResponse,
    CopilotSummaryResponse,
    CustomerRead,
    DashboardMetric,
    DashboardResponse,
    LeadRead,
    OrderItemRead,
    ProductRead,
    RevenuePoint,
    SalesGoalRead,
    SalesOrderCreate,
    SalesOrderRead,
    SupportCaseRead,
    TaskItemRead,
    VisionExtractResponse,
)
from .seed import seed_data
from .services import CopilotService, VisionExtractionService


vision_service = VisionExtractionService()
copilot_service = CopilotService()
SessionDep = Annotated[Session, Depends(get_session)]


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


@app.get("/api/products", response_model=list[ProductRead])
def list_products(session: SessionDep) -> list[Product]:
    return session.exec(select(Product).order_by(Product.created_at.desc())).all()


@app.get("/api/contacts", response_model=list[ContactRead])
def list_contacts(session: SessionDep) -> list[Contact]:
    return session.exec(select(Contact).order_by(Contact.created_at.desc())).all()


@app.get("/api/leads", response_model=list[LeadRead])
def list_leads(session: SessionDep) -> list[SalesLead]:
    return session.exec(select(SalesLead).order_by(SalesLead.due_date.asc())).all()


@app.get("/api/cases", response_model=list[SupportCaseRead])
def list_cases(session: SessionDep) -> list[SupportCase]:
    return session.exec(select(SupportCase).order_by(SupportCase.due_date.asc())).all()


@app.get("/api/tasks", response_model=list[TaskItemRead])
def list_tasks(session: SessionDep) -> list[TaskItem]:
    return session.exec(select(TaskItem).order_by(TaskItem.created_at.desc())).all()


@app.get("/api/goals", response_model=list[SalesGoalRead])
def list_goals(session: SessionDep) -> list[SalesGoal]:
    return session.exec(select(SalesGoal).order_by(SalesGoal.created_at.desc())).all()


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
        product.stock = max(product.stock - item.quantity, 0)
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
    session.commit()
    session.refresh(order)
    return serialize_order(order, session)


@app.post("/api/vision-extract", response_model=VisionExtractResponse)
async def vision_extract(file: Annotated[UploadFile, File(...)], session: SessionDep) -> VisionExtractResponse:
    customers = session.exec(select(Customer)).all()
    products = session.exec(select(Product)).all()
    return await vision_service.extract(file, customers=customers, products=products)


@app.get("/api/copilot/summary", response_model=CopilotSummaryResponse)
async def copilot_summary(session: SessionDep) -> CopilotSummaryResponse:
    leads = session.exec(select(SalesLead).order_by(SalesLead.due_date.asc())).all()
    return await copilot_service.summarize(leads)


@app.post("/api/copilot/follow-up", response_model=CopilotFollowUpResponse)
async def copilot_follow_up(payload: CopilotFollowUpRequest, session: SessionDep) -> CopilotFollowUpResponse:
    lead = session.get(SalesLead, payload.lead_id) if payload.lead_id else None
    if payload.lead_id and not lead:
        raise HTTPException(status_code=404, detail="商机不存在")
    return await copilot_service.follow_up(payload, lead)


@app.post("/api/copilot/order-draft", response_model=CopilotOrderDraftResponse)
async def copilot_order_draft(payload: CopilotOrderDraftRequest, session: SessionDep) -> CopilotOrderDraftResponse:
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

    return await copilot_service.order_draft(customer, products, payload.business_goal)


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
