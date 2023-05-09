from src.allocation.lib import base_types


class OutOfStock(base_types.Event):
    sku: str
