from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from src.allocation.domain import model
from src.allocation.repositories import AbstractRepository


class InvalidSkuException(Exception):
    """Raise when there's no batch with the provided sku"""

    ...


def is_valid_sku(sku: str, batches: List[model.Batch]) -> bool:
    """Validate if a received sku is present on the database

    Args:
        sku (str): Unique product identifier. ex. RED-CHAIR
        batches (List[model.Batch]): List of available stock batches

    Returns:
        bool: True if at leat one batch with the defined sku is found
    """
    return sku in {b.sku for b in batches}


def allocate(
    line: model.OrderLine, repo: AbstractRepository, session: Session
) -> str:
    """Service to allocate an order and persist the data

    Args:
        line (model.OrderLine): New order to allocate
        repo (AbstractRepository): Repository used for the persistance layer
        session (Session): Database session for this allocation process

    Raises:
        InvalidSkuException: Raise when there's no batch with the provided sku

    Returns:
        batch_ref (str): Reference of the batch where the order is allocated
    """
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSkuException(f"Invalid sku {line.sku}")
    batch_ref = model.allocate(line, batches)
    session.commit()
    return batch_ref