from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from src.allocation.domain import model, service
from src.allocation.lib import config
from src.allocation.repositories import sqlalchemy_repository as repository

router = APIRouter(prefix="/api", tags=["Allocation"])


@router.post(
    path="/allocate/",
    status_code=status.HTTP_201_CREATED,
)
async def allocate(payload: model.OrderLine) -> Dict[str, Any]:
    session = config.get_session()
    repo: repository.AbstractRepository = repository.SqlAlchemyRepository(session)

    try:
        batch_ref = service.allocate(line=payload, repo=repo, session=session)
    except (model.OutOfStockException, service.InvalidSkuException) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {"batch_ref": batch_ref}
