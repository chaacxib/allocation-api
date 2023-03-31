import os
from typing import Any, Callable, Generator, List, Set, Tuple

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, clear_mappers, sessionmaker
from sqlalchemy.sql import text

from src.allocation.adapters.orm import metadata, start_mappers
from src.main import app

_TEST_DB_FILE: str = ".pytest_cache/sqlite_db.db"


@pytest.fixture
def in_memory_db() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def file_db() -> Generator[Engine, None, None]:
    engine = create_engine(f"sqlite:///{_TEST_DB_FILE}")
    metadata.create_all(engine)
    yield engine
    if os.path.exists(_TEST_DB_FILE):
        os.remove(_TEST_DB_FILE)


@pytest.fixture
def session(in_memory_db: Engine) -> Generator[Session, None, None]:
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


@pytest.fixture
def file_session(file_db: Engine) -> Generator[Session, None, None]:
    start_mappers()
    yield sessionmaker(bind=file_db)()
    clear_mappers()


@pytest.fixture
def add_stock(file_session: Session) -> Generator[Callable[..., None], None, None]:
    batches_added: Set[str] = set()
    skus_added: Set[str] = set()

    def _add_stock(lines: List[Tuple[str, str, int, str]]) -> None:
        for ref, sku, qty, eta in lines:
            file_session.execute(
                statement=text(
                    "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
                    " VALUES (:ref, :sku, :qty, :eta)"
                ),
                params=dict(ref=ref, sku=sku, qty=qty, eta=eta),
            )
            [[batch_id]] = file_session.execute(
                statement=text(
                    "SELECT id FROM batches WHERE reference=:ref AND sku=:sku"
                ),
                params=dict(ref=ref, sku=sku),
            )
            batches_added.add(batch_id)
            skus_added.add(sku)
        file_session.commit()

    yield _add_stock

    for batch_id in batches_added:
        file_session.execute(
            statement=text("DELETE FROM allocations WHERE batch_id=:batch_id"),
            params=dict(batch_id=batch_id),
        )
        file_session.execute(
            statement=text("DELETE FROM batches WHERE id=:batch_id"),
            params=dict(batch_id=batch_id),
        )
    for sku in skus_added:
        file_session.execute(
            statement=text("DELETE FROM order_lines WHERE sku=:sku"),
            params=dict(sku=sku),
        )
    file_session.commit()


@pytest.fixture
def client() -> httpx.Client:
    return TestClient(app=app)


@pytest.fixture
def mock_config_get_session(mocker: Any, file_session: Session) -> None:
    mocker.patch(
        "src.allocation.routers.entrypoints.config.get_session",
        return_value=file_session,
    )
