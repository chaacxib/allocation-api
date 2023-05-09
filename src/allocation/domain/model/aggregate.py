import datetime
from typing import List, Optional, Set

import pydantic

from src.allocation.domain.model import events as domain_events
from src.allocation.lib import base_types


class OutOfStockException(Exception):
    """Raise when there's no stock to allocate an order"""


class OrderLine(base_types.ValueObject):
    """Client order for an specific product

    Attributes:
        sku (str): Unique product identifier. ex. RED-CHAIR
        order_id (str): Unique order identifier
        qty (int): Number of product units for the order
    """

    sku: str
    order_id: str
    qty: int = pydantic.Field(..., gt=0)


class Batch(base_types.Entity):
    """Batch of stock ordered by the purchasing department

    Attributes:
        id (str): Unique identifier for the batch order.
        sku (str): Unique product identifier.
        eta (date): Date when the Batch should arrive to the Warehouse.
        purchased_quantity (int): Number of product units puchased for the batch.
    """

    sku: str
    eta: Optional[datetime.date]
    purchased_quantity: int
    _allocations: Set[OrderLine] = pydantic.PrivateAttr(default_factory=set)

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

    def can_allocate(self, line: OrderLine) -> bool:
        """Validates if there are available resources to allocate a new order

        Args:
            line (OrderLine): Order to allocate on this Batch

        Returns:
            bool: Returns true when is possible
            to allocate the order line on this batch
        """
        return self.sku == line.sku and self.available_quantity >= line.qty

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
        return self.purchased_quantity - self.allocated_quantity

    @property
    def allocations(self) -> Set[OrderLine]:
        """Read OrderLines allocated on this batch.

        Returns:
            _allocations (Set[OrderLine]): Collection of order lines
            allocated on Batch.
        """
        return self._allocations


class Product(base_types.Aggregate):
    """Client order for an specific product

    Attributes:
        sku (str): Unique product identifier. ex. RED-CHAIR.
        batches (List[Batch]): List of order batches associates to the product.
    """

    sku: str = pydantic.Field(primary_key=True)
    batches: List[Batch] = pydantic.Field(default_factory=list)

    def add_batch(self, batch: Batch) -> None:
        self.batches.append(batch)

    def allocate(self, line: OrderLine) -> Optional[str]:
        """Allocates a new order on the nearest available stock batch order

        Args:
            line (OrderLine): New order to allocate

        Raises:
            OutOfStockError: Raise when there's no stock to allocate an order

        Returns:
            reference (str): Unique identifier of the batch where
            the order was allocated
        """
        try:
            batch = next(
                b for b in sorted(self.batches) if b.can_allocate(line=line)
            )

            batch.allocate(line=line)
            self._update_version()

            return batch.id
        except StopIteration:
            self.events.append(domain_events.OutOfStock(sku=line.sku))
            return None
