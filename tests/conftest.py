import uuid
from typing import Generator

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.allocation.adapters.orm import Base


@pytest.fixture
def in_memory_db() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def file_db(tmpdir: str) -> Generator[Engine, None, None]:
    engine = create_engine(f"sqlite:///{tmpdir}/test-{uuid.uuid4()}.db")
    Base.metadata.create_all(engine)
    yield engine


@pytest.fixture
def session_factory(
    in_memory_db: Engine,
) -> Generator[sessionmaker[Session], None, None]:
    yield sessionmaker(bind=in_memory_db)


@pytest.fixture
def file_session_factory(
    file_db: Engine,
) -> Generator[sessionmaker[Session], None, None]:
    yield sessionmaker(bind=file_db)


@pytest.fixture
def session(in_memory_db: Engine) -> Generator[Session, None, None]:
    yield sessionmaker(bind=in_memory_db)()


@pytest.fixture
def client(file_session_factory: sessionmaker[Session]) -> httpx.Client:
    from fastapi.testclient import TestClient

    from src.allocation.domain.service import unit_of_work
    from src.allocation.lib.config import get_default_uow
    from src.main import app

    def get_default_uow_override() -> unit_of_work.AbstractUnitOfWork:
        return unit_of_work.SqlAlchemyUnitOfWork(
            session_factory=file_session_factory
        )

    app.dependency_overrides[get_default_uow] = get_default_uow_override

    return TestClient(app=app)
