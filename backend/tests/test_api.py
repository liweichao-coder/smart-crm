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
