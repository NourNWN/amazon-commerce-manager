import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    amazon_order_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False
    )
    destination_country: Mapped[str | None] = mapped_column(String)
    sale_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_status: Mapped[str | None] = mapped_column(String)

    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    final_decision: Mapped[str | None] = mapped_column(String)  # authorized / stopped
    supplier_purchase_id: Mapped[str | None] = mapped_column(String)
    tracking_number: Mapped[str | None] = mapped_column(String)
    delivery_status: Mapped[str] = mapped_column(String, default="pending")
