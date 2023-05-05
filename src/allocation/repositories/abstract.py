import abc
from typing import List, Optional, Set

from src.allocation.domain.model import aggregate


class AbstractRepository(abc.ABC):
    def __init__(self) -> None:
        self.seen: Set[aggregate.Product] = set()
        super().__init__()

    @abc.abstractmethod
    def add(self, product: aggregate.Product) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, sku: str) -> Optional[aggregate.Product]:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[aggregate.Product]:
        raise NotImplementedError
