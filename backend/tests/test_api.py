import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import database
from app.config import settings
import app.main as main_module
from app.seed import seed_data


app = main_module.app


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


def test_resource_collection_payloads() -> None:
    endpoints = {
        "/api/customers": "company",
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

    for response in responses.values():
        assert response.status_code == 201

    assert responses["customer"].json()["company"] == "测试智能制造"
    assert responses["lead"].json()["stage"] == "proposal"
    assert responses["goal"].json()["progress"] == 50
    assert any(customer["company"] == "测试智能制造" for customer in customer_list)
    assert any(lead["title"] == "测试智能制造 CRM 升级" for lead in lead_list)


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


def test_copilot_summary_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        response = client.get("/api/copilot/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["insights"]
    assert payload["top_opportunity"]["rule_score"] >= 0
    assert payload["forecast_amount"] >= 0
    assert payload["fallback_used"] is True


def test_copilot_follow_up_by_lead(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", "")
    with TestClient(app) as client:
        lead = client.get("/api/leads").json()[0]
        response = client.post("/api/copilot/follow-up", json={"lead_id": lead["id"]})

    assert response.status_code == 200
    payload = response.json()
    assert payload["message_draft"]
    assert payload["next_best_action"]
    assert payload["fallback_used"] is True


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
