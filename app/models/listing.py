import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False
    )
    amazon_asin: Mapped[str | None] = mapped_column(String)
    amazon_sku: Mapped[str | None] = mapped_column(String)
    listed_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    margin_at_listing: Mapped[float | None] = mapped_column(Numeric(10, 2))

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
