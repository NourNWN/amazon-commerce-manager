import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class RiskCheck(Base):
    __tablename__ = "risk_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    check_name: Mapped[str] = mapped_column(String, nullable=False)  # payment / fraud / stock / ...
    result: Mapped[str] = mapped_column(String, nullable=False)  # pass / fail
    value: Mapped[float | None] = mapped_column(Numeric(10, 2))

    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
