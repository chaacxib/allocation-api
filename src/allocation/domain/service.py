from __future__ import annotations

from typing import List

from src.allocation.adapters import unit_of_work
from src.allocation.domain import model
from src.allocation.domain.model import dto


class InvalidSkuException(Exception):
    """Raise when there's no batch with the provided sku"""

    ...


def is_valid_sku(sku: str, batches: List[model.Batch]) -> bool:
    """Validate if a received sku is present on the database

    Args:
        sku (str): Unique product identifier. ex. RED-CHAIR
        batches (List[Batch]): List of available stock batches

    Returns:
        bool: True if at leat one batch with the defined sku is found
    """
    return sku in {b.sku for b in batches}


async def add_batch(
    dto: dto.BatchInput,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    """Service to save a new order batch

    Args:
        dto (BatchInput): New batch data to store
        uow (AbstractUnitOfWork): Unit of Work used for the persistance layer
    """
    async with uow:
        uow.batches.add(model.Batch(**dto.dict()))
        await uow.commit()


async def allocate(
    dto: dto.OrderLineInput,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    """Service to allocate an order and persist the data

    Args:
        dto (OrderLineInput): New order data to allocate
        uow (AbstractUnitOfWork): Unit of Work used for the persistance layer

    Raises:
        InvalidSkuException: Raise when there's no batch with the provided sku

    Returns:
        batch_ref (str): Reference of the batch where the order is allocated
    """
    async with uow:
        batches = uow.batches.list()
        if not is_valid_sku(dto.sku, batches):
            raise InvalidSkuException(f"Invalid sku {dto.sku}")
        batch_ref = model.allocate(
            line=model.OrderLine(**dto.dict()), batches=batches
        )
        await uow.commit()
    return batch_ref
