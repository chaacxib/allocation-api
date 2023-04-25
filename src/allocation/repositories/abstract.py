import abc
from typing import List, Optional

from src.allocation.domain.model import aggregate


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, product: aggregate.Product) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, sku: str) -> Optional[aggregate.Product]:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[aggregate.Product]:
        raise NotImplementedError
