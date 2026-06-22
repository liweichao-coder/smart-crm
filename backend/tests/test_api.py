from collections import Counter

import pytest
from fastapi.testclient import TestClient as FastAPITestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app import database
from app.config import settings
import app.main as main_module
from app.models import AuthUser
from app.seed import seed_data


app = main_module.app


class TestClient(FastAPITestClient):
    def __init__(self, *args, auth: bool = True, **kwargs):
        self._auto_auth = auth
        super().__init__(*args, **kwargs)

    def __enter__(self):
        client = super().__enter__()
        if self._auto_auth:
            login = client.post("/api/auth/login", json={"account": "demo@smart-crm.local", "password": "SmartCRM@2026"})
            assert login.status_code == 200
            client.headers.update({"Authorization": f"Bearer {login.json()['token']}"})
        return client


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(main_module, "engine", test_engine)
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        seed_data(session)

    yield

    SQLModel.metadata.drop_all(test_engine)


def test_health_check() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_payload() -> None:
    with TestClient(app) as client:
        response = client.get("/api/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"]
    assert "ai_orders_ratio" in payload


def test_notifications_are_data_driven(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        response = client.get("/api/notifications")
        client.get("/api/copilot/summary")
        copilot_response = client.get("/api/notifications?limit=50")

    assert response.status_code == 200
    notifications = response.json()
    assert notifications
    categories = {item["category"] for item in notifications}
    assert {"任务", "库存", "商机"} <= categories
    assert all(item["href"].startswith("/") for item in notifications)
    assert any(item["severity"] == "critical" for item in notifications)

    assert copilot_response.status_code == 200
    copilot_notifications = copilot_response.json()
    assert any(item["entity_type"] == "copilot_recommendation" for item in copilot_notifications)
    assert any(item["entity_type"] == "ai_interaction" and item["severity"] == "warning" for item in copilot_notifications)


def test_sales_performance_report_payload_and_filters() -> None:
    with TestClient(app) as client:
        response = client.get("/api/reports/sales-performance")
        filtered = client.get("/api/reports/sales-performance?owner=李伟超&region=华南")
        invalid_range = client.get("/api/reports/sales-performance?date_from=2026-07-01&date_to=2026-06-01")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["metrics"]) == 6
    assert payload["owner_performance"]
    assert payload["region_performance"]
    assert {stage["stage"] for stage in payload["funnel"]} == {"new", "qualified", "proposal", "negotiation", "won", "lost"}
    assert payload["ai_impact"]["ai_order_count"] > 0
    assert payload["ai_impact"]["ai_revenue"] > 0
    assert payload["inventory_risks"]

    assert filtered.status_code == 200
    filtered_payload = filtered.json()
    assert filtered_payload["applied_filters"]["owner"] == "李伟超"
    assert filtered_payload["applied_filters"]["region"] == "华南"
    assert all(row["name"] == "李伟超" for row in filtered_payload["owner_performance"])
    assert all(row["name"] == "华南" for row in filtered_payload["region_performance"])

    assert invalid_range.status_code == 400
    assert "开始日期" in invalid_range.json()["detail"]


def test_permission_matrix_payload() -> None:
    with TestClient(app) as client:
        response = client.get("/api/admin/permission-matrix")

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_role"] == "管理员"
    permission_keys = {item["key"] for item in payload["permission_catalog"]}
    assert {"crm:read", "reports:read", "permissions:read"} <= permission_keys

    roles = {role["role"]: role for role in payload["roles"]}
    assert roles["管理员"]["all_permissions"] is True
    assert "permissions:read" in roles["销售经理"]["permissions"]
    assert "catalog:manage" not in roles["销售"]["permissions"]

    modules = {module["path"]: module for module in payload["modules"]}
    assert modules["/permissions"]["permission"] == "permissions:read"
    assert "销售" not in modules["/permissions"]["roles"]
    assert "管理员" in modules["/permissions"]["roles"]


