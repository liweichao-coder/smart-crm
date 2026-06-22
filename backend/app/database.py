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

        approval_exists = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='orderapprovalrequest'")
        ).first()
        if approval_exists:
            approval_columns = {
                row[1] for row in connection.execute(text("PRAGMA table_info(orderapprovalrequest)")).fetchall()
            }
            if "risk_level" not in approval_columns:
                connection.execute(
                    text("ALTER TABLE orderapprovalrequest ADD COLUMN risk_level VARCHAR NOT NULL DEFAULT 'medium'")
                )
            if "sla_due_at" not in approval_columns:
                connection.execute(text("ALTER TABLE orderapprovalrequest ADD COLUMN sla_due_at DATETIME"))
                connection.execute(
                    text(
                        """
                        UPDATE orderapprovalrequest
                        SET sla_due_at = datetime(created_at, '+24 hours')
                        WHERE status = 'pending' AND sla_due_at IS NULL
                        """
                    )
                )

        recommendation_exists = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='copilotrecommendation'")
        ).first()
        if recommendation_exists:
            recommendation_columns = {
                row[1] for row in connection.execute(text("PRAGMA table_info(copilotrecommendation)")).fetchall()
            }
            recommendation_column_defs = {
                "feedback_status": "VARCHAR NOT NULL DEFAULT ''",
                "feedback_rating": "INTEGER NOT NULL DEFAULT 0",
                "feedback_note": "VARCHAR NOT NULL DEFAULT ''",
                "feedback_by": "VARCHAR NOT NULL DEFAULT ''",
                "feedback_at": "DATETIME",
            }
            for column_name, column_def in recommendation_column_defs.items():
                if column_name not in recommendation_columns:
                    connection.execute(text(f"ALTER TABLE copilotrecommendation ADD COLUMN {column_name} {column_def}"))


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    run_lightweight_migrations()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
