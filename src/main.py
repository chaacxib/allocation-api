from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.allocation.lib import config, settings
from src.allocation.routers.entrypoints import router

_SETTINGS = settings.get_settings()


app = FastAPI(lifespan=config.lifespan, **_SETTINGS.project.dict())
app.add_middleware(middleware_class=CORSMiddleware, **_SETTINGS.cors.dict())
app.include_router(router)
