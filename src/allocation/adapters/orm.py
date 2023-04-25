from sqlalchemy import Column, Date, ForeignKey, Integer, MetaData, String, Table
from sqlalchemy.orm import registry, relationship

from src.allocation.domain.model import aggregate

metadata = MetaData()

products = Table(
    "products",
    metadata,
    Column("sku", String(255), primary_key=True),
    Column("version_number", Integer, server_default="0", nullable=False),
)

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("order_id", String(255)),
)

batches = Table(
    "batches",
    metadata,
    Column("id", String(255), primary_key=True),
    Column("sku", String(255), ForeignKey("products.sku")),
    Column("purchased_quantity", Integer, nullable=False),
    Column("eta", Date, nullable=True),
)

allocations = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", Integer, ForeignKey("order_lines.id")),
    Column("batch_id", Integer, ForeignKey("batches.id")),
)


def start_mappers() -> None:
    mapper_registry = registry()
    lines_mapper = mapper_registry.map_imperatively(
        class_=aggregate.OrderLine, local_table=order_lines
    )
    batches_mapper = mapper_registry.map_imperatively(
        class_=aggregate.Batch,
        local_table=batches,
        properties={
            "_allocations": relationship(
                lines_mapper,
                secondary=allocations,
                collection_class=set,
            )
        },
    )
    mapper_registry.map_imperatively(
        class_=aggregate.Product,
        local_table=products,
        properties={
            "batches": relationship(
                batches_mapper,
                lazy="dynamic",
            )
        },
    )
