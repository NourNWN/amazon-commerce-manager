import uuid

from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ShippingRoute(Base):
    __tablename__ = "shipping_routes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False
    )
    destination_country: Mapped[str] = mapped_column(String, nullable=False)
    avg_days: Mapped[int | None] = mapped_column(Integer)
    max_days: Mapped[int | None] = mapped_column(Integer)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
