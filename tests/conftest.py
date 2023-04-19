import os
from typing import Generator

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, clear_mappers, sessionmaker

from src.allocation.adapters.orm import metadata, start_mappers

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
def session_factory(
    in_memory_db: Engine,
) -> Generator[sessionmaker[Session], None, None]:
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()


@pytest.fixture
def file_session_factory(
    file_db: Engine,
) -> Generator[sessionmaker[Session], None, None]:
    start_mappers()
    yield sessionmaker(bind=file_db)
    clear_mappers()


@pytest.fixture
def session(in_memory_db: Engine) -> Generator[Session, None, None]:
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


@pytest.fixture
def client(file_session_factory: sessionmaker[Session]) -> httpx.Client:
    from fastapi.testclient import TestClient

    from src.allocation.adapters import unit_of_work
    from src.allocation.lib.config import get_default_uow
    from src.main import app

    def get_default_uow_override() -> unit_of_work.AbstractUnitOfWork:
        return unit_of_work.SqlAlchemyUnitOfWork(
            session_factory=file_session_factory
        )

    app.dependency_overrides[get_default_uow] = get_default_uow_override

    return TestClient(app=app)
