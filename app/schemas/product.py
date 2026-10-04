from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProductBase(BaseModel):
    supplier_id: UUID
    supplier_sku: str | None = None
    title: str
    supplier_price: float
    stock_qty: int = 0
    compliance_flag: str = "clear"


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: UUID
    last_price_check: datetime | None
    last_stock_check: datetime | None
    status: str

    class Config:
        from_attributes = True