def test_resource_collection_payloads() -> None:
    endpoints = {
        "/api/customers": "company",
        "/api/products": "sku",
        "/api/contacts": "company",
        "/api/leads": "customer_name",
        "/api/cases": "status_label",
        "/api/tasks": "status_label",
        "/api/goals": "progress",
    }

    with TestClient(app) as client:
        responses = {path: client.get(path) for path in endpoints}

    for path, required_key in endpoints.items():
        assert responses[path].status_code == 200
        payload = responses[path].json()
        assert payload
        assert required_key in payload[0]


def test_auth_login_me_logout_and_audit() -> None:
    with TestClient(app) as client:
        failed_login = client.post("/api/auth/login", json={"account": "demo@smart-crm.local", "password": "wrong"})
        login = client.post("/api/auth/login", json={"account": "demo@smart-crm.local", "password": "SmartCRM@2026"})
        token = login.json()["token"]
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        audit_logs = client.get("/api/auth/audit-logs?page=1&per_page=5&event=login").json()
        logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        revoked_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert failed_login.status_code == 401
    assert login.status_code == 200
    payload = login.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "demo@smart-crm.local"
    assert payload["organizations"][0]["name"] == "深大 AI CRM 课程组"
    assert me.status_code == 200
    assert me.json()["user"]["role"] == "管理员"
    assert audit_logs["total"] >= 2
    statuses = {item["status"] for item in audit_logs["items"]}
    assert {"success", "failed"} <= statuses
    assert logout.status_code == 200
    assert logout.json()["revoked"] is True
    assert revoked_me.status_code == 401


def test_auth_register_new_workspace() -> None:
    register_payload = {
        "organization_name": "课程答辩测试组",
        "full_name": "注册测试员",
        "email": "register-smoke@smart-crm.local",
        "phone": "18800001111",
        "password": "Course@2026",
        "confirm_password": "Course@2026",
    }

    with TestClient(app) as client:
        created = client.post("/api/auth/register", json=register_payload)
        duplicate = client.post("/api/auth/register", json=register_payload)
        token = created.json()["token"]
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert created.status_code == 201
    assert created.json()["user"]["email"] == "register-smoke@smart-crm.local"
    assert created.json()["organizations"][0]["name"] == "课程答辩测试组"
    assert duplicate.status_code == 400
    assert "已注册" in duplicate.json()["detail"]
    assert me.status_code == 200
    assert me.json()["user"]["organization_name"] == "课程答辩测试组"


def test_rbac_rejects_unauthenticated_business_api() -> None:
    with TestClient(app, auth=False) as client:
        protected_response = client.get("/api/customers")
        login_response = client.post("/api/auth/login", json={"account": "demo@smart-crm.local", "password": "SmartCRM@2026"})

    assert protected_response.status_code == 401
    assert protected_response.json()["detail"] == "请先登录"
    assert login_response.status_code == 200


def test_rbac_sales_role_permissions() -> None:
    register_payload = {
        "organization_name": "销售权限测试组",
        "full_name": "销售权限用户",
        "email": "sales-rbac@smart-crm.local",
        "phone": "18800002222",
        "password": "Sales@2026",
        "confirm_password": "Sales@2026",
    }

    with TestClient(app, auth=False) as client:
        created = client.post("/api/auth/register", json=register_payload)
        assert created.status_code == 201

        with Session(main_module.engine) as session:
            user = session.exec(select(AuthUser).where(AuthUser.email == "sales-rbac@smart-crm.local")).one()
            user.role = "销售"
            session.add(user)
            session.commit()

        login = client.post("/api/auth/login", json={"account": "sales-rbac@smart-crm.local", "password": "Sales@2026"})
        token = login.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        me = client.get("/api/auth/me", headers=headers)
        customers = client.get("/api/customers", headers=headers)
        created_customer = client.post("/api/customers", json={"company": "销售权限客户", "contact_person": "销售员"}, headers=headers)
        denied_product = client.post(
            "/api/products",
            json={"name": "无权限商品", "sku": "RBAC-DENIED-001", "category": "软件", "unit_price": 100, "stock": 1},
            headers=headers,
        )
        denied_audit = client.get("/api/business-audit-logs", headers=headers)
        denied_report = client.get("/api/reports/sales-performance", headers=headers)
        denied_matrix = client.get("/api/admin/permission-matrix", headers=headers)

    assert login.status_code == 200
    assert me.json()["user"]["role"] == "销售"
    assert "catalog:manage" not in me.json()["user"]["permissions"]
    assert customers.status_code == 200
    assert created_customer.status_code == 201
    assert denied_product.status_code == 403
    assert denied_audit.status_code == 403
    assert denied_report.status_code == 403
    assert denied_matrix.status_code == 403


