from fastapi import APIRouter, HTTPException, status

from src.allocation.domain.model import aggregate, dto, events
from src.allocation.domain.service import handlers, messagebus
from src.allocation.routers import commons

app_router = APIRouter(prefix="/batches", tags=["Batches"])


@app_router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
)
async def add_batch(
    payload: dto.BatchInput,
    uow: commons.DefaultUnitOfWork,
) -> None:
    await messagebus.handle(
        uow=uow,
        event=events.BatchCreated(
            ref=payload.reference,
            sku=payload.sku,
            qty=payload.purchased_quantity,
            eta=payload.eta,
        ),
    )


@app_router.post(
    path="/allocate/",
    status_code=status.HTTP_201_CREATED,
    response_model=dto.OrderLineOutput,
)
async def allocate(
    payload: dto.OrderLineInput,
    uow: commons.DefaultUnitOfWork,
) -> dto.OrderLineOutput:
    try:
        results = await messagebus.handle(
            event=events.AllocationRequired(**payload.dict()), uow=uow
        )
        batch_ref = results.pop(0)
    except (aggregate.OutOfStockException, handlers.InvalidSkuException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return dto.OrderLineOutput(batch_ref=batch_ref)
