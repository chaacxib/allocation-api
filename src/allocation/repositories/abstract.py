import abc
from typing import Optional, Set

from src.allocation.domain.model import aggregate


class AbstractRepository(abc.ABC):
    def __init__(self) -> None:
        self.seen: Set[aggregate.Product] = set()
        super().__init__()

    def add(self, product: aggregate.Product) -> None:
        self._add(product)
        self.seen.add(product)

    def get(self, sku: str) -> Optional[aggregate.Product]:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: aggregate.Product) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku: str) -> Optional[aggregate.Product]:
        raise NotImplementedError
