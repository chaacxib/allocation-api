from datetime import date
from typing import List, Optional, Set

import pydantic


class OutOfStockError(Exception):
    """Raise when there's no stock to allocate an order"""


class OrderLine(pydantic.BaseModel):
    """Client order for an specific product

    Attributes:
        sku (str): Unique product identifier. ex. RED-CHAIR
        qty (int): Number of product units for the order
        order_id (str): Unique order identifier
    """

    sku: str
    qty: int = pydantic.Field(..., gt=0)
    order_id: str

    class Config:
        frozen = True


class Batch:
    """Batch of stock ordered by the purchasing department

    Attributes:
        reference (str): Unique identifier for the batch order
        sku (str): Unique product identifier.
        eta (date): Date when the Batch should arrive to the Warehouse.
    """

    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations: Set[OrderLine] = set()

    def __repr__(self) -> str:
        return f"<Batch {self.reference}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self) -> int:
        return hash(self.reference)

    def __gt__(self, other: "Batch") -> bool:
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration as err:
        raise OutOfStockError(f"Out of stock for sku {line.sku}") from err
