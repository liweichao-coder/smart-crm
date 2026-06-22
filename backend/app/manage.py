from __future__ import annotations

import argparse

from sqlmodel import Session, SQLModel

from .database import create_db_and_tables, engine
from .models import Customer, InventoryMovement, OrderItem, Product, SalesLead, SalesOrder  # noqa: F401
from .seed import seed_data


def reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()
    with Session(engine) as session:
        seed_data(session)


def seed_db() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        seed_data(session)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart CRM database management")
    parser.add_argument("command", choices=["reset-db", "seed-db"], help="Database command to run")
    args = parser.parse_args()

    if args.command == "reset-db":
        reset_db()
        print("Smart CRM demo database reset and seeded.")
    elif args.command == "seed-db":
        seed_db()
        print("Smart CRM demo database seeded if it was empty.")


if __name__ == "__main__":
    main()
