import datetime
from typing import Optional

from src.allocation.lib import base_types


class OutOfStock(base_types.Event):
    sku: str


class BatchCreated(base_types.Event):
    ref: str
    sku: str
    qty: int
    eta: Optional[datetime.date] = None


class BatchQuantityChanged(base_types.Event):
    ref: str
    qty: int


class AllocationRequired(base_types.Event):
    order_id: str
    sku: str
    qty: int
