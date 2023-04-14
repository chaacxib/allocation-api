from typing import Annotated, Any

from fastapi import Depends

from src.allocation.lib.config import get_session

GetDBSession = Annotated[Any, Depends(get_session)]
