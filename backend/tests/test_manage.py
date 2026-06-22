from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app import database
from app import manage
from app.models import Customer


def use_memory_database(monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(database, "engine", test_engine)
    return test_engine


def test_doctor_passes_after_demo_reset(monkeypatch, capsys) -> None:
    test_engine = use_memory_database(monkeypatch)

    manage.reset_db()
    result = manage.doctor()
    output = capsys.readouterr().out

    assert result == 0
    assert "environment is ready" in output
    assert "customers: 12 / target 12 [OK]" in output
    assert "customer_activities: 16 / target 16 [OK]" in output
    assert "orders: 12 / target 12 [OK]" in output

    SQLModel.metadata.drop_all(test_engine)


def test_doctor_warns_when_demo_data_is_missing(monkeypatch, capsys) -> None:
    test_engine = use_memory_database(monkeypatch)
    database.create_db_and_tables()

    result = manage.doctor()
    output = capsys.readouterr().out

    assert result == 1
    assert "below target" in output
    assert "customers: 0 / target 12 [LOW]" in output
    assert "reset-db" in output

    SQLModel.metadata.drop_all(test_engine)


def test_backup_and_restore_sqlite_database(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "smart_crm.db"
    test_engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    monkeypatch.setattr(database, "engine", test_engine)

    manage.reset_db()
    backup_path = manage.backup_db(str(tmp_path / "snapshots"))

    assert backup_path.exists()
    assert backup_path.parent.name == "snapshots"

    with Session(database.engine) as session:
        customer = session.exec(select(Customer)).first()
        assert customer is not None
        session.delete(customer)
        session.commit()
        assert len(session.exec(select(Customer)).all()) == 11

    restored_path = manage.restore_db(str(backup_path))

    assert restored_path == database_path.resolve()
    with Session(database.engine) as session:
        assert len(session.exec(select(Customer)).all()) == 12

    SQLModel.metadata.drop_all(test_engine)
    test_engine.dispose()
