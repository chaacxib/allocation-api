from functools import lru_cache
from typing import List, Optional

import pydantic


class _ProjectSettings(pydantic.BaseModel):
    title: str = "Allocation API"
    version: str = "0.1.0"
    description: str = "Example application code based on the cosmic python book"

    redoc_url: Optional[str] = None
    docs_url: Optional[str] = None
    openapi_url: Optional[str] = None


class _CorsSettings(pydantic.BaseModel):
    allow_credentials: bool = True
    allow_origins: List[str] = ["*"]
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


class _LoggingSettings(pydantic.BaseModel):
    timestamp_use_utc: bool = False
    timestamp_format: str = "%Y-%m-%d %H:%M.%S"
    key_render_order: list[str] = [
        "timestamp",
        "level",
        "event",
    ]


class _DatabaseSettings(pydantic.BaseModel):
    host: str = "localhost"
    port: int = 54321
    user: str = "allocation"
    password: str = "abc123"
    database: str = "allocation"

    @property
    def mysql_uri(self) -> str:
        return (
            "mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
        ).format(**self.dict())


class _Settings(pydantic.BaseSettings):
    project: _ProjectSettings = _ProjectSettings()
    cors: _CorsSettings = _CorsSettings()
    logging: _LoggingSettings = _LoggingSettings()
    database: _DatabaseSettings = _DatabaseSettings()

    is_local_environment: Optional[bool] = False

    class Config(pydantic.BaseSettings.Config):
        env_prefix = "app_"
        env_nested_delimiter = "__"

    def configure_environment(self) -> None:
        if self.is_local_environment:
            self.project.docs_url = "/docs"
            self.project.redoc_url = "/redoc"
            self.project.openapi_url = "/openapi.json"


@lru_cache()
def get_settings() -> _Settings:
    """Takes advange of lru_cache decorator only instantiating the settings parameter
    once and storing the result on cache for faster use and response

    Returns:
        Settings: The instantiated Settings object
    """
    _settings = _Settings()
    _settings.configure_environment()
    return _settings
