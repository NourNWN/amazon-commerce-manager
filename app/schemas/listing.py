from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ListingBase(BaseModel):
    product_id: UUID
    amazon_asin: str | None = None
    amazon_sku: str | None = None
    listed_price: float
    margin_at_listing: float | None = None
    is_active: bool = True


class ListingCreate(ListingBase):
    pass


class ListingResponse(ListingBase):
    id: UUID
    published_at: datetime | None

    class Config:
        from_attributes = True
