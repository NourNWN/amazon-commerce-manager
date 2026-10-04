import uuid
from datetime import date as date_type

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AccountHealthSnapshot(Base):
    __tablename__ = "account_health_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    late_shipment_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    order_defect_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    valid_tracking_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(String, default="healthy")  # healthy / warning / critical
