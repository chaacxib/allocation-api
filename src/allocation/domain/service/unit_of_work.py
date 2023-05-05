import abc
from typing import Annotated, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.allocation import repositories
from src.allocation.domain.service import messagebus
from src.allocation.lib import settings

SessionFactory = Annotated[sessionmaker[Session], sessionmaker]

_SETTINGS = settings.get_settings()
DEFAULT_SESSION_FACTORY: SessionFactory = sessionmaker(
    bind=create_engine(
        url=_SETTINGS.database.mysql_uri,
        isolation_level="REPEATABLE READ",
    )
)


class AbstractUnitOfWork(abc.ABC):
    products: repositories.AbstractRepository

    async def __aenter__(self) -> "AbstractUnitOfWork":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.rollback()

    async def commit(self) -> None:
        await self._commit()

    async def publish_events(self) -> None:
        for product in self.products.seen:
            while product.events:
                event = product.events.pop(0)
                messagebus.handle(event)

    @abc.abstractmethod
    async def _commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self, session_factory: SessionFactory = DEFAULT_SESSION_FACTORY
    ) -> None:
        self.session_factory = session_factory
        super().__init__()

    async def __aenter__(self) -> AbstractUnitOfWork:
        self.session: Session = self.session_factory()
        self.products = repositories.SqlAlchemyRepository(session=self.session)
        return await super().__aenter__()

    async def __exit__(self, *args: Any) -> None:
        await super().__aexit__(*args)
        self.session.close()

    async def _commit(self) -> None:
        self.session.commit()

    async def rollback(self) -> None:
        self.session.rollback()


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.products = repositories.FakeRepository(set())
        self.committed = False
        super().__init__()

    async def _commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        ...
