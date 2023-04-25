from typing import Annotated

from fastapi import Depends

from src.allocation.adapters import unit_of_work
from src.allocation.lib import config

DefaultUnitOfWork = Annotated[
    unit_of_work.AbstractUnitOfWork, Depends(config.get_default_uow)
]
