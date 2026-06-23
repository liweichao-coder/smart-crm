from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_ACCOUNT = "demo@smart-crm.local"
DEFAULT_PASSWORD = "SmartCRM@2026"


class SmokeFailure(RuntimeError):
    pass


@dataclass
class SmokeClient:
    base_url: str
    timeout: float
    token: str = ""

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = Request(f"{self.base_url}{path}", data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                if not raw:
                    return None
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return json.loads(raw.decode("utf-8"))
                return raw.decode("utf-8", errors="replace")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SmokeFailure(f"{method} {path} returned {exc.code}: {detail}") from exc
        except URLError as exc:
            raise SmokeFailure(f"{method} {path} failed: {exc.reason}") from exc

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if params:
            path = f"{path}?{urlencode(params)}"
        return self.request("GET", path)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, payload or {})


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def items(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    raise SmokeFailure("Expected a list payload or a paginated payload with items.")


def assert_non_empty_list(label: str, payload: Any) -> list[Any]:
    values = items(payload)
    expect(bool(values), f"{label} should contain at least one item.")
    return values


def query(path: str, **params: Any) -> str:
    return f"{path}?{urlencode(params)}"


def run_smoke(client: SmokeClient, account: str, password: str, include_ai_write: bool) -> list[str]:
    passed: list[str] = []

    health = client.get("/api/health")
    expect(health.get("status") == "ok", f"/api/health status is {health.get('status')!r}.")
    expect(health.get("database", {}).get("connected") is True, "Database readiness is not connected.")
    expect("sk-" not in json.dumps(health), "/api/health leaked an API key-like token.")
    expect(health.get("consistency", {}).get("issue_count") == 0, "Consistency check has issues.")
    passed.append("readiness")

    login = client.post("/api/auth/login", {"account": account, "password": password})
    token = login.get("token")
    expect(isinstance(token, str) and len(token) >= 20, "Login did not return a bearer token.")
    client.token = token
    passed.append("login")

    me = client.get("/api/auth/me")
    expect(me.get("user", {}).get("email") == account, "Current user does not match the login account.")
    expect(me.get("organizations"), "Current session did not include organizations.")
    passed.append("current-user")

    sessions = assert_non_empty_list("auth sessions", client.get("/api/auth/sessions"))
    expect(any(session.get("current") for session in sessions), "Auth sessions did not mark the current session.")
    passed.append("sessions")

    dashboard = client.get("/api/dashboard")
    expect(len(dashboard.get("metrics", [])) >= 4, "Dashboard metrics are incomplete.")
    passed.append("dashboard")

    customers = assert_non_empty_list("customers", client.get(query("/api/customers", page=1, per_page=3)))
    products = assert_non_empty_list("products", client.get(query("/api/products", page=1, per_page=3)))
    contacts = assert_non_empty_list("contacts", client.get(query("/api/contacts", page=1, per_page=3)))
    leads = assert_non_empty_list("leads", client.get(query("/api/leads", page=1, per_page=3)))
    assert_non_empty_list("cases", client.get(query("/api/cases", page=1, per_page=3)))
    assert_non_empty_list("tasks", client.get(query("/api/tasks", page=1, per_page=3)))
    assert_non_empty_list("goals", client.get(query("/api/goals", page=1, per_page=3)))
    assert_non_empty_list("orders", client.get(query("/api/orders", page=1, per_page=3)))
    passed.append("core-resources")

    notifications = client.get("/api/notifications")
    expect(isinstance(notifications, list), "Notifications should return a list.")
    passed.append("notifications")

    sales_report = client.get("/api/reports/sales-performance")
    expect(len(sales_report.get("metrics", [])) >= 4, "Sales report metrics are incomplete.")
    approval_report = client.get("/api/reports/approval-performance")
    expect(len(approval_report.get("metrics", [])) >= 4, "Approval report metrics are incomplete.")
    passed.append("reports")

    matrix = client.get("/api/admin/permission-matrix")
    expect(matrix.get("roles"), "Permission matrix should contain roles.")
    assert_non_empty_list("team members", client.get(query("/api/admin/users", page=1, per_page=3)))
    passed.append("admin")

    consistency = client.get("/api/system/consistency-checks")
    expect(consistency.get("overall_status") == "ok", "Consistency API did not return ok.")
    passed.append("consistency")

    recommendations = client.get(query("/api/copilot/recommendations", page=1, per_page=3))
    expect(isinstance(items(recommendations), list), "Copilot recommendations should be list-shaped.")
    ai_audit = client.get(query("/api/ai-audit-logs", page=1, per_page=3))
    expect(isinstance(items(ai_audit), list), "AI audit logs should be list-shaped.")
    business_audit = client.get(query("/api/business-audit-logs", page=1, per_page=3))
    expect(isinstance(items(business_audit), list), "Business audit logs should be list-shaped.")
    passed.append("audit-and-copilot-history")

    if customers:
        workspace = client.get(f"/api/customers/{customers[0]['id']}/workspace")
        expect(workspace.get("health_profile", {}).get("score") is not None, "Customer workspace lacks health profile.")
        passed.append("customer-workspace")

    if include_ai_write:
        summary = client.get("/api/copilot/summary")
        expect(summary.get("insights"), "Copilot summary did not return insights.")
        if leads:
            follow_up = client.post("/api/copilot/follow-up", {"lead_id": leads[0]["id"]})
            expect(follow_up.get("message_draft"), "Copilot follow-up did not return a draft.")
        passed.append("ai-write")

    return passed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Smart CRM API smoke checks against a running backend.")
    parser.add_argument("--base-url", default=os.getenv("SMART_CRM_SMOKE_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--account", default=os.getenv("SMART_CRM_SMOKE_ACCOUNT", DEFAULT_ACCOUNT))
    parser.add_argument("--password", default=os.getenv("SMART_CRM_SMOKE_PASSWORD", DEFAULT_PASSWORD))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("SMART_CRM_SMOKE_TIMEOUT", "12")))
    parser.add_argument(
        "--include-ai-write",
        action="store_true",
        help="Also call Copilot summary and follow-up endpoints. These may write AI audit and recommendation records.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    base_url = args.base_url.rstrip("/")
    client = SmokeClient(base_url=base_url, timeout=args.timeout)
    try:
        passed = run_smoke(client, args.account, args.password, args.include_ai_write)
    except SmokeFailure as exc:
        print(f"SMOKE FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        if client.token:
            try:
                client.post("/api/auth/logout")
            except SmokeFailure as exc:
                print(f"SMOKE WARNING: logout failed: {exc}", file=sys.stderr)

    print(f"Smart CRM API smoke passed against {base_url}.")
    for label in passed:
        print(f"- {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
