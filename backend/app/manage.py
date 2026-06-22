from __future__ import annotations

import argparse

from sqlmodel import Session, SQLModel, select

from . import database
from .consistency import build_consistency_payload
from .config import settings
from .models import (  # noqa: F401
    AIInteractionLog,
    AuthUser,
    BusinessAuditLog,
    Contact,
    CopilotRecommendation,
    CustomerActivity,
    Customer,
    InventoryMovement,
    OrderApprovalRequest,
    OrderItem,
    Organization,
    Product,
    SalesGoal,
    SalesLead,
    SalesOrder,
    SupportCase,
    TaskItem,
    UserPreference,
)
from .seed import seed_data


DEMO_DATA_TARGETS = [
    ("organizations", Organization, 1),
    ("users", AuthUser, 5),
    ("customers", Customer, 12),
    ("products", Product, 10),
    ("contacts", Contact, 12),
    ("customer_activities", CustomerActivity, 16),
    ("leads_opportunities", SalesLead, 15),
    ("support_cases", SupportCase, 8),
    ("tasks", TaskItem, 8),
    ("sales_goals", SalesGoal, 4),
    ("orders", SalesOrder, 12),
    ("order_items", OrderItem, 22),
    ("inventory_movements", InventoryMovement, 22),
    ("order_approvals", OrderApprovalRequest, 2),
]


def reset_db() -> None:
    SQLModel.metadata.drop_all(database.engine)
    database.create_db_and_tables()
    with Session(database.engine) as session:
        seed_data(session)


def seed_db() -> None:
    database.create_db_and_tables()
    with Session(database.engine) as session:
        seed_data(session)


def collect_demo_stats(session: Session) -> list[tuple[str, int, int]]:
    return [(label, len(session.exec(select(model)).all()), minimum) for label, model, minimum in DEMO_DATA_TARGETS]


def doctor() -> int:
    database.create_db_and_tables()
    with Session(database.engine) as session:
        stats = collect_demo_stats(session)
        consistency = build_consistency_payload(session)

    print("Smart CRM environment doctor")
    print(f"- database_url: {settings.database_url}")
    print(f"- llm_base_url: {settings.llm_base_url}")
    print(f"- llm_model: {settings.llm_model}")
    print(f"- llm_api_key: {'configured' if settings.llm_api_key else 'not configured, rule fallback enabled'}")
    print("- demo data:")
    for label, count, minimum in stats:
        status = "OK" if count >= minimum else "LOW"
        print(f"  {label}: {count} / target {minimum} [{status}]")
    print("- consistency:")
    print(
        f"  status: {consistency['overall_status']} / issues {consistency['issue_count']} "
        f"(critical {consistency['critical_count']}, warning {consistency['warning_count']})"
    )

    missing = [(label, count, minimum) for label, count, minimum in stats if count < minimum]
    if missing:
        print("Doctor result: demo data is below target. Run `python -m app.manage reset-db` before a presentation.")
        return 1
    if consistency["issue_count"]:
        print("Doctor result: cross-table consistency issues found. Open Operation Audit for details before a presentation.")
        return 1

    print("Doctor result: environment is ready for a classroom demo.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart CRM database management")
    parser.add_argument("command", choices=["reset-db", "seed-db", "doctor"], help="Database command to run")
    args = parser.parse_args()

    if args.command == "reset-db":
        reset_db()
        print("Smart CRM demo database reset and seeded.")
    elif args.command == "seed-db":
        seed_db()
        print("Smart CRM demo database seeded if it was empty.")
    elif args.command == "doctor":
        raise SystemExit(doctor())


if __name__ == "__main__":
    main()
