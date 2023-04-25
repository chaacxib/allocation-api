from fastapi import APIRouter, HTTPException, status

from src.allocation.domain import model, service
from src.allocation.domain.model import dto
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
    await service.add_batch(uow=uow, dto=payload)


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
        batch_ref = await service.allocate(uow=uow, dto=payload)
    except (model.OutOfStockException, service.InvalidSkuException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return dto.OrderLineOutput(batch_ref=batch_ref)
