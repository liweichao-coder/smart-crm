from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, SQLModel, select

from . import database
from .consistency import build_consistency_payload
from .config import settings
from .models import (  # noqa: F401
    AIInteractionLog,
    AuthUser,
    BusinessAuditLog,
    CaptureDraft,
    Contact,
    CopilotRecommendation,
    CustomerActivity,
    Customer,
    InventoryMovement,
    OrderApprovalRequest,
    OrderItem,
    Organization,
    Product,
    ReportSnapshot,
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
    ("customer_activities", CustomerActivity, 17),
    ("leads_opportunities", SalesLead, 15),
    ("support_cases", SupportCase, 9),
    ("tasks", TaskItem, 9),
    ("sales_goals", SalesGoal, 4),
    ("orders", SalesOrder, 12),
    ("order_items", OrderItem, 22),
    ("inventory_movements", InventoryMovement, 22),
    ("order_approvals", OrderApprovalRequest, 2),
    ("capture_drafts", CaptureDraft, 1),
    ("copilot_recommendations", CopilotRecommendation, 1),
    ("ai_interactions", AIInteractionLog, 2),
    ("business_audit_logs", BusinessAuditLog, 3),
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


def migrate_db() -> None:
    database.create_db_and_tables()


def sqlite_database_path() -> Path:
    url = database.engine.url
    if url.get_backend_name() != "sqlite":
        raise RuntimeError("backup and restore commands currently support SQLite databases only")

    database_name = url.database
    if not database_name or database_name == ":memory:":
        raise RuntimeError("backup and restore commands require a file-backed SQLite database")

    return Path(database_name).resolve()


def resolve_backup_path(output: str | None = None) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"smart_crm_backup_{timestamp}.db"

    if not output:
        directory = sqlite_database_path().parent / "backups"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / filename

    candidate = Path(output).resolve()
    if candidate.exists() and candidate.is_dir():
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate / filename

    if candidate.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        candidate.parent.mkdir(parents=True, exist_ok=True)
        return candidate

    candidate.mkdir(parents=True, exist_ok=True)
    return candidate / filename


def backup_db(output: str | None = None) -> Path:
    database.create_db_and_tables()
    source_path = sqlite_database_path()
    if not source_path.exists():
        raise RuntimeError(f"SQLite database file does not exist: {source_path}")

    backup_path = resolve_backup_path(output)
    with sqlite3.connect(source_path) as source, sqlite3.connect(backup_path) as target:
        source.backup(target)

    return backup_path


def restore_db(backup_path: str) -> Path:
    source_path = Path(backup_path).resolve()
    if not source_path.exists() or not source_path.is_file():
        raise RuntimeError(f"Backup file does not exist: {source_path}")

    target_path = sqlite_database_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    database.engine.dispose()
    shutil.copy2(source_path, target_path)
    database.create_db_and_tables()
    return target_path


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
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("reset-db", help="Drop, recreate, and seed the classroom demo database")
    subparsers.add_parser("seed-db", help="Create tables and seed demo data when missing")
    subparsers.add_parser("migrate", help="Create missing tables and run lightweight migrations without resetting data")
    subparsers.add_parser("doctor", help="Check demo data scale and cross-table consistency")
    backup_parser = subparsers.add_parser("backup-db", help="Create a SQLite backup snapshot for teammate handoff")
    backup_parser.add_argument("output", nargs="?", help="Optional output .db file or directory")
    restore_parser = subparsers.add_parser("restore-db", help="Restore the SQLite database from a backup snapshot")
    restore_parser.add_argument("backup_path", help="Path to a .db/.sqlite backup file")
    args = parser.parse_args()

    if args.command == "reset-db":
        reset_db()
        print("Smart CRM demo database reset and seeded.")
    elif args.command == "seed-db":
        seed_db()
        print("Smart CRM demo database seeded if it was empty.")
    elif args.command == "migrate":
        migrate_db()
        print("Smart CRM database schema migrated. Existing data was preserved.")
    elif args.command == "backup-db":
        backup_path = backup_db(args.output)
        print(f"Smart CRM database backup written to: {backup_path}")
    elif args.command == "restore-db":
        target_path = restore_db(args.backup_path)
        print(f"Smart CRM database restored to: {target_path}")
    elif args.command == "doctor":
        raise SystemExit(doctor())


if __name__ == "__main__":
    main()
