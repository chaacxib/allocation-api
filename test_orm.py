# pyright: reportPrivateUsage=false
from datetime import date
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.sql import text

import model


def test_orderline_mapper_can_load_lines(session: Session) -> None:
    session.execute(
        statement=text(
            "INSERT INTO order_lines (order_id, sku, qty) VALUES "
            '("order1", "RED-CHAIR", 12),'
            '("order1", "RED-TABLE", 13),'
            '("order2", "BLUE-LIPSTICK", 14)'
        )
    )
    expected: List[model.OrderLine] = [
        model.OrderLine(order_id="order1", sku="RED-CHAIR", qty=12),
        model.OrderLine(order_id="order1", sku="RED-TABLE", qty=13),
        model.OrderLine(order_id="order2", sku="BLUE-LIPSTICK", qty=14),
    ]
    assert session.query(model.OrderLine).all() == expected


def test_orderline_mapper_can_save_lines(session: Session) -> None:
    new_line = model.OrderLine(order_id="order1", sku="DECORATIVE-WIDGET", qty=12)
    session.add(new_line)
    session.commit()

    rows = list(
        session.execute(
            statement=text('SELECT order_id, sku, qty FROM "order_lines"')
        )
    )
    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]


def test_retrieving_batches(session: Session) -> None:
    session.execute(
        statement=text(
            "INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES "
            '("batch1", "sku1", 100, null)'
        )
    )
    session.execute(
        statement=text(
            "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
            ' VALUES ("batch2", "sku2", 200, "2011-04-11")'
        )
    )
    expected = [
        model.Batch(ref="batch1", sku="sku1", qty=100, eta=None),
        model.Batch(ref="batch2", sku="sku2", qty=200, eta=date(2011, 4, 11)),
    ]

    assert session.query(model.Batch).all() == expected


def test_saving_batches(session: Session) -> None:
    batch = model.Batch(ref="batch1", sku="sku1", qty=100, eta=None)
    session.add(batch)
    session.commit()

    rows = session.execute(
        statement=text(
            'SELECT reference, sku, _purchased_quantity, eta FROM "batches"'
        )
    )
    assert list(rows) == [("batch1", "sku1", 100, None)]


def test_saving_allocations(session: Session) -> None:
    batch = model.Batch(ref="batch1", sku="sku1", qty=100, eta=None)
    line = model.OrderLine(order_id="order1", sku="sku1", qty=10)
    batch.allocate(line)
    session.add(batch)
    session.commit()
    rows = list(
        session.execute(
            statement=text('SELECT orderline_id, batch_id FROM "allocations"')
        )
    )
    assert rows == [(getattr(batch, "id"), getattr(batch, "id"))]


def test_retrieving_allocations(session: Session) -> None:
    session.execute(
        statement=text(
            "INSERT INTO order_lines (order_id, sku, qty)"
            'VALUES ("order1", "sku1", 12)'
        )
    )
    [[olid]] = session.execute(
        statement=text(
            "SELECT id FROM order_lines WHERE order_id=:order_id AND sku=:sku"
        ),
        params=dict(order_id="order1", sku="sku1"),
    )
    session.execute(
        statement=text(
            "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
            ' VALUES ("batch1", "sku1", 100, null)'
        )
    )
    [[bid]] = session.execute(
        statement=text("SELECT id FROM batches WHERE reference=:ref AND sku=:sku"),
        params=dict(ref="batch1", sku="sku1"),
    )
    session.execute(
        statement=text(
            "INSERT INTO allocations (orderline_id, batch_id) VALUES (:olid, :bid)"
        ),
        params=dict(olid=olid, bid=bid),
    )

    batch = session.query(model.Batch).one()

    assert batch._allocations == {
        model.OrderLine(order_id="order1", sku="sku1", qty=12)
    }
