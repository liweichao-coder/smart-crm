from collections.abc import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from .config import settings


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def run_lightweight_migrations() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as connection:
        table_exists = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='customer'")
        ).first()
        if not table_exists:
            return
        columns = {row[1] for row in connection.execute(text("PRAGMA table_info(customer)")).fetchall()}
        if "owner" not in columns:
            connection.execute(text("ALTER TABLE customer ADD COLUMN owner VARCHAR NOT NULL DEFAULT '李伟超'"))
            contact_exists = connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='contact'")
            ).first()
            if contact_exists:
                connection.execute(
                    text(
                        """
                        UPDATE customer
                        SET owner = COALESCE(
                            (
                                SELECT contact.owner
                                FROM contact
                                WHERE contact.company = customer.company
                                ORDER BY contact.id ASC
                                LIMIT 1
                            ),
                            customer.contact_person,
                            '李伟超'
                        )
                        """
                    )
                )
            else:
                connection.execute(
                    text(
                        """
                        UPDATE customer
                        SET owner = COALESCE(customer.contact_person, '李伟超')
                        """
                    )
                )


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    run_lightweight_migrations()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
