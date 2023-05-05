import pydantic


class Event(pydantic.BaseModel):
    ...


class OutOfStock(Event):
    sku: str
