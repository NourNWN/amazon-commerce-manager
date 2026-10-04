"""
Response-only schemas for tables populated by internal business logic,
not by direct manual input: orders, risk_checks, wallet_transactions,
account_health_snapshots. No *Create schemas on purpose - see the
dedicated order-processing flow (to be built separately) for how these
rows actually get created.
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class OrderResponse(BaseModel):
    id: UUID
    amazon_order_id: str
    listing_id: UUID
    destination_country: str | None
    sale_price: float
    payment_status: str | None
    received_at: datetime | None
    final_decision: str | None
    supplier_purchase_id: str | None
    tracking_number: str | None
    delivery_status: str

    class Config:
        from_attributes = True


class RiskCheckResponse(BaseModel):
    id: UUID
    order_id: UUID
    check_name: str
    result: str
    value: float | None
    checked_at: datetime

    class Config:
        from_attributes = True


class WalletTransactionResponse(BaseModel):
    id: UUID
    order_id: UUID | None
    type: str
    amount: float
    balance_after: float
    created_at: datetime

    class Config:
        from_attributes = True


class AccountHealthSnapshotResponse(BaseModel):
    id: UUID
    snapshot_date: date
    late_shipment_rate: float | None
    order_defect_rate: float | None
    valid_tracking_rate: float | None
    status: str

    class Config:
        from_attributes = True
