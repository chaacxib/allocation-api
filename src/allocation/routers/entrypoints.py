from fastapi import APIRouter, HTTPException, status

from src.allocation.domain import model, service
from src.allocation.domain.model import dto
from src.allocation.repositories import sqlalchemy_repository as repository
from src.allocation.routers import commons

app_router = APIRouter(prefix="/batches", tags=["Batches"])


@app_router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
)
async def add_batch(
    payload: dto.BatchInput,
    session: commons.GetDBSession,
) -> None:
    repo: repository.AbstractRepository = repository.SqlAlchemyRepository(session)
    service.add_batch(repo=repo, session=session, dto=payload)


@app_router.post(
    path="/allocate/",
    status_code=status.HTTP_201_CREATED,
    response_model=dto.OrderLineOutput,
)
async def allocate(
    payload: dto.OrderLineInput,
    session: commons.GetDBSession,
) -> dto.OrderLineOutput:
    repo: repository.AbstractRepository = repository.SqlAlchemyRepository(session)

    try:
        batch_ref = service.allocate(
            repo=repo,
            dto=payload,
            session=session,
        )
    except (model.OutOfStockException, service.InvalidSkuException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return dto.OrderLineOutput(batch_ref=batch_ref)
