from typing import Any, Callable, Optional, Set

import pydash
from sqlalchemy.orm import Session

from src.allocation.adapters import orm
from src.allocation.domain.model import aggregate
from src.allocation.repositories.abstract import AbstractRepository


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session) -> None:
        self.session = session
        super().__init__()

    def _add(self, product: aggregate.Product) -> None:
        _new_product = orm.ProductMapper.from_domain(product)
        self.session.merge(_new_product)

    def _get(self, sku: str) -> Optional[aggregate.Product]:
        _product = self.session.get(orm.ProductMapper, sku)
        if _product:
            return aggregate.Product.from_orm(_product)

    def _get_by_batchref(self, ref: str) -> Optional[aggregate.Product]:
        _product = (
            self.session.query(orm.ProductMapper)
            .join(orm.BatchMapper)
            .filter(orm.BatchMapper.id == ref)
            .first()
        )
        if _product:
            return aggregate.Product.from_orm(_product)


class FakeRepository(AbstractRepository):
    def __init__(self, products: Set[aggregate.Product]) -> None:
        self._products = set(products)
        super().__init__()

    def _add(self, product: aggregate.Product) -> None:
        self._products.add(product)

    def _get(self, sku: str) -> Optional[aggregate.Product]:
        _product: Any = pydash.collections.find(self._products, {"sku": sku})
        if isinstance(_product, aggregate.Product):
            return _product

    def _get_by_batchref(self, ref: str) -> Optional[aggregate.Product]:
        batches_filter: Callable[[aggregate.Product], bool] = (
            lambda p: pydash.collections.find(p.batches, {"id": ref}) is not None
        )
        _product: Any = pydash.collections.find(self._products, batches_filter)
        if isinstance(_product, aggregate.Product):
            return _product
