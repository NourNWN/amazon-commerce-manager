import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    platform: Mapped[str | None] = mapped_column(String)  # Alibaba / CJ Dropshipping / AliExpress / مباشر
    blind_shipping_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    contact_method: Mapped[str | None] = mapped_column(String)
    api_available: Mapped[bool] = mapped_column(Boolean, default=False)
    api_credentials: Mapped[dict | None] = mapped_column(JSON)  # يُشفَّر لاحقًا قبل الإنتاج

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="active")  # active / suspended