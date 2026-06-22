from collections import Counter

import pytest
from fastapi.testclient import TestClient as FastAPITestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app import database
from app.config import settings
import app.main as main_module
from app.models import AuthUser, CopilotRecommendation, Customer, CustomerActivity, SalesLead, SalesOrder, TaskItem
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


def test_customer_owner_lightweight_migration_backfills_from_contacts(monkeypatch) -> None:
    migration_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with migration_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE customer (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                company VARCHAR NOT NULL,
                industry VARCHAR NOT NULL,
                city VARCHAR NOT NULL,
                contact_person VARCHAR NOT NULL,
                phone VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                source VARCHAR NOT NULL,
                level VARCHAR NOT NULL,
                annual_revenue FLOAT NOT NULL,
                status VARCHAR NOT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )
        connection.exec_driver_sql("CREATE TABLE contact (id INTEGER PRIMARY KEY, company VARCHAR NOT NULL, owner VARCHAR NOT NULL)")
        connection.exec_driver_sql(
            """
            INSERT INTO customer
            (id, name, company, industry, city, contact_person, phone, email, source, level, annual_revenue, status, created_at)
            VALUES (1, '周宁', '南山科技', '人工智能', '深圳', '周宁', '13200008888', 'zhouning@nanshan.ai', '校企合作', 'S', 1680000, 'active', '2026-06-23 00:00:00')
            """
        )
        connection.exec_driver_sql("INSERT INTO contact (id, company, owner) VALUES (1, '南山科技', '李伟超')")

    monkeypatch.setattr(database, "engine", migration_engine)
    database.run_lightweight_migrations()

    with migration_engine.connect() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(customer)").fetchall()}
        owner = connection.exec_driver_sql("SELECT owner FROM customer WHERE id = 1").scalar_one()

    assert "owner" in columns
    assert owner == "李伟超"


