from typing import List, Optional, Set

from sqlalchemy.orm import Session

from src.allocation.domain.model import aggregate
from src.allocation.repositories.abstract import AbstractRepository


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session) -> None:
        self.session = session
        super().__init__()

    def add(self, product: aggregate.Product) -> None:
        self.session.add(product)

    def get(self, sku: str) -> Optional[aggregate.Product]:
        return self.session.query(aggregate.Product).filter_by(sku=sku).first()

    def list(self) -> List[aggregate.Product]:
        return self.session.query(aggregate.Product).all()


class FakeRepository(AbstractRepository):
    def __init__(self, products: Set[aggregate.Product]) -> None:
        self._products = set(products)
        super().__init__()

    def add(self, product: aggregate.Product) -> None:
        self._products.add(product)

    def get(self, sku: str) -> Optional[aggregate.Product]:
        try:
            return next(p for p in self._products if p.sku == sku)
        except StopIteration:
            return None

    def list(self) -> List[aggregate.Product]:
        return list(self._products)
