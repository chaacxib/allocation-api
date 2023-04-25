from datetime import date, timedelta

import pytest

from src.allocation.domain.model import aggregate

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_prefers_warehouse_batches_to_shipments() -> None:
    in_stock_batch = aggregate.Batch(
        id="in-stock-batch",
        sku="RETRO-CLOCK",
        purchased_quantity=100,
        eta=None,
    )
    shipment_batch = aggregate.Batch(
        id="shipment-batch",
        sku="RETRO-CLOCK",
        purchased_quantity=100,
        eta=tomorrow,
    )
    line = aggregate.OrderLine(order_id="oref", sku="RETRO-CLOCK", qty=10)
    product = aggregate.Product(
        sku="RETRO-CLOCK", batches=[in_stock_batch, shipment_batch]
    )
    product.allocate(line)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches() -> None:
    earliest = aggregate.Batch(
        id="speedy-batch",
        sku="MINIMALIST-SPOON",
        purchased_quantity=100,
        eta=today,
    )
    medium = aggregate.Batch(
        id="normal-batch",
        sku="MINIMALIST-SPOON",
        purchased_quantity=100,
        eta=tomorrow,
    )
    latest = aggregate.Batch(
        id="slow-batch",
        sku="MINIMALIST-SPOON",
        purchased_quantity=100,
        eta=later,
    )
    product = aggregate.Product(
        sku="MINIMALIST-SPOON", batches=[medium, earliest, latest]
    )
    line = aggregate.OrderLine(order_id="order1", sku="MINIMALIST-SPOON", qty=10)

    product.allocate(line)

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref() -> None:
    in_stock_batch = aggregate.Batch(
        id="in-stock-batch-ref",
        sku="HIGHBROW-POSTER",
        purchased_quantity=100,
        eta=None,
    )
    shipment_batch = aggregate.Batch(
        id="shipment-batch-ref",
        sku="HIGHBROW-POSTER",
        purchased_quantity=100,
        eta=tomorrow,
    )
    line = aggregate.OrderLine(order_id="oref", sku="HIGHBROW-POSTER", qty=10)
    product = aggregate.Product(
        sku="HIGHBROW-POSTER", batches=[in_stock_batch, shipment_batch]
    )

    allocation = product.allocate(line)
    assert allocation == in_stock_batch.id


def test_raises_out_of_stock_exception_if_cannot_allocate() -> None:
    batch = aggregate.Batch(
        id="batch1", sku="SMALL-FORK", purchased_quantity=10, eta=today
    )
    product = aggregate.Product(sku="SMALL-FORK", batches=[batch])

    product.allocate(
        aggregate.OrderLine(order_id="order1", sku="SMALL-FORK", qty=10)
    )

    with pytest.raises(aggregate.OutOfStockException, match="SMALL-FORK"):
        product.allocate(
            aggregate.OrderLine(order_id="order2", sku="SMALL-FORK", qty=1)
        )


def test_increments_version_number() -> None:
    line = aggregate.OrderLine(order_id="oref", sku="SCANDI-PEN", qty=10)
    product = aggregate.Product(
        sku="SCANDI-PEN",
        batches=[
            aggregate.Batch(
                id="b1", sku="SCANDI-PEN", purchased_quantity=100, eta=None
            )
        ],
    )
    product.version_number = 7
    product.allocate(line)
    assert product.version_number == 8
