from typing import Optional

from src.allocation.adapters import email
from src.allocation.domain.model import aggregate, events
from src.allocation.domain.service import unit_of_work


class InvalidSkuException(Exception):
    """Raise when there's no batch with the provided sku"""


class InvalidBatchReferenceException(Exception):
    """Raise when there's no batch with the provided reference"""


async def add_batch(
    event: events.BatchCreated,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """Service to save a new order batch

    Args:
        event (BatchQuantityChanged): Event that triggers this handler
        uow (AbstractUnitOfWork): Unit of Work used for the persistance layer
    """
    _batch = aggregate.Batch(
        id=event.ref,
        sku=event.sku,
        eta=event.eta,
        purchased_quantity=event.qty,
    )
    async with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = aggregate.Product(sku=event.sku)
        product.add_batch(_batch)
        uow.products.add(product=product)
        await uow.commit()


async def allocate(
    event: events.AllocationRequired,
    uow: unit_of_work.AbstractUnitOfWork,
) -> Optional[str]:
    """Service to allocate an order and persist the data

    Args:
        event (BatchQuantityChanged): Event that triggers this handler
        uow (AbstractUnitOfWork): Unit of Work used for the persistance layer

    Raises:
        InvalidSkuException: Raise when there's no batch with the provided sku

    Returns:
        batch_ref (str): Reference of the batch where the order is allocated
    """
    _line = aggregate.OrderLine(
        sku=event.sku, order_id=event.order_id, qty=event.qty
    )
    async with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            raise InvalidSkuException(f"Invalid sku {event.sku}")
        batch_ref = product.allocate(line=_line)
        await uow.commit()
    return batch_ref


async def change_batch_quantity(
    event: events.BatchQuantityChanged,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """Service to update stored batch quantity

    Args:
        event (BatchQuantityChanged): Event that triggers this handler
        uow (AbstractUnitOfWork): Unit of Work used for the persistance layer

    Raises:
        InvalidBatchReferenceException: Raise when there's no batch
        with the provided reference
    """
    async with uow:
        product = uow.products.get_by_batchref(ref=event.ref)
        if product is None:
            raise InvalidBatchReferenceException(
                f"Invalid Batch reference {event.ref}"
            )
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        await uow.commit()


async def send_out_of_stock_notification(
    event: events.OutOfStock,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """Service to send an email notification when a product is
    out of stock.

    Args:
        event (BatchQuantityChanged): Event that triggers this handler
        uow (AbstractUnitOfWork): Unit of Work used for the persistance layer
    """
    del uow
    email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )
