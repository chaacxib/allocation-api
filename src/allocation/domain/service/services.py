from typing import Optional

from src.allocation.domain.model import aggregate, dto
from src.allocation.domain.service import unit_of_work


class InvalidSkuException(Exception):
    """Raise when there's no batch with the provided sku"""

    ...


async def add_batch(
    dto: dto.BatchInput,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """Service to save a new order batch

    Args:
        dto (BatchInput): New batch data to store
        uow (AbstractUnitOfWork): Unit of Work used for the persistance layer
    """
    _batch = aggregate.Batch(
        id=dto.reference,
        sku=dto.sku,
        eta=dto.eta,
        purchased_quantity=dto.purchased_quantity,
    )
    async with uow:
        product = uow.products.get(sku=dto.sku)
        if product is None:
            product = aggregate.Product(sku=dto.sku)
        product.add_batch(_batch)
        uow.products.add(product=product)
        await uow.commit()


async def allocate(
    dto: dto.OrderLineInput,
    uow: unit_of_work.AbstractUnitOfWork,
) -> Optional[str]:
    """Service to allocate an order and persist the data

    Args:
        dto (OrderLineInput): New order data to allocate
        uow (AbstractUnitOfWork): Unit of Work used for the persistance layer

    Raises:
        InvalidSkuException: Raise when there's no batch with the provided sku

    Returns:
        batch_ref (str): Reference of the batch where the order is allocated
    """
    _line = aggregate.OrderLine(sku=dto.sku, order_id=dto.order_id, qty=dto.qty)
    async with uow:
        product = uow.products.get(sku=dto.sku)
        if product is None:
            raise InvalidSkuException(f"Invalid sku {dto.sku}")
        batch_ref = product.allocate(line=_line)
        await uow.commit()
    return batch_ref
