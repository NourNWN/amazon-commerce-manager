from uuid import UUID

from pydantic import BaseModel


class ShippingRouteBase(BaseModel):
    supplier_id: UUID
    destination_country: str
    avg_days: int | None = None
    max_days: int | None = None
    is_approved: bool = False


class ShippingRouteCreate(ShippingRouteBase):
    pass


class ShippingRouteResponse(ShippingRouteBase):
    id: UUID

    class Config:
        from_attributes = True
