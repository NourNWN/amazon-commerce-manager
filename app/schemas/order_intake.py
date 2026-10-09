from datetime import datetime

from pydantic import BaseModel

from app.schemas.readonly import OrderResponse


class OrderIntake(BaseModel):
    """
    Shape of an incoming customer order, as it will arrive from Amazon
    (via SP-API Orders later). For now it is submitted manually through /docs
    to test the full flow end to end.
    """
    amazon_order_id: str
    amazon_sku: str                 # used to find the matching listing in our database
    destination_country: str        # ISO country code, e.g. "DE"
    shipping_address: str
    billing_address: str | None = None   # Amazon may not expose this to sellers, so it is optional
    sale_price: float
    payment_status: str             # "complete" / "authorized" / "pending" / ...
    payment_pending_since: datetime | None = None
    is_first_order_from_customer: bool = False


class RiskCheckOutcome(BaseModel):
    check_name: str
    passed: bool
    value: float | None = None
    reason: str | None = None


class OrderIntakeResponse(BaseModel):
    order: OrderResponse
    decision: str                      # "authorized" / "stopped" / "pending_review"
    failed_check: str | None = None
    checks: list[RiskCheckOutcome]     # empty when the order was already processed earlier
    already_processed: bool