from datetime import date
from typing import Optional

import pydantic


class OrderLineInput(pydantic.BaseModel):
    sku: str = pydantic.Field(
        ..., title="Stock-Keeping Unit", description="Unique product identifier"
    )
    order_id: str = pydantic.Field(
        ..., title="Id", description="Unique order identifier"
    )
    qty: int = pydantic.Field(
        ...,
        title="Quantity",
        description="Number of product units for the order",
        gt=0,
    )


class OrderLineOutput(pydantic.BaseModel):
    batch_ref: str = pydantic.Field(
        ...,
        title="Batch reference",
        description="Unique identifier for the batch where the order was allocated",
    )


class BatchInput(pydantic.BaseModel):
    reference: str = pydantic.Field(
        ...,
        title="Reference",
        description="Unique identifier for the batch order",
        alias="ref",
    )
    sku: str = pydantic.Field(
        ..., title="Stock-Keeping Unit", description="Unique product identifier"
    )
    purchased_quantity: int = pydantic.Field(
        ...,
        title="Quantity",
        description="Number of product units for the batch order",
        gt=0,
        alias="qty",
    )
    eta: Optional[date] = pydantic.Field(
        None,
        title="Estimated Time of Arrival",
        description="Date when the Batch should arrive to the Warehouse",
    )
