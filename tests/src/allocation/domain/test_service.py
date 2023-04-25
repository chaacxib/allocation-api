import pytest


@pytest.mark.asyncio
async def test_add_batch() -> None:
    from src.allocation.adapters import unit_of_work
    from src.allocation.domain import service
    from src.allocation.domain.model import dto

    uow = unit_of_work.FakeUnitOfWork()

    await service.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None),
    )
    assert uow.batches.get("b1") is not None
    assert uow.committed


@pytest.mark.asyncio
async def test_allocate_returns_allocation() -> None:
    from src.allocation.adapters import unit_of_work
    from src.allocation.domain import service
    from src.allocation.domain.model import dto

    uow = unit_of_work.FakeUnitOfWork()
    await service.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="batch1", sku="COMPLICATED-LAMP", qty=100, eta=None),
    )

    result = await service.allocate(
        uow=uow,
        dto=dto.OrderLineInput(sku="COMPLICATED-LAMP", order_id="o1", qty=10),
    )
    assert result == "batch1"


@pytest.mark.asyncio
async def test_allocate_errors_for_invalid_sku() -> None:
    from src.allocation.adapters import unit_of_work
    from src.allocation.domain import service
    from src.allocation.domain.model import dto

    uow = unit_of_work.FakeUnitOfWork()
    await service.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="b1", sku="AREALSKU", qty=100, eta=None),
    )

    with pytest.raises(
        service.InvalidSkuException, match="Invalid sku NONEXISTENTSKU"
    ):
        await service.allocate(
            uow=uow,
            dto=dto.OrderLineInput(sku="NONEXISTENTSKU", order_id="o1", qty=10),
        )


@pytest.mark.asyncio
async def test_commits() -> None:
    from src.allocation.adapters import unit_of_work
    from src.allocation.domain import service
    from src.allocation.domain.model import dto

    uow = unit_of_work.FakeUnitOfWork()

    await service.add_batch(
        uow=uow,
        dto=dto.BatchInput(ref="b1", sku="OMINOUS-MIRROR", qty=100, eta=None),
    )
    await service.allocate(
        uow=uow,
        dto=dto.OrderLineInput(sku="OMINOUS-MIRROR", order_id="o1", qty=10),
    )

    assert uow.committed
