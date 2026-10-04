import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False
    )
    supplier_sku: Mapped[str | None] = mapped_column(String)
    title: Mapped[str] = mapped_column(String, nullable=False)
    supplier_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    last_price_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_stock_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)

    compliance_flag: Mapped[str] = mapped_column(String, default="clear")  # clear / restricted / blocked
    status: Mapped[str] = mapped_column(String, default="candidate")  # candidate / ready / rejected / listed