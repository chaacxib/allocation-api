import datetime
from typing import List, Set

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.allocation.domain.model import aggregate


class Base(DeclarativeBase):
    ...


allocations_table = Table(
    "allocations",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", Integer, ForeignKey("order_lines.id")),
    Column("batch_id", Integer, ForeignKey("batches.id")),
)


class ProductMapper(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(255), primary_key=True)
    version_number: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
        nullable=False,
    )

    batches: Mapped[List["BatchMapper"]] = relationship()

    @staticmethod
    def from_domain(
        product: aggregate.Product,
    ) -> "ProductMapper":
        return ProductMapper(
            **product.dict(exclude={"events", "batches"}),
            batches=list(map(BatchMapper.from_domain, product.batches)),
        )


class BatchMapper(Base):
    __tablename__ = "batches"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    sku: Mapped[str] = mapped_column(String(255), ForeignKey("products.sku"))
    purchased_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    eta: Mapped[datetime.date] = mapped_column(Date, nullable=True)

    _allocations: Mapped[Set["OrderLineMapper"]] = relationship(
        secondary=allocations_table
    )

    @staticmethod
    def from_domain(
        batch: aggregate.Batch,
    ) -> "BatchMapper":
        return BatchMapper(
            **batch.dict(),
            _allocations=set(map(OrderLineMapper.from_domain, batch.allocations)),
        )


class OrderLineMapper(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(255))
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    order_id: Mapped[str] = mapped_column(String(255))

    @staticmethod
    def from_domain(
        order_line: aggregate.OrderLine,
    ) -> "OrderLineMapper":
        return OrderLineMapper(
            **order_line.dict(),
            id=hash(order_line),
        )
