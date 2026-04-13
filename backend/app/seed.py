from __future__ import annotations

from datetime import date, timedelta

from sqlmodel import Session, select

from .models import Customer, LeadStage, OrderItem, OrderStatus, Product, SalesLead, SalesOrder


def seed_data(session: Session) -> None:
    existing_customer = session.exec(select(Customer)).first()
    if existing_customer:
        return

    customers = [
        Customer(
            name="李强",
            company="星海装备",
            industry="工业制造",
            city="上海",
            contact_person="李强",
            phone="13800001111",
            email="liqiang@xinghai.com",
            source="展会",
            level="A",
        ),
        Customer(
            name="陈敏",
            company="云川医疗",
            industry="医疗器械",
            city="杭州",
            contact_person="陈敏",
            phone="13900002222",
            email="chenmin@yunchuan.com",
            source="老客户转介绍",
            level="S",
        ),
        Customer(
            name="王凯",
            company="北辰教育科技",
            industry="教育信息化",
            city="深圳",
            contact_person="王凯",
            phone="13700003333",
            email="wangkai@beichen.com",
            source="官网咨询",
            level="B",
        ),
    ]
    session.add_all(customers)
    session.flush()

    products = [
        Product(name="智能巡检终端", sku="AI-DEVICE-001", category="硬件", unit_price=16800, stock=42),
        Product(name="销售分析大屏授权", sku="SAAS-LIC-008", category="软件", unit_price=6800, stock=999),
        Product(name="客户数据接入服务", sku="SERV-API-003", category="服务", unit_price=4200, stock=200),
        Product(name="移动录单套件", sku="MOBILE-KIT-011", category="硬件", unit_price=9800, stock=35),
    ]
    session.add_all(products)
    session.flush()

    today = date.today()
    leads = [
        SalesLead(
            title="校企合作采购项目",
            customer_name="北辰教育科技",
            owner="李伟超",
            region="华南",
            expected_amount=120000,
            stage=LeadStage.proposal,
            next_action="提交最终报价单",
            due_date=today + timedelta(days=2),
            ai_assisted=True,
        ),
        SalesLead(
            title="医院智能终端补货",
            customer_name="云川医疗",
            owner="王晨",
            region="华东",
            expected_amount=86000,
            stage=LeadStage.negotiation,
            next_action="确认交付周期",
            due_date=today + timedelta(days=1),
            ai_assisted=False,
        ),
        SalesLead(
            title="工业现场改造一期",
            customer_name="星海装备",
            owner="李伟超",
            region="华东",
            expected_amount=152000,
            stage=LeadStage.qualified,
            next_action="安排现场勘查",
            due_date=today + timedelta(days=4),
            ai_assisted=True,
        ),
    ]
    session.add_all(leads)
    session.flush()

    orders = [
        SalesOrder(
            customer_id=customers[1].id,
            owner="李伟超",
            region="华东",
            currency="CNY",
            status=OrderStatus.confirmed,
            order_date=today - timedelta(days=6),
            due_date=today + timedelta(days=6),
            notes="由 AI 从微信截图辅助生成，人工复核后提交。",
            created_by_ai=True,
            ai_confidence_score=0.93,
            total_amount=40400,
        ),
        SalesOrder(
            customer_id=customers[0].id,
            owner="王晨",
            region="华东",
            currency="CNY",
            status=OrderStatus.fulfilled,
            order_date=today - timedelta(days=15),
            due_date=today - timedelta(days=1),
            notes="传统手工录入订单。",
            created_by_ai=False,
            ai_confidence_score=0.0,
            total_amount=16800,
        ),
    ]
    session.add_all(orders)
    session.flush()

    items = [
        OrderItem(order_id=orders[0].id, product_id=products[0].id, quantity=2, unit_price=16800, line_total=33600),
        OrderItem(order_id=orders[0].id, product_id=products[2].id, quantity=1, unit_price=6800, line_total=6800),
        OrderItem(order_id=orders[1].id, product_id=products[0].id, quantity=1, unit_price=16800, line_total=16800),
    ]
    session.add_all(items)
    session.commit()
