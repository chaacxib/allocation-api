from datetime import date
from typing import List, Optional, Set

import pydantic
from pydantic.dataclasses import dataclass


class OutOfStockError(Exception):
    """Raise when there's no stock to allocate an order"""


@dataclass(unsafe_hash=True)
class OrderLine:
    """Client order for an specific product

    Attributes:
        sku (str): Unique product identifier. ex. RED-CHAIR
        order_id (str): Unique order identifier
        qty (int): Number of product units for the order
    """

    sku: str
    order_id: str
    qty: int = pydantic.Field(..., gt=0)


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
        super().__init__()

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
        """Allocates an order to this batch if possible

        Args:
            line (OrderLine): Order to allocate on this Batch
        """
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> None:
        """Removes order from batch if allocated

        Args:
            line (OrderLine): Order to deallocate from this Batch
        """
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        """Total allocated items on this batch

        Returns:
            total (int): Quantity of products allocated.
        """
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        """Available items on the Batch.

        Returns:
            quantity (int): Quantity of products available to allocate.
        """
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        """Validates if there are available resources to allocate a new order

        Args:
            line (OrderLine): Order to allocate on this Batch

        Returns:
            bool: Returns true when is possible
            to allocate the order line on this batch
        """
        return self.sku == line.sku and self.available_quantity >= line.qty


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    """Allocates a new order on the nearest available stock batch order

    Args:
        line (OrderLine): New order to allocate
        batches (List[Batch]): List of available stock batches

    Raises:
        OutOfStockError: Raise when there's no stock to allocate an order

    Returns:
        reference (str): Unique identifier where the order was allocated
    """
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration as err:
        raise OutOfStockError(f"Out of stock for sku {line.sku}") from err
