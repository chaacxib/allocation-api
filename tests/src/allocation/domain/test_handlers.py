import pytest


class TestAddBatch:
    @pytest.mark.asyncio
    async def test_should_create_product_when_batch_is_created(self) -> None:
        from src.allocation.domain.model import events
        from src.allocation.domain.service import messagebus as subject
        from src.allocation.domain.service import unit_of_work

        uow = unit_of_work.FakeUnitOfWork()

        await subject.handle(
            uow=uow,
            event=events.BatchCreated(
                ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None
            ),
        )
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    @pytest.mark.asyncio
    async def test_should_append_batch_when_product_already_exists(self) -> None:
        from src.allocation.domain.model import events
        from src.allocation.domain.service import messagebus as subject
        from src.allocation.domain.service import unit_of_work

        uow = unit_of_work.FakeUnitOfWork()

        await subject.handle(
            uow=uow,
            event=events.BatchCreated(ref="b1", sku="GARISH-RUG", qty=100, eta=None),
        )
        await subject.handle(
            uow=uow,
            event=events.BatchCreated(ref="b2", sku="GARISH-RUG", qty=99, eta=None),
        )
        _product = uow.products.get("GARISH-RUG")
        assert _product is not None
        assert "b2" in [b.id for b in _product.batches]


class TestAllocate:
    @pytest.mark.asyncio
    async def test_should_return_allocation_batch_when_order_is_allocated(
        self,
    ) -> None:
        from src.allocation.domain.model import events
        from src.allocation.domain.service import messagebus as subject
        from src.allocation.domain.service import unit_of_work

        uow = unit_of_work.FakeUnitOfWork()

        await subject.handle(
            uow=uow,
            event=events.BatchCreated(
                ref="batch1", sku="COMPLICATED-LAMP", qty=100, eta=None
            ),
        )

        results = await subject.handle(
            uow=uow,
            event=events.AllocationRequired(
                sku="COMPLICATED-LAMP", order_id="o1", qty=10
            ),
        )
        assert results.pop(0) == "batch1"

    @pytest.mark.asyncio
    async def test_should_raise_invalid_sku_when_product_doesnt_exist(self) -> None:
        from src.allocation.domain.model import events
        from src.allocation.domain.service import handlers
        from src.allocation.domain.service import messagebus as subject
        from src.allocation.domain.service import unit_of_work

        uow = unit_of_work.FakeUnitOfWork()
        await subject.handle(
            uow=uow,
            event=events.BatchCreated(ref="b1", sku="AREALSKU", qty=100, eta=None),
        )

        with pytest.raises(
            handlers.InvalidSkuException, match="Invalid sku NONEXISTENTSKU"
        ):
            await subject.handle(
                uow=uow,
                event=events.AllocationRequired(
                    sku="NONEXISTENTSKU", order_id="o1", qty=10
                ),
            )

    @pytest.mark.asyncio
    async def test_uow_should_commit_to_persistent_layer_when_order_allocated(
        self,
    ) -> None:
        from src.allocation.domain.model import events
        from src.allocation.domain.service import messagebus as subject
        from src.allocation.domain.service import unit_of_work

        uow = unit_of_work.FakeUnitOfWork()

        await subject.handle(
            uow=uow,
            event=events.BatchCreated(
                ref="b1", sku="OMINOUS-MIRROR", qty=100, eta=None
            ),
        )
        await subject.handle(
            uow=uow,
            event=events.AllocationRequired(
                sku="OMINOUS-MIRROR", order_id="o1", qty=10
            ),
        )

        assert uow.committed


class TestChangeBatchQuantity:
    @pytest.mark.asyncio
    async def test_should_change_available_quantity_when_batch_quantity_updated(
        self,
    ) -> None:
        from src.allocation.domain.model import events
        from src.allocation.domain.service import messagebus as subject
        from src.allocation.domain.service import unit_of_work

        uow = unit_of_work.FakeUnitOfWork()

        await subject.handle(
            uow=uow,
            event=events.BatchCreated(
                ref="batch1", sku="ADORABLE-SETTEE", qty=100, eta=None
            ),
        )
        _product = uow.products.get(sku="ADORABLE-SETTEE")
        assert _product
        batch = _product.batches[0]
        assert batch.available_quantity == 100

        await subject.handle(
            uow=uow,
            event=events.BatchQuantityChanged(ref="batch1", qty=50),
        )
        assert batch.available_quantity == 50

    @pytest.mark.asyncio
    async def test_should_reallocate_order_when_not_enough_stock_in_batch(
        self,
    ) -> None:
        import datetime

        from src.allocation.domain.model import events
        from src.allocation.domain.service import messagebus as subject
        from src.allocation.domain.service import unit_of_work

        _process_sku = "INDIFFERENT-TABLE"
        uow = unit_of_work.FakeUnitOfWork()
        event_history = [
            events.BatchCreated(ref="batch1", sku=_process_sku, qty=50, eta=None),
            events.BatchCreated(
                ref="batch2", sku=_process_sku, qty=50, eta=datetime.date.today()
            ),
            events.AllocationRequired(sku=_process_sku, order_id="order1", qty=20),
            events.AllocationRequired(sku=_process_sku, order_id="order2", qty=20),
        ]

        for e in event_history:
            await subject.handle(event=e, uow=uow)

        await subject.handle(
            uow=uow, event=events.BatchQuantityChanged(ref="batch1", qty=25)
        )

        _published_event = uow.get_published_event_by_type(events.AllocationRequired)
        assert isinstance(_published_event, events.AllocationRequired)
        assert _published_event.order_id in {"order1", "order2"}
        assert _published_event.sku == _process_sku
