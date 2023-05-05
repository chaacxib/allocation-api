import pytest


@pytest.mark.asyncio
async def test_add_batch_for_new_product() -> None:
    from src.allocation.domain.model import dto
    from src.allocation.domain.service import services, unit_of_work

    uow = unit_of_work.FakeUnitOfWork()

    await services.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None),
    )
    assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


@pytest.mark.asyncio
async def test_add_batch_for_existing_product() -> None:
    from src.allocation.domain.model import dto
    from src.allocation.domain.service import services, unit_of_work

    uow = unit_of_work.FakeUnitOfWork()

    await services.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="b1", sku="GARISH-RUG", qty=100, eta=None),
    )
    await services.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="b2", sku="GARISH-RUG", qty=99, eta=None),
    )
    _product = uow.products.get("GARISH-RUG")
    assert _product is not None
    assert "b2" in [b.id for b in _product.batches]


@pytest.mark.asyncio
async def test_allocate_returns_allocation() -> None:
    from src.allocation.domain.model import dto
    from src.allocation.domain.service import services, unit_of_work

    uow = unit_of_work.FakeUnitOfWork()
    await services.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="batch1", sku="COMPLICATED-LAMP", qty=100, eta=None),
    )

    result = await services.allocate(
        uow=uow,
        dto=dto.OrderLineInput(sku="COMPLICATED-LAMP", order_id="o1", qty=10),
    )
    assert result == "batch1"


@pytest.mark.asyncio
async def test_allocate_errors_for_invalid_sku() -> None:
    from src.allocation.domain.model import dto
    from src.allocation.domain.service import services, unit_of_work

    uow = unit_of_work.FakeUnitOfWork()
    await services.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="b1", sku="AREALSKU", qty=100, eta=None),
    )

    with pytest.raises(
        services.InvalidSkuException, match="Invalid sku NONEXISTENTSKU"
    ):
        await services.allocate(
            uow=uow,
            dto=dto.OrderLineInput(sku="NONEXISTENTSKU", order_id="o1", qty=10),
        )


@pytest.mark.asyncio
async def test_commits() -> None:
    from src.allocation.domain.model import dto
    from src.allocation.domain.service import services, unit_of_work

    uow = unit_of_work.FakeUnitOfWork()

    await services.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="b1", sku="OMINOUS-MIRROR", qty=100, eta=None),
    )
    await services.allocate(
        uow=uow,
        dto=dto.OrderLineInput(sku="OMINOUS-MIRROR", order_id="o1", qty=10),
    )

    assert uow.committed