def test_order_approval_sla_lightweight_migration(monkeypatch) -> None:
    migration_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with migration_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE customer (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                company VARCHAR NOT NULL,
                industry VARCHAR NOT NULL,
                city VARCHAR NOT NULL,
                contact_person VARCHAR NOT NULL,
                phone VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                source VARCHAR NOT NULL,
                level VARCHAR NOT NULL,
                annual_revenue FLOAT NOT NULL,
                status VARCHAR NOT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            CREATE TABLE orderapprovalrequest (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                owner VARCHAR NOT NULL,
                requester VARCHAR NOT NULL,
                reviewer VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                reason VARCHAR NOT NULL,
                risk_summary VARCHAR NOT NULL,
                requested_total FLOAT NOT NULL,
                previous_order_status VARCHAR NOT NULL,
                target_order_status VARCHAR NOT NULL,
                decision_comment VARCHAR NOT NULL,
                decided_at DATETIME,
                created_at DATETIME NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO orderapprovalrequest
            (id, order_id, owner, requester, reviewer, status, reason, risk_summary, requested_total, previous_order_status, target_order_status, decision_comment, decided_at, created_at)
            VALUES (1, 1, '李伟超', '李伟超', '销售经理', 'pending', '旧版审批', '旧版风险摘要', 120000, 'draft', 'confirmed', '', NULL, '2026-06-23 00:00:00')
            """
        )

    monkeypatch.setattr(database, "engine", migration_engine)
    database.run_lightweight_migrations()

    with migration_engine.connect() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(orderapprovalrequest)").fetchall()}
        migrated = connection.exec_driver_sql(
            "SELECT risk_level, sla_due_at FROM orderapprovalrequest WHERE id = 1"
        ).one()

    assert {"risk_level", "sla_due_at"} <= columns
    assert migrated.risk_level == "medium"
    assert migrated.sla_due_at is not None


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
    assert any(item["entity_type"] == "order_approval" and "SLA" in item["message"] for item in copilot_notifications)


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
    assert {"crm:read", "reports:read", "permissions:read", "approval:manage", "team:manage"} <= permission_keys

    roles = {role["role"]: role for role in payload["roles"]}
    assert roles["管理员"]["all_permissions"] is True
    assert "permissions:read" in roles["销售经理"]["permissions"]
    assert "team:manage" in roles["销售经理"]["permissions"]
    assert "approval:manage" in roles["销售经理"]["permissions"]
    assert "catalog:manage" not in roles["销售"]["permissions"]
    assert "approval:manage" not in roles["销售"]["permissions"]

    modules = {module["path"]: module for module in payload["modules"]}
    assert modules["/permissions"]["permission"] == "permissions:read"
    assert "销售" not in modules["/permissions"]["roles"]
    assert "管理员" in modules["/permissions"]["roles"]
    assert modules["/team"]["permission"] == "team:manage"
    assert "销售经理" in modules["/team"]["roles"]
    assert "销售" not in modules["/team"]["roles"]


def test_resource_collection_payloads() -> None:
    endpoints = {
        "/api/customers": "company",
        "/api/customer-activities": "subject",
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


def test_field_level_validation_rejects_invalid_payloads() -> None:
    with TestClient(app) as client:
        customer = client.get("/api/customers").json()[0]
        product = client.get("/api/products").json()[0]
        task = client.get("/api/tasks").json()[0]
        responses = [
            client.post("/api/customers", json={"company": "校验客户", "contact_person": "张三", "email": "not-email"}),
            client.post("/api/contacts", json={"name": "校验联系人", "company": "校验客户", "email": "bad-email"}),
            client.post("/api/products", json={"name": "非法分类商品", "sku": "INVALID-CATEGORY-001", "category": "课程", "unit_price": 100, "stock": 1}),
            client.post("/api/cases", json={"title": "非法优先级工单", "account": "校验客户", "owner": "李伟超", "priority": "urgent"}),
            client.patch(f"/api/tasks/{task['id']}", json={"status": "blocked"}),
            client.post("/api/goals", json={"name": "非法目标", "current": 10, "target": 0}),
            client.post(
                "/api/orders",
                json={
                    "customer_id": customer["id"],
                    "owner": "李伟超",
                    "region": "华南",
                    "currency": "CNY",
                    "status": "draft",
                    "order_date": "2026-06-30",
                    "due_date": "2026-06-22",
                    "items": [{"product_id": product["id"], "quantity": 1, "unit_price": product["unit_price"]}],
                },
            ),
            client.post(
                "/api/orders",
                json={
                    "customer_id": customer["id"],
                    "owner": "李伟超",
                    "region": "华南",
                    "currency": "CNY",
                    "status": "draft",
                    "order_date": "2026-06-22",
                    "due_date": "2026-06-30",
                    "items": [],
                },
            ),
        ]

    assert all(response.status_code == 422 for response in responses)
    details = [str(response.json()["detail"]) for response in responses]
    assert any("请输入有效邮箱" in detail for detail in details)
    assert any("商品分类无效" in detail for detail in details)
    assert any("交付日期不能早于下单日期" in detail for detail in details)


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


def test_team_member_management_and_status_login_guard() -> None:
    with TestClient(app) as client:
        me = client.get("/api/auth/me")
        self_id = me.json()["user"]["id"]
        created = client.post(
            "/api/admin/users",
            json={
                "full_name": "团队演示销售",
                "email": "team-sales@smart-crm.local",
                "phone": "18800005555",
                "role": "销售",
                "position": "课程演示销售",
                "department": "客户增长中心",
                "location": "深圳 · 粤海",
                "status": "active",
                "password": "Team@2026",
                "confirm_password": "Team@2026",
            },
        )
        duplicate = client.post(
            "/api/admin/users",
            json={
                "full_name": "重复成员",
                "email": "team-sales@smart-crm.local",
                "password": "Team@2026",
                "confirm_password": "Team@2026",
            },
        )
        members = client.get("/api/admin/users?role=销售")
        updated = client.patch(
            f"/api/admin/users/{created.json()['id']}",
            json={
                "role": "销售经理",
                "status": "inactive",
                "position": "销售小组长",
                "password": "TeamNew@2026",
                "confirm_password": "TeamNew@2026",
            },
        )
        inactive_login = client.post("/api/auth/login", json={"account": "team-sales@smart-crm.local", "password": "TeamNew@2026"})
        self_profile_update = client.patch(f"/api/admin/users/{self_id}", json={"phone": "18600002048", "role": "管理员", "status": "active"})
        self_update = client.patch(f"/api/admin/users/{self_id}", json={"status": "inactive"})
        manager_login = client.post("/api/auth/login", json={"account": "manager@smart-crm.local", "password": "SmartCRM@2026"})
        manager_headers = {"Authorization": f"Bearer {manager_login.json()['token']}"}
        manager_admin_create = client.post(
            "/api/admin/users",
            json={
                "full_name": "越权管理员",
                "email": "manager-admin@smart-crm.local",
                "role": "管理员",
                "password": "Team@2026",
                "confirm_password": "Team@2026",
            },
            headers=manager_headers,
        )
        audit_logs = client.get("/api/auth/audit-logs?q=team-sales@smart-crm.local").json()

    assert created.status_code == 201
    assert created.json()["role"] == "销售"
    assert created.json()["data_scope"] == "own"
    assert duplicate.status_code == 400
    assert members.status_code == 200
    assert any(member["email"] == "team-sales@smart-crm.local" for member in members.json())
    assert updated.status_code == 200
    assert updated.json()["role"] == "销售经理"
    assert updated.json()["status"] == "inactive"
    assert updated.json()["data_scope"] == "all"
    assert inactive_login.status_code == 403
    assert self_profile_update.status_code == 200
    assert self_update.status_code == 400
    assert manager_admin_create.status_code == 403
    assert any(log["event"] == "team_create" for log in audit_logs)
    assert any(log["event"] == "team_update" for log in audit_logs)


def test_rbac_rejects_unauthenticated_business_api() -> None:
    with TestClient(app, auth=False) as client:
        protected_response = client.get("/api/customers")
        login_response = client.post("/api/auth/login", json={"account": "demo@smart-crm.local", "password": "SmartCRM@2026"})

    assert protected_response.status_code == 401
    assert protected_response.json()["detail"] == "请先登录"
    assert login_response.status_code == 200


def test_rbac_sales_role_permissions(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    register_payload = {
        "organization_name": "销售权限测试组",
        "full_name": "李伟超",
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
        dashboard = client.get("/api/dashboard", headers=headers)
        leads = client.get("/api/leads", headers=headers)
        tasks = client.get("/api/tasks", headers=headers)
        orders = client.get("/api/orders", headers=headers)
        created_customer = client.post("/api/customers", json={"company": "销售权限客户", "contact_person": "销售员"}, headers=headers)
        denied_customer_create = client.post(
            "/api/customers",
            json={"company": "越权客户", "contact_person": "销售员", "owner": "王蕾"},
            headers=headers,
        )
        denied_lead_create = client.post(
            "/api/leads",
            json={"title": "越权商机", "customer_name": "越权客户", "owner": "王蕾", "due_date": "2026-06-30"},
            headers=headers,
        )

        with Session(main_module.engine) as session:
            other_customer = session.exec(select(Customer).where(Customer.owner != "李伟超")).first()
            other_lead = session.exec(select(SalesLead).where(SalesLead.owner != "李伟超")).first()
            other_order = session.exec(select(SalesOrder).where(SalesOrder.owner != "李伟超")).first()
            other_task = session.exec(select(TaskItem).where(TaskItem.owner != "李伟超")).first()
            assert other_customer is not None
            assert other_lead is not None
            assert other_order is not None
            assert other_task is not None
            other_customer_id = other_customer.id
            other_lead_id = other_lead.id
            other_order_id = other_order.id
            other_task_id = other_task.id

            own_recommendation = CopilotRecommendation(
                source="scope_test",
                lead_title="本人 Copilot 推荐",
                customer_name="北辰教育科技",
                owner="李伟超",
                region="华南",
                stage="proposal",
                grade="A",
                rule_score=91,
                next_best_action="联系采购确认最终报价",
            )
            other_recommendation = CopilotRecommendation(
                source="scope_test",
                lead_id=other_lead.id,
                lead_title=other_lead.title,
                customer_name=other_lead.customer_name,
                owner=other_lead.owner,
                region=other_lead.region,
                stage=other_lead.stage.value,
                grade="B",
                rule_score=82,
                next_best_action="整理跨团队跟进方案",
            )
            session.add(own_recommendation)
            session.add(other_recommendation)
            session.commit()
            session.refresh(own_recommendation)
            session.refresh(other_recommendation)
            own_recommendation_id = own_recommendation.id
            other_recommendation_id = other_recommendation.id

        denied_customer_update = client.patch(f"/api/customers/{other_customer_id}", json={"industry": "越权修改"}, headers=headers)
        denied_lead_update = client.patch(f"/api/leads/{other_lead_id}", json={"stage": "won"}, headers=headers)
        denied_order_update = client.patch(f"/api/orders/{other_order_id}", json={"status": "fulfilled"}, headers=headers)
        denied_task_update = client.patch(f"/api/tasks/{other_task_id}", json={"status": "today"}, headers=headers)
        products = client.get("/api/products", headers=headers).json()
        created_contact_default_owner = client.post(
            "/api/contacts",
            json={"name": "默认负责人联系人", "company": "销售权限客户", "owner": "未分配"},
            headers=headers,
        )
        created_lead_default_owner = client.post(
            "/api/leads",
            json={
                "title": "默认负责人线索",
                "customer_name": "销售权限客户",
                "owner": "未分配",
                "due_date": "2026-06-30",
            },
            headers=headers,
        )
        created_case_default_owner = client.post(
            "/api/cases",
            json={
                "title": "默认负责人工单",
                "account": "销售权限客户",
                "owner": "待分配",
                "due_date": "2026-06-30",
            },
            headers=headers,
        )
        created_task_default_owner = client.post(
            "/api/tasks",
            json={"title": "默认负责人任务", "owner": "新负责人", "due_date": "明天 18:00"},
            headers=headers,
        )
        created_order_default_owner = client.post(
            "/api/orders",
            json={
                "customer_id": created_customer.json()["id"],
                "owner": "未分配",
                "region": "华南",
                "currency": "CNY",
                "status": "draft",
                "order_date": "2026-06-23",
                "due_date": "2026-07-03",
                "notes": "默认负责人订单",
                "created_by_ai": False,
                "items": [{"product_id": products[0]["id"], "quantity": 1, "unit_price": products[0]["unit_price"]}],
            },
            headers=headers,
        )
        denied_order_for_other_customer = client.post(
            "/api/orders",
            json={
                "customer_id": other_customer_id,
                "owner": "李伟超",
                "region": "华南",
                "currency": "CNY",
                "status": "draft",
                "order_date": "2026-06-23",
                "due_date": "2026-07-03",
                "notes": "越权客户订单",
                "created_by_ai": False,
                "items": [{"product_id": products[0]["id"], "quantity": 1, "unit_price": products[0]["unit_price"]}],
            },
            headers=headers,
        )
        recommendations = client.get("/api/copilot/recommendations", headers=headers)
        own_copilot_ask = client.post(
            "/api/copilot/ask",
            json={"question": "我本周应该优先跟进什么？"},
            headers=headers,
        )
        denied_copilot_ask = client.post(
            "/api/copilot/ask",
            json={"question": "这个客户有什么风险？", "customer_id": other_customer_id},
            headers=headers,
        )
        denied_recommendation_task = client.post(
            f"/api/copilot/recommendations/{other_recommendation_id}/task",
            headers=headers,
        )
        denied_product = client.post(
            "/api/products",
            json={"name": "无权限商品", "sku": "RBAC-DENIED-001", "category": "软件", "unit_price": 100, "stock": 1},
            headers=headers,
        )
        denied_audit = client.get("/api/business-audit-logs", headers=headers)
        denied_consistency = client.get("/api/system/consistency-checks", headers=headers)
        denied_report = client.get("/api/reports/sales-performance", headers=headers)
        denied_matrix = client.get("/api/admin/permission-matrix", headers=headers)
        denied_team = client.get("/api/admin/users", headers=headers)

    assert login.status_code == 200
    assert me.json()["user"]["role"] == "销售"
    assert me.json()["user"]["data_scope"] == "own"
    assert "catalog:manage" not in me.json()["user"]["permissions"]
    assert customers.status_code == 200
    assert dashboard.status_code == 200
    assert leads.status_code == 200
    assert tasks.status_code == 200
    assert orders.status_code == 200
    assert recommendations.status_code == 200
    assert own_copilot_ask.status_code == 200
    assert denied_copilot_ask.status_code == 403
    assert customers.json()
    assert leads.json()
    assert tasks.json()
    assert orders.json()
    assert all(item["owner"] == "李伟超" for item in customers.json())
    assert all(item["owner"] == "李伟超" for item in leads.json())
    assert all(item["owner"] == "李伟超" for item in tasks.json())
    assert all(item["owner"] == "李伟超" for item in orders.json())
    assert all(item["owner"] == "李伟超" for item in recommendations.json())
    assert any(item["id"] == own_recommendation_id for item in recommendations.json())
    assert all(item["id"] != other_recommendation_id for item in recommendations.json())
    assert created_customer.status_code == 201
    assert created_customer.json()["owner"] == "李伟超"
    assert created_contact_default_owner.status_code == 201
    assert created_contact_default_owner.json()["owner"] == "李伟超"
    assert created_lead_default_owner.status_code == 201
    assert created_lead_default_owner.json()["owner"] == "李伟超"
    assert created_case_default_owner.status_code == 201
    assert created_case_default_owner.json()["owner"] == "李伟超"
    assert created_task_default_owner.status_code == 201
    assert created_task_default_owner.json()["owner"] == "李伟超"
    assert created_order_default_owner.status_code == 201
    assert created_order_default_owner.json()["owner"] == "李伟超"
    assert denied_customer_create.status_code == 403
    assert denied_customer_update.status_code == 403
    assert denied_order_for_other_customer.status_code == 403
    assert denied_lead_create.status_code == 403
    assert denied_lead_update.status_code == 403
    assert denied_order_update.status_code == 403
    assert denied_task_update.status_code == 403
    assert denied_recommendation_task.status_code == 403
    assert denied_product.status_code == 403
    assert denied_audit.status_code == 403
    assert denied_consistency.status_code == 403
    assert denied_report.status_code == 403
    assert denied_matrix.status_code == 403
    assert denied_team.status_code == 403


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


def test_customer_workspace_aggregates_account_plan(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        order = client.get("/api/orders").json()[0]
        response = client.get(f"/api/customers/{order['customer_id']}/workspace")
        audit_response = client.get("/api/ai-audit-logs?operation=customer_account_plan")

    assert response.status_code == 200
    payload = response.json()
    assert payload["customer"]["id"] == order["customer_id"]
    assert {metric["label"] for metric in payload["metrics"]} == {"客户健康分", "累计收入", "在管商机", "服务风险"}
    assert payload["orders"]
    assert any(item["category"] == "订单" for item in payload["timeline"])
    assert payload["account_plan"]["fallback_used"] is True
    assert payload["account_plan"]["summary"]
    assert payload["account_plan"]["next_actions"]

    assert audit_response.status_code == 200
    assert any(item["operation"] == "customer_account_plan" for item in audit_response.json())


def test_customer_activity_create_updates_workspace_and_audit(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        customer = client.get("/api/customers").json()[0]
        created = client.post(
            f"/api/customers/{customer['id']}/activities",
            json={
                "activity_type": "meeting",
                "subject": "高层复盘会议",
                "summary": "客户确认希望把 AI 副驾扩展到售后团队。",
                "outcome": "扩展意向明确",
                "next_action": "发送售后场景报价",
                "sentiment": "positive",
            },
        )
        activity_payload = created.json()
        activities = client.get(f"/api/customer-activities?customer_id={customer['id']}&q=高层复盘")
        workspace = client.get(f"/api/customers/{customer['id']}/workspace")
        task_response = client.post(f"/api/customer-activities/{activity_payload['id']}/task")
        duplicate_task_response = client.post(f"/api/customer-activities/{activity_payload['id']}/task")
        tasks = client.get("/api/tasks", params={"q": f"CustomerActivity#{activity_payload['id']}"})
        audit_logs = client.get("/api/business-audit-logs?entity_type=customer_activity")
        task_audit_logs = client.get("/api/business-audit-logs", params={"entity_type": "task"})

    assert created.status_code == 201
    activity = activity_payload
    assert activity["customer_id"] == customer["id"]
    assert activity["customer_name"] == customer["company"]
    assert activity["subject"] == "高层复盘会议"

    assert activities.status_code == 200
    assert any(item["id"] == activity["id"] for item in activities.json())

    assert workspace.status_code == 200
    workspace_payload = workspace.json()
    assert any(item["id"] == activity["id"] for item in workspace_payload["activities"])
    assert any(item["category"] == "互动" and item["title"] == "高层复盘会议" for item in workspace_payload["timeline"])
    assert "发送售后场景报价" in workspace_payload["account_plan"]["next_actions"]

    assert audit_logs.status_code == 200
    assert any(log["entity_id"] == activity["id"] and log["action"] == "create" for log in audit_logs.json())

    assert task_response.status_code == 201
    task = task_response.json()
    assert task["title"].startswith(f"跟进 {customer['company']}")
    assert f"CustomerActivity#{activity['id']}" in task["description"]
    assert "发送售后场景报价" in task["description"]
    assert task["priority"] == "warm"
    assert duplicate_task_response.status_code == 201
    assert duplicate_task_response.json()["id"] == task["id"]
    assert tasks.status_code == 200
    assert len(tasks.json()) == 1
    assert any(log["action"] == "convert" and log["entity_id"] == task["id"] for log in task_audit_logs.json())


def test_customer_workspace_respects_sales_scope(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    register_payload = {
        "organization_name": "客户工作台权限组",
        "full_name": "李伟超",
        "email": "workspace-sales@smart-crm.local",
        "phone": "18800004444",
        "password": "Sales@2026",
        "confirm_password": "Sales@2026",
    }

    with TestClient(app, auth=False) as client:
        created = client.post("/api/auth/register", json=register_payload)
        assert created.status_code == 201
        with Session(main_module.engine) as session:
            user = session.exec(select(AuthUser).where(AuthUser.email == "workspace-sales@smart-crm.local")).one()
            user.role = "销售"
            other_customer = session.exec(select(Customer).where(Customer.owner != "李伟超")).first()
            assert other_customer is not None
            other_activity = session.exec(select(CustomerActivity).where(CustomerActivity.owner != "李伟超")).first()
            assert other_activity is not None
            other_customer_id = other_customer.id
            other_activity_id = other_activity.id
            session.add(user)
            session.commit()

        login = client.post("/api/auth/login", json={"account": "workspace-sales@smart-crm.local", "password": "Sales@2026"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        own_customer = client.get("/api/customers", headers=headers).json()[0]
        own_workspace = client.get(f"/api/customers/{own_customer['id']}/workspace", headers=headers)
        denied_workspace = client.get(f"/api/customers/{other_customer_id}/workspace", headers=headers)
        own_activity = client.post(
            f"/api/customers/{own_customer['id']}/activities",
            json={"subject": "销售本人客户跟进", "summary": "确认下一次演示时间。"},
            headers=headers,
        )
        own_task = client.post(f"/api/customer-activities/{own_activity.json()['id']}/task", headers=headers)
        denied_activity = client.post(
            f"/api/customers/{other_customer_id}/activities",
            json={"subject": "越权客户跟进", "summary": "不应允许写入。"},
            headers=headers,
        )
        denied_task = client.post(f"/api/customer-activities/{other_activity_id}/task", headers=headers)

    assert own_workspace.status_code == 200
    assert own_workspace.json()["customer"]["owner"] == "李伟超"
    assert denied_workspace.status_code == 403
    assert own_activity.status_code == 201
    assert own_activity.json()["owner"] == "李伟超"
    assert own_task.status_code == 201
    assert own_task.json()["owner"] == "李伟超"
    assert denied_activity.status_code == 403
    assert denied_task.status_code == 403


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


def test_order_approval_workflow() -> None:
    with TestClient(app) as client:
        customers = client.get("/api/customers").json()
        products = client.get("/api/products").json()
        order_response = client.post(
            "/api/orders",
            json={
                "customer_id": customers[0]["id"],
                "owner": "李伟超",
                "region": "华南",
                "currency": "CNY",
                "status": "draft",
                "order_date": "2026-06-23",
                "due_date": "2026-07-03",
                "notes": "审批流测试订单",
                "created_by_ai": True,
                "ai_confidence_score": 0.82,
                "items": [
                    {
                        "product_id": products[0]["id"],
                        "quantity": 1,
                        "unit_price": products[0]["unit_price"],
                    }
                ],
            },
        )
        order_id = order_response.json()["id"]

        approval_response = client.post(
            f"/api/orders/{order_id}/approval-requests",
            json={"reason": "高价值 AI 订单进入确认前需要经理复核。", "reviewer": "销售经理"},
        )
        duplicate_response = client.post(
            f"/api/orders/{order_id}/approval-requests",
            json={"reason": "重复提交审批"},
        )
        pending_approvals = client.get("/api/order-approvals?status=pending").json()
        medium_approvals = client.get("/api/order-approvals?risk_level=medium").json()

        register_payload = {
            "organization_name": "审批权限测试组",
            "full_name": "李伟超",
            "email": "approval-sales@smart-crm.local",
            "phone": "18800003333",
            "password": "Sales@2026",
            "confirm_password": "Sales@2026",
        }
        created = client.post("/api/auth/register", json=register_payload)
        assert created.status_code == 201
        with Session(main_module.engine) as session:
            user = session.exec(select(AuthUser).where(AuthUser.email == "approval-sales@smart-crm.local")).one()
            user.role = "销售"
            session.add(user)
            session.commit()

        sales_login = client.post("/api/auth/login", json={"account": "approval-sales@smart-crm.local", "password": "Sales@2026"})
        sales_headers = {"Authorization": f"Bearer {sales_login.json()['token']}"}
        reminder_response = client.post(
            f"/api/order-approvals/{approval_response.json()['id']}/reminders",
            json={"message": "请销售经理在 SLA 截止前处理。"},
            headers=sales_headers,
        )
        denied_assignment = client.post(
            f"/api/order-approvals/{approval_response.json()['id']}/assignment",
            json={"reviewer": "王蕾", "comment": "销售尝试转派审批。"},
            headers=sales_headers,
        )
        assignment_response = client.post(
            f"/api/order-approvals/{approval_response.json()['id']}/assignment",
            json={"reviewer": "王蕾", "comment": "转派给销售经理王蕾处理。"},
        )
        denied_decision = client.post(
            f"/api/order-approvals/{approval_response.json()['id']}/decision",
            json={"decision": "approved"},
            headers=sales_headers,
        )
        decision_response = client.post(
            f"/api/order-approvals/{approval_response.json()['id']}/decision",
            json={"decision": "approved", "comment": "库存与交付资源已复核，同意确认。"},
        )
        second_decision = client.post(
            f"/api/order-approvals/{approval_response.json()['id']}/decision",
            json={"decision": "rejected"},
        )
        orders_after = client.get("/api/orders").json()
        audit_logs = client.get("/api/business-audit-logs?entity_type=order_approval").json()

    assert order_response.status_code == 201
    assert approval_response.status_code == 201
    approval_payload = approval_response.json()
    assert approval_payload["status"] == "pending"
    assert approval_payload["order_id"] == order_id
    assert approval_payload["owner"] == "李伟超"
    assert "AI" in approval_payload["risk_summary"]
    assert approval_payload["risk_level"] == "medium"
    assert approval_payload["sla_due_at"]
    assert approval_payload["sla_status"] in {"on_track", "due_soon"}
    assert approval_payload["sla_hours_remaining"] is not None
    assert duplicate_response.status_code == 400
    assert any(item["id"] == approval_payload["id"] for item in pending_approvals)
    assert any(item["id"] == approval_payload["id"] for item in medium_approvals)
    assert reminder_response.status_code == 200
    assert denied_assignment.status_code == 403
    assert assignment_response.status_code == 200
    assert assignment_response.json()["reviewer"] == "王蕾"
    assert denied_decision.status_code == 403
    assert decision_response.status_code == 200
    assert decision_response.json()["status"] == "approved"
    assert second_decision.status_code == 400
    assert next(order for order in orders_after if order["id"] == order_id)["status"] == "confirmed"
    audit_actions = {(log["entity_type"], log["action"]) for log in audit_logs}
    assert ("order_approval", "submit_approval") in audit_actions
    assert ("order_approval", "remind_approval") in audit_actions
    assert ("order_approval", "assign_approval") in audit_actions
    assert ("order_approval", "approve") in audit_actions


def test_order_approval_policy_blocks_sales_direct_confirmation() -> None:
    with TestClient(app) as client:
        sales_login = client.post("/api/auth/login", json={"account": "sales@smart-crm.local", "password": "SmartCRM@2026"})
        sales_headers = {"Authorization": f"Bearer {sales_login.json()['token']}"}
        manager_login = client.post("/api/auth/login", json={"account": "manager@smart-crm.local", "password": "SmartCRM@2026"})
        manager_headers = {"Authorization": f"Bearer {manager_login.json()['token']}"}

        customer = client.get("/api/customers", headers=sales_headers).json()[0]
        products = client.get("/api/products", headers=sales_headers).json()
        product = next(item for item in products if item["sku"] == "SERV-DEPLOY-018")
        order_response = client.post(
            "/api/orders",
            json={
                "customer_id": customer["id"],
                "owner": "赵可",
                "region": "华南",
                "currency": "CNY",
                "status": "draft",
                "order_date": "2026-06-23",
                "due_date": "2026-06-27",
                "notes": "审批策略拦截测试订单",
                "created_by_ai": True,
                "ai_confidence_score": 0.58,
                "items": [
                    {
                        "product_id": product["id"],
                        "quantity": 4,
                        "unit_price": product["unit_price"],
                    }
                ],
            },
            headers=sales_headers,
        )
        order_id = order_response.json()["id"]
        denied_confirmation = client.patch(
            f"/api/orders/{order_id}",
            json={"status": "confirmed"},
            headers=sales_headers,
        )
        approval_response = client.post(
            f"/api/orders/{order_id}/approval-requests",
            json={"reason": "AI 低置信度且高金额订单，申请经理确认。"},
            headers=sales_headers,
        )
        pending_denied_confirmation = client.patch(
            f"/api/orders/{order_id}",
            json={"status": "confirmed"},
            headers=sales_headers,
        )
        decision_response = client.post(
            f"/api/order-approvals/{approval_response.json()['id']}/decision",
            json={"decision": "approved", "comment": "合同金额和交付排期已复核。"},
            headers=manager_headers,
        )
        orders_after = client.get("/api/orders", headers=sales_headers).json()

    assert sales_login.status_code == 200
    assert manager_login.status_code == 200
    assert order_response.status_code == 201
    assert denied_confirmation.status_code == 403
    assert "审批策略" in denied_confirmation.json()["detail"]
    assert approval_response.status_code == 201
    assert "高价值订单" in approval_response.json()["risk_summary"]
    assert "AI" in approval_response.json()["risk_summary"]
    assert approval_response.json()["risk_level"] in {"high", "critical"}
    assert approval_response.json()["sla_due_at"]
    assert pending_denied_confirmation.status_code == 403
    assert "待审批申请" in pending_denied_confirmation.json()["detail"]
    assert decision_response.status_code == 200
    assert decision_response.json()["status"] == "approved"
    assert next(order for order in orders_after if order["id"] == order_id)["status"] == "confirmed"


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


def test_consistency_checks_detect_cross_table_issues() -> None:
    with TestClient(app) as client:
        clean_response = client.get("/api/system/consistency-checks")
        with Session(main_module.engine) as session:
            order = session.exec(select(SalesOrder)).first()
            assert order is not None
            order.total_amount += 88
            session.add(order)
            session.commit()
        broken_response = client.get("/api/system/consistency-checks")

    assert clean_response.status_code == 200
    clean_payload = clean_response.json()
    assert clean_payload["overall_status"] == "ok"
    assert clean_payload["issue_count"] == 0
    assert clean_payload["ok_count"] >= 5

    assert broken_response.status_code == 200
    broken_payload = broken_response.json()
    assert broken_payload["overall_status"] == "warning"
    assert broken_payload["issue_count"] >= 1
    assert any(check["category"] == "订单金额合计" and check["status"] == "issue" for check in broken_payload["checks"])


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


def test_copilot_ask_uses_crm_context_and_audit(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        response = client.post("/api/copilot/ask", json={"question": "本周最需要优先跟进哪些客户？"})
        audit_logs = client.get("/api/ai-audit-logs", params={"operation": "copilot_ask"}).json()

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "本周最需要优先跟进哪些客户？"
    assert payload["answer"]
    assert payload["next_actions"]
    assert payload["evidence"]
    assert any("客户" in item and "商机" in item for item in payload["evidence"])
    assert payload["fallback_used"] is True
    assert any(log["operation"] == "copilot_ask" and log["fallback_used"] is True for log in audit_logs)


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
