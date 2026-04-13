from fastapi.testclient import TestClient

from app.main import app


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
