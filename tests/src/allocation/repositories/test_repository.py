# pyright: reportPrivateUsage=false
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from src.allocation.domain import model
from src.allocation.repositories import sqlalchemy_repository as repository


def insert_order_line(session: Session) -> int:
    session.execute(
        statement=text(
            "INSERT INTO order_lines (order_id, sku, qty)"
            ' VALUES ("order1", "GENERIC-SOFA", 12)'
        )
    )
    [[orderline_id]] = session.execute(
        statement=text(
            "SELECT id FROM order_lines WHERE order_id=:order_id AND sku=:sku"
        ),
        params=dict(order_id="order1", sku="GENERIC-SOFA"),
    )
    return orderline_id


def insert_batch(session: Session, batch_id: str) -> str:
    session.execute(
        statement=text(
            "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
            ' VALUES (:batch_id, "GENERIC-SOFA", 100, null)'
        ),
        params=dict(batch_id=batch_id),
    )
    [[batch_id]] = session.execute(
        statement=text(
            'SELECT id FROM batches WHERE reference=:batch_id AND sku="GENERIC-SOFA"'
        ),
        params=dict(batch_id=batch_id),
    )
    return batch_id


def insert_allocation(session: Session, orderline_id: int, batch_id: str) -> None:
    session.execute(
        statement=text(
            "INSERT INTO allocations (orderline_id, batch_id)"
            " VALUES (:orderline_id, :batch_id)"
        ),
        params=dict(orderline_id=orderline_id, batch_id=batch_id),
    )


def test_repository_can_save_a_batch(session: Session) -> None:
    batch = model.Batch(ref="batch1", sku="RUSTY-SOAPDISH", qty=100, eta=None)

    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute(
        statement=text(
            'SELECT reference, sku, _purchased_quantity, eta FROM "batches"'
        )
    )
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, None)]


def test_repository_can_retrieve_a_batch_with_allocations(session: Session) -> None:
    orderline_id = insert_order_line(session=session)
    batch1_id = insert_batch(session=session, batch_id="batch1")
    insert_batch(session=session, batch_id="batch2")
    insert_allocation(session=session, orderline_id=orderline_id, batch_id=batch1_id)

    repo = repository.SqlAlchemyRepository(session)
    retrieved = repo.get(reference="batch1")

    expected = model.Batch(ref="batch1", sku="GENERIC-SOFA", qty=100, eta=None)
    assert retrieved == expected  # Batch.__eq__ only compares reference
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {
        model.OrderLine(order_id="order1", sku="GENERIC-SOFA", qty=12),
    }
