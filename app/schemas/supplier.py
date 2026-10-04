from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SupplierBase(BaseModel):
    name: str
    platform: str | None = None
    blind_shipping_confirmed: bool = False
    contact_method: str | None = None
    api_available: bool = False


class SupplierCreate(SupplierBase):
    # Who is approving this supplier right now (manual vetting step, per the Risk Rules Specification)
    approved_by: str


class SupplierResponse(SupplierBase):
    id: UUID
    approved_at: datetime | None
    approved_by: str | None
    status: str

    class Config:
        from_attributes = True  # allows returning a SQLAlchemy model instance directly