def test_paginated_collection_queries() -> None:
    with TestClient(app) as client:
        customers = client.get("/api/customers?page=1&per_page=3&q=深圳")
        products = client.get("/api/products?page=1&per_page=2&category=软件")
        leads = client.get("/api/leads?page=1&per_page=5&stage=proposal&ai_assisted=true")
        orders = client.get("/api/orders?page=1&per_page=2&status=draft&created_by_ai=true")
        client.post("/api/customers", json={"company": "分页审计客户", "contact_person": "审计查询员"})
        audit_logs = client.get("/api/business-audit-logs?page=1&per_page=1&entity_type=customer&action=create")

    assert customers.status_code == 200
    customer_payload = customers.json()
    assert customer_payload["page"] == 1
    assert customer_payload["per_page"] == 3
    assert customer_payload["total"] >= 3
    assert len(customer_payload["items"]) == 3
    assert all("深圳" in " ".join(str(value) for value in customer.values()) for customer in customer_payload["items"])

    assert products.status_code == 200
    product_payload = products.json()
    assert product_payload["total"] >= 2
    assert all(product["category"] == "软件" for product in product_payload["items"])

    assert leads.status_code == 200
    lead_payload = leads.json()
    assert lead_payload["items"]
    assert all(lead["stage"] == "proposal" and lead["ai_assisted"] is True for lead in lead_payload["items"])

    assert orders.status_code == 200
    order_payload = orders.json()
    assert order_payload["items"]
    assert all(order["status"] == "draft" and order["created_by_ai"] is True for order in order_payload["items"])

    assert audit_logs.status_code == 200
    audit_payload = audit_logs.json()
    assert audit_payload["total"] >= 1
    assert audit_payload["items"][0]["entity_type"] == "customer"
    assert audit_payload["items"][0]["action"] == "create"


def test_create_business_resources() -> None:
    with TestClient(app) as client:
        responses = {
            "customer": client.post(
                "/api/customers",
                json={
                    "company": "测试智能制造",
                    "industry": "智能制造",
                    "contact_person": "周测试",
                    "annual_revenue": 320000,
                },
            ),
            "contact": client.post(
                "/api/contacts",
                json={
                    "name": "林联系人",
                    "company": "测试智能制造",
                    "role": "采购经理",
                    "owner": "李伟超",
                },
            ),
            "lead": client.post(
                "/api/leads",
                json={
                    "title": "测试智能制造 CRM 升级",
                    "customer_name": "测试智能制造",
                    "owner": "李伟超",
                    "expected_amount": 128000,
                    "stage": "proposal",
                    "next_action": "发送正式报价单",
                    "due_date": "2026-06-30",
                },
            ),
            "case": client.post(
                "/api/cases",
                json={
                    "title": "测试工单",
                    "account": "测试智能制造",
                    "owner": "徐柠",
                    "priority": "warm",
                    "status": "open",
                    "status_label": "Open",
                    "due_date": "2026-06-25",
                },
            ),
            "task": client.post(
                "/api/tasks",
                json={
                    "title": "测试任务",
                    "description": "验证任务真实写库。",
                    "owner": "李伟超",
                    "due_date": "今天 18:00",
                    "priority": "hot",
                    "status": "today",
                    "status_label": "今天",
                },
            ),
            "goal": client.post(
                "/api/goals",
                json={
                    "name": "测试销售目标",
                    "period": "2026 Q3",
                    "current": 50000,
                    "target": 100000,
                    "note": "验证目标真实写库。",
                },
            ),
        }

        customer_list = client.get("/api/customers").json()
        lead_list = client.get("/api/leads").json()
        audit_logs = client.get("/api/business-audit-logs").json()

    for response in responses.values():
        assert response.status_code == 201

    assert responses["customer"].json()["company"] == "测试智能制造"
    assert responses["lead"].json()["stage"] == "proposal"
    assert responses["goal"].json()["progress"] == 50
    assert any(customer["company"] == "测试智能制造" for customer in customer_list)
    assert any(lead["title"] == "测试智能制造 CRM 升级" for lead in lead_list)
    created_entities = {log["entity_type"] for log in audit_logs if log["action"] == "create"}
    assert {"customer", "contact", "lead", "case", "task", "goal"} <= created_entities


