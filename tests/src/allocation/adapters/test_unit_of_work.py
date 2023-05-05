from typing import Optional

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from src.allocation.domain.model import aggregate
from src.allocation.domain.service import unit_of_work


def insert_batch(
    session: Session,
    ref: str,
    sku: str,
    qty: int,
    eta: Optional[str],
    product_version: int = 1,
) -> None:
    session.execute(
        statement=text(
            "INSERT INTO products (sku, version_number) VALUES (:sku, :version)",
        ),
        params=dict(sku=sku, version=product_version),
    )
    session.execute(
        statement=text(
            "INSERT INTO batches (id, sku, purchased_quantity, eta)"
            " VALUES (:ref, :sku, :qty, :eta)",
        ),
        params=dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def get_allocated_batch_ref(session: Session, order_id: str, sku: str) -> str:
    [[order_line_id]] = session.execute(
        statement=text(
            "SELECT id FROM order_lines WHERE order_id=:order_id AND sku=:sku",
        ),
        params=dict(order_id=order_id, sku=sku),
    )
    [[batch_ref]] = session.execute(
        statement=text(
            "SELECT b.id FROM allocations JOIN batches"
            " AS b ON batch_id = b.id"
            " WHERE orderline_id=:order_line_id",
        ),
        params=dict(order_line_id=order_line_id),
    )
    return batch_ref


@pytest.mark.asyncio
async def test_uow_can_retrieve_a_batch_and_allocate_to_it(
    session_factory: unit_of_work.SessionFactory,
) -> None:
    session = session_factory()
    insert_batch(
        session=session, ref="batch1", sku="HIPSTER-WORKBENCH", qty=100, eta=None
    )
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory=session_factory)
    async with uow:
        product = uow.products.get(sku="HIPSTER-WORKBENCH")
        if not product:
            raise aggregate.OutOfStockException()
        product.allocate(
            line=aggregate.OrderLine(order_id="o1", sku="HIPSTER-WORKBENCH", qty=10)
        )
        await uow.commit()

    batch_ref = get_allocated_batch_ref(
        session=session, order_id="o1", sku="HIPSTER-WORKBENCH"
    )
    assert batch_ref == "batch1"


@pytest.mark.asyncio
async def test_rolls_back_uncommitted_work_by_default(
    session_factory: unit_of_work.SessionFactory,
) -> None:
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory=session_factory)
    async with uow:
        insert_batch(
            session=uow.session, ref="batch1", sku="MEDIUM-PLINTH", qty=100, eta=None
        )

    new_session = session_factory()
    rows = list(new_session.execute(statement=text('SELECT * FROM "batches"')))
    assert rows == []


@pytest.mark.asyncio
async def test_rolls_back_on_error(
    session_factory: unit_of_work.SessionFactory,
) -> None:
    class TestException(Exception):
        ...

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory=session_factory)
    with pytest.raises(TestException):
        async with uow:
            insert_batch(
                session=uow.session,
                ref="batch1",
                sku="LARGE-FORK",
                qty=100,
                eta=None,
            )
            raise TestException()

    new_session = session_factory()
    rows = list(new_session.execute(statement=text('SELECT * FROM "batches"')))
    assert rows == []