def test_create_update_and_delete_products() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/api/products",
            json={
                "name": "课程演示商品",
                "sku": "COURSE-DEMO-001",
                "category": "软件",
                "unit_price": 5200,
                "stock": 42,
            },
        )
        duplicate = client.post(
            "/api/products",
            json={
                "name": "重复 SKU 商品",
                "sku": "COURSE-DEMO-001",
                "category": "软件",
                "unit_price": 5200,
                "stock": 1,
            },
        )
        product_id = created.json()["id"]
        updated = client.patch(f"/api/products/{product_id}", json={"unit_price": 6800, "stock": 60})
        deleted = client.delete(f"/api/products/{product_id}")
        protected_product = client.get("/api/products").json()[0]
        protected_delete = client.delete(f"/api/products/{protected_product['id']}")

    assert created.status_code == 201
    assert created.json()["sku"] == "COURSE-DEMO-001"
    assert duplicate.status_code == 400
    assert updated.status_code == 200
    assert updated.json()["unit_price"] == 6800
    assert updated.json()["stock"] == 60
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert protected_delete.status_code == 400
    assert "订单或库存流水" in protected_delete.json()["detail"]


def test_update_and_delete_business_resources() -> None:
    with TestClient(app) as client:
        customer = client.post("/api/customers", json={"company": "可编辑客户", "contact_person": "旧联系人"}).json()
        updated_customer = client.patch(
            f"/api/customers/{customer['id']}",
            json={"industry": "智能制造", "contact_person": "新联系人"},
        )

        contact = client.post("/api/contacts", json={"name": "可编辑联系人", "company": "可编辑客户", "owner": "李伟超"}).json()
        updated_contact = client.patch(f"/api/contacts/{contact['id']}", json={"role": "采购负责人"})

        lead = client.post(
            "/api/leads",
            json={
                "title": "可编辑商机",
                "customer_name": "可编辑客户",
                "owner": "李伟超",
                "stage": "proposal",
                "due_date": "2026-06-30",
            },
        ).json()
        updated_lead = client.patch(f"/api/leads/{lead['id']}", json={"stage": "negotiation", "expected_amount": 188000})

        case = client.post(
            "/api/cases",
            json={"title": "可编辑工单", "account": "可编辑客户", "owner": "徐柠", "due_date": "2026-06-25"},
        ).json()
        updated_case = client.patch(f"/api/cases/{case['id']}", json={"status": "working", "status_label": "Pending"})

        task = client.post("/api/tasks", json={"title": "可编辑任务", "owner": "李伟超"}).json()
        updated_task = client.patch(f"/api/tasks/{task['id']}", json={"status": "today", "status_label": "今天"})

        goal = client.post("/api/goals", json={"name": "可编辑目标", "current": 10, "target": 100}).json()
        updated_goal = client.patch(f"/api/goals/{goal['id']}", json={"current": 50})

        delete_responses = [
            client.delete(f"/api/contacts/{contact['id']}"),
            client.delete(f"/api/leads/{lead['id']}"),
            client.delete(f"/api/cases/{case['id']}"),
            client.delete(f"/api/tasks/{task['id']}"),
            client.delete(f"/api/goals/{goal['id']}"),
            client.delete(f"/api/customers/{customer['id']}"),
        ]
        seeded_customer = client.get("/api/customers").json()[0]
        protected_delete = client.delete(f"/api/customers/{seeded_customer['id']}")
        audit_logs = client.get("/api/business-audit-logs").json()

    assert updated_customer.status_code == 200
    assert updated_customer.json()["contact_person"] == "新联系人"
    assert updated_contact.json()["role"] == "采购负责人"
    assert updated_lead.json()["stage"] == "negotiation"
    assert updated_lead.json()["expected_amount"] == 188000
    assert updated_case.json()["status_label"] == "Pending"
    assert updated_task.json()["status"] == "today"
    assert updated_goal.json()["progress"] == 50
    assert all(response.status_code == 200 and response.json()["deleted"] is True for response in delete_responses)
    assert protected_delete.status_code == 400
    assert "已有订单" in protected_delete.json()["detail"]
    audit_actions = {(log["entity_type"], log["action"]) for log in audit_logs}
    for entity_type in {"contact", "lead", "case", "task", "goal"}:
        assert (entity_type, "update") in audit_actions
        assert (entity_type, "delete") in audit_actions


def test_create_order() -> None:
    with TestClient(app) as client:
        customers = client.get("/api/customers").json()
        products = client.get("/api/products").json()
        response = client.post(
            "/api/orders",
            json={
                "customer_id": customers[0]["id"],
                "owner": "李伟超",
                "region": "华东",
                "currency": "CNY",
                "status": "draft",
                "order_date": "2026-04-13",
                "due_date": "2026-04-20",
                "notes": "测试订单",
                "created_by_ai": True,
                "ai_confidence_score": 0.88,
                "items": [
                    {
                        "product_id": products[0]["id"],
                        "quantity": 1,
                        "unit_price": products[0]["unit_price"],
                    }
                ],
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["created_by_ai"] is True
    assert payload["items"][0]["quantity"] == 1


def test_update_order_lifecycle_fields() -> None:
    with TestClient(app) as client:
        order = client.get("/api/orders").json()[0]
        response = client.patch(
            f"/api/orders/{order['id']}",
            json={
                "owner": "王蕾",
                "region": "华北",
                "status": "fulfilled",
                "due_date": "2026-07-08",
                "notes": "订单状态已由运营复核更新。",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["owner"] == "王蕾"
    assert payload["region"] == "华北"
    assert payload["status"] == "fulfilled"
    assert payload["due_date"] == "2026-07-08"
    assert payload["notes"] == "订单状态已由运营复核更新。"
    assert payload["items"]


def test_update_order_items_reprices_and_adjusts_inventory() -> None:
    with TestClient(app) as client:
        order = next(item for item in client.get("/api/orders").json() if len(item["items"]) >= 2)
        initial_audit = client.get(f"/api/orders/{order['id']}/inventory-movements").json()
        temp_product = client.post(
            "/api/products",
            json={
                "name": "订单调整测试商品",
                "sku": "ORDER-EDIT-SMOKE-001",
                "category": "软件",
                "unit_price": 1200,
                "stock": 20,
            },
        ).json()
        products_before = {product["id"]: product for product in client.get("/api/products").json()}
        old_quantities = Counter()
        for item in order["items"]:
            old_quantities[item["product_id"]] += item["quantity"]
        response = client.patch(
            f"/api/orders/{order['id']}",
            json={
                "items": [
                    {
                        "product_id": temp_product["id"],
                        "quantity": 3,
                        "unit_price": 1350,
                    }
                ],
            },
        )
        products_after = {product["id"]: product for product in client.get("/api/products").json()}
        movements = client.get("/api/inventory/movements?limit=80").json()
        order_audit = client.get(f"/api/orders/{order['id']}/inventory-movements")

    assert initial_audit
    assert all(f"订单 #{order['id']} " in movement["reason"] for movement in initial_audit)
    assert response.status_code == 200
    assert order_audit.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["product_id"] == temp_product["id"]
    assert payload["items"][0]["quantity"] == 3
    assert payload["items"][0]["line_total"] == 4050
    assert payload["total_amount"] == 4050
    assert products_after[temp_product["id"]]["stock"] == products_before[temp_product["id"]]["stock"] - 3
    for product_id, quantity in old_quantities.items():
        assert products_after[product_id]["stock"] == products_before[product_id]["stock"] + quantity
    adjustment_product_ids = {movement["product_id"] for movement in movements if movement["source"] == "order_adjustment"}
    assert temp_product["id"] in adjustment_product_ids
    assert set(old_quantities) <= adjustment_product_ids
    audit_sources = {movement["source"] for movement in order_audit.json()}
    assert {"seed_order_deduction", "order_adjustment"} <= audit_sources


def test_order_inventory_movements_rejects_missing_order() -> None:
    with TestClient(app) as client:
        response = client.get("/api/orders/99999/inventory-movements")

    assert response.status_code == 404
    assert response.json()["detail"] == "订单不存在"


def test_update_order_items_rejects_insufficient_stock() -> None:
    with TestClient(app) as client:
        order = client.get("/api/orders").json()[0]
        temp_product = client.post(
            "/api/products",
            json={
                "name": "低库存订单调整商品",
                "sku": "ORDER-EDIT-LOW-STOCK-001",
                "category": "硬件",
                "unit_price": 8800,
                "stock": 1,
            },
        ).json()
        response = client.patch(
            f"/api/orders/{order['id']}",
            json={
                "items": [
                    {
                        "product_id": temp_product["id"],
                        "quantity": 2,
                        "unit_price": 8800,
                    }
                ],
            },
        )
        product_after = next(product for product in client.get("/api/products").json() if product["id"] == temp_product["id"])

    assert response.status_code == 400
    assert "库存不足" in response.json()["detail"]
    assert product_after["stock"] == 1


def test_create_order_rejects_insufficient_stock() -> None:
    with TestClient(app) as client:
        customers = client.get("/api/customers").json()
        low_stock_product = client.get("/api/inventory/restock-alerts").json()[0]
        response = client.post(
            "/api/orders",
            json={
                "customer_id": customers[0]["id"],
                "owner": "李伟超",
                "region": "华南",
                "currency": "CNY",
                "status": "confirmed",
                "order_date": "2026-06-22",
                "due_date": "2026-06-30",
                "notes": "验证库存不足保护",
                "created_by_ai": False,
                "items": [
                    {
                        "product_id": low_stock_product["product_id"],
                        "quantity": low_stock_product["current_stock"] + 1,
                        "unit_price": low_stock_product["unit_price"],
                    }
                ],
            },
        )

    assert response.status_code == 400
    assert "库存不足" in response.json()["detail"]


def test_export_orders_csv() -> None:
    with TestClient(app) as client:
        response = client.get("/api/orders/export.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    body = response.text
    assert "订单ID,客户,负责人" in body
    assert "智能巡检终端" in body
    assert "AI Copilot 演示数据" in body


def test_inventory_restock_alerts_and_movements() -> None:
    with TestClient(app) as client:
        alerts_response = client.get("/api/inventory/restock-alerts")
        initial_movements = client.get("/api/inventory/movements").json()
        alert = alerts_response.json()[0]

        restock_response = client.post(
            f"/api/products/{alert['product_id']}/restock",
            json={"quantity": 25, "reason": "测试低库存补货", "operator": "李伟超"},
        )

        customers = client.get("/api/customers").json()
        restocked_product = restock_response.json()["product"]
        order_response = client.post(
            "/api/orders",
            json={
                "customer_id": customers[0]["id"],
                "owner": "李伟超",
                "region": "华南",
                "currency": "CNY",
                "status": "confirmed",
                "order_date": "2026-06-22",
                "due_date": "2026-06-30",
                "notes": "验证库存流水",
                "created_by_ai": False,
                "items": [
                    {
                        "product_id": restocked_product["id"],
                        "quantity": 1,
                        "unit_price": restocked_product["unit_price"],
                    }
                ],
            },
        )
        movements = client.get("/api/inventory/movements").json()

    assert alerts_response.status_code == 200
    assert alert["priority"] in {"critical", "warning"}
    assert alert["recommended_restock"] > 0
    assert any(movement["source"] == "seed_order_deduction" for movement in initial_movements)

    assert restock_response.status_code == 200
    restock_payload = restock_response.json()
    assert restock_payload["product"]["stock"] == alert["current_stock"] + 25
    assert restock_payload["movement"]["source"] == "manual_restock"
    assert restock_payload["movement"]["before_stock"] == alert["current_stock"]
    assert restock_payload["movement"]["after_stock"] == alert["current_stock"] + 25

    assert order_response.status_code == 201
    sources = {movement["source"] for movement in movements}
    assert {"manual_restock", "order_deduction", "seed_order_deduction"} <= sources


def test_vision_extract_text_file_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    order_text = "客户：云川医疗 联系人：陈敏\n智能巡检终端 x2\n客户数据接入服务 x1"

    with TestClient(app) as client:
        response = client.post(
            "/api/vision-extract",
            files={"file": ("order.txt", order_text.encode("utf-8"), "text/plain")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["company"] == "云川医疗"
    assert payload["customer_name"] == "陈敏"
    assert payload["fallback_used"] is True
    assert payload["source"] == "local_text_parser"
    assert payload["items"][0]["product_name"] == "智能巡检终端"
    assert payload["items"][0]["quantity"] == 2


def test_vision_extract_llm_json(monkeypatch) -> None:
    async def fake_complete_messages(**kwargs):
        messages = kwargs["messages"]
        assert messages[1]["content"][1]["type"] == "image_url"
        return (
            '{"customer_name":"周宁","company":"南山科技","confidence":0.93,'
            '"summary":"多模态识别到一张订单截图。",'
            '"items":[{"product_name":"AI 商机评分模块","quantity":3,"unit_price":12800}],'
            '"suggested_notes":"模型识别结果，需人工复核。"}',
            False,
        )

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_vision_model", "test-vision-model")
    monkeypatch.setattr(main_module.vision_service.llm, "complete_messages", fake_complete_messages)

    with TestClient(app) as client:
        response = client.post(
            "/api/vision-extract",
            files={"file": ("order.jpg", b"fake-jpeg-bytes", "image/jpeg")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["company"] == "南山科技"
    assert payload["fallback_used"] is False
    assert payload["source"] == "llm_vision"
    assert payload["items"][0]["product_name"] == "AI 商机评分模块"
    assert payload["items"][0]["quantity"] == 3


def test_ai_audit_logs_record_runtime_actions(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    order_text = "客户：云川医疗 联系人：陈敏\n智能巡检终端 x1"

    with TestClient(app) as client:
        assert client.get("/api/ai-audit-logs").json() == []
        lead = client.get("/api/leads").json()[0]
        customer = client.get("/api/customers").json()[0]
        product = client.get("/api/products").json()[0]

        client.get("/api/copilot/summary")
        client.post("/api/copilot/follow-up", json={"lead_id": lead["id"]})
        client.post(
            "/api/copilot/order-draft",
            json={
                "customer_id": customer["id"],
                "product_ids": [product["id"]],
                "business_goal": "验证 AI 审计日志",
            },
        )
        client.post(
            "/api/vision-extract",
            files={"file": ("order.txt", order_text.encode("utf-8"), "text/plain")},
        )
        response = client.get("/api/ai-audit-logs")

    assert response.status_code == 200
    logs = response.json()
    operations = {log["operation"] for log in logs}
    assert {"copilot_summary", "copilot_follow_up", "copilot_order_draft", "vision_extract"} <= operations
    assert all(log["fallback_used"] is True for log in logs)
    assert all(log["latency_ms"] >= 0 for log in logs)
    assert all("sk-" not in log["request_summary"] for log in logs)


def test_business_audit_logs_record_core_write_actions() -> None:
    with TestClient(app) as client:
        assert client.get("/api/business-audit-logs").json() == []
        customer_response = client.post(
            "/api/customers",
            json={
                "company": "审计测试客户",
                "industry": "智能制造",
                "contact_person": "审计负责人",
                "annual_revenue": 420000,
                "status": "active",
            },
        )
        product_response = client.post(
            "/api/products",
            json={
                "name": "审计测试商品",
                "sku": "AUDIT-PRODUCT-001",
                "category": "软件",
                "unit_price": 3600,
                "stock": 30,
            },
        )
        product = product_response.json()
        restock_response = client.post(
            f"/api/products/{product['id']}/restock",
            json={"quantity": 5, "reason": "审计测试补货", "operator": "审计员"},
        )
        order_response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_response.json()["id"],
                "owner": "审计员",
                "region": "华南",
                "currency": "CNY",
                "status": "draft",
                "order_date": "2026-06-23",
                "due_date": "2026-06-30",
                "notes": "审计测试订单",
                "created_by_ai": False,
                "items": [
                    {
                        "product_id": product["id"],
                        "quantity": 2,
                        "unit_price": product["unit_price"],
                    }
                ],
            },
        )
        update_response = client.patch(
            f"/api/orders/{order_response.json()['id']}",
            json={"status": "confirmed", "notes": "审计测试订单已确认"},
        )
        audit_logs = client.get("/api/business-audit-logs").json()

    assert customer_response.status_code == 201
    assert product_response.status_code == 201
    assert restock_response.status_code == 200
    assert order_response.status_code == 201
    assert update_response.status_code == 200
    actions = {(log["entity_type"], log["action"]) for log in audit_logs}
    assert ("customer", "create") in actions
    assert ("product", "create") in actions
    assert ("product", "restock") in actions
    assert ("order", "create") in actions
    assert ("order", "update") in actions
    assert all(log["status"] == "success" for log in audit_logs)


def test_copilot_summary_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        response = client.get("/api/copilot/summary")
        history_response = client.get("/api/copilot/recommendations?source=summary&page=1&per_page=3")

    assert response.status_code == 200
    payload = response.json()
    assert payload["insights"]
    assert payload["top_opportunity"]["rule_score"] >= 0
    assert payload["forecast_amount"] >= 0
    assert payload["fallback_used"] is True

    assert history_response.status_code == 200
    history = history_response.json()
    assert history["total"] >= min(len(payload["insights"]), 5)
    assert len(history["items"]) <= 3
    assert history["items"][0]["source"] == "summary"
    assert history["items"][0]["score_reasons"]
    assert history["items"][0]["llm_summary"]
    assert history["items"][0]["fallback_used"] is True


def test_copilot_follow_up_by_lead(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        lead = client.get("/api/leads").json()[0]
        response = client.post("/api/copilot/follow-up", json={"lead_id": lead["id"]})
        history_response = client.get("/api/copilot/recommendations?source=follow_up&fallback_used=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["message_draft"]
    assert payload["next_best_action"]
    assert payload["fallback_used"] is True

    assert history_response.status_code == 200
    history = history_response.json()
    assert any(item["lead_id"] == lead["id"] and item["message_draft"] for item in history)
    assert all(item["source"] == "follow_up" for item in history)


def test_copilot_recommendation_can_create_task(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        client.get("/api/copilot/summary")
        recommendation = client.get("/api/copilot/recommendations?source=summary").json()[0]
        response = client.post(f"/api/copilot/recommendations/{recommendation['id']}/task")
        duplicate_response = client.post(f"/api/copilot/recommendations/{recommendation['id']}/task")
        tasks = client.get("/api/tasks", params={"q": f"CopilotRecommendation#{recommendation['id']}"}).json()
        lead = client.get("/api/leads", params={"q": recommendation["lead_title"]}).json()[0]
        audit_logs = client.get("/api/business-audit-logs", params={"entity_type": "task"}).json()

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"].startswith("跟进")
    assert f"CopilotRecommendation#{recommendation['id']}" in payload["description"]
    assert payload["priority"] in {"hot", "warm", "cold"}
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["id"] == payload["id"]
    assert len(tasks) == 1
    assert lead["next_action"] == recommendation["next_best_action"]
    assert lead["ai_assisted"] is True
    assert any(log["action"] == "convert" and log["entity_id"] == payload["id"] for log in audit_logs)


def test_copilot_order_draft(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        customer = client.get("/api/customers").json()[0]
        products = client.get("/api/products").json()
        response = client.post(
            "/api/copilot/order-draft",
            json={
                "customer_id": customer["id"],
                "product_ids": [products[0]["id"]],
                "business_goal": "生成课程演示用智能订单草稿",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["customer_id"] == customer["id"]
    assert payload["items"][0]["quantity"] >= 1
    assert payload["fallback_used"] is True
