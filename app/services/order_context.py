from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.product import Product
from app.models.shipping_route import ShippingRoute
from app.models.wallet_transaction import WalletTransaction
from app.schemas.order_intake import OrderIntake
from app.services.risk.orchestrator import OrderRiskContext

# --- Temporary assumptions -------------------------------------------------
# These values are not stored anywhere in the database yet. They should move
# to a settings table (editable without code changes) in a later step.
AMAZON_FEE_RATE = 0.15        # approximate Amazon referral fee, as a share of sale price
REFUND_RESERVE_RATE = 0.05    # safety reserve for refunds, as a share of sale price
DEFAULT_SHIPPING_COST = 5.0   # flat supplier shipping cost per order
STARTING_CAPITAL = 100.0      # total capital available to the system
EMERGENCY_RESERVE = 40.0      # capital that must never be committed


class ListingNotFoundError(Exception):
    """Raised when no active listing matches the SKU of an incoming order."""


async def _get_active_exposure(db: AsyncSession) -> float:
    """Capital currently committed = sum of 'reserve' minus sum of 'release' transactions."""
    reserved = await db.scalar(
        select(func.coalesce(func.sum(WalletTransaction.amount), 0)).where(WalletTransaction.type == "reserve")
    )
    released = await db.scalar(
        select(func.coalesce(func.sum(WalletTransaction.amount), 0)).where(WalletTransaction.type == "release")
    )
    return float(reserved) - float(released)


async def build_risk_context(db: AsyncSession, intake: OrderIntake) -> tuple[OrderRiskContext, Listing]:
    """
    Gathers everything the risk engine needs for one incoming order.
    Returns the context together with the matched listing (needed later to save the order).
    """
    listing = await db.scalar(
        select(Listing).where(Listing.amazon_sku == intake.amazon_sku, Listing.is_active.is_(True))
    )
    if listing is None:
        raise ListingNotFoundError(f"No active listing found for SKU '{intake.amazon_sku}'")

    product = await db.get(Product, listing.product_id)

    destination = intake.destination_country.strip().upper()
    route = await db.scalar(
        select(ShippingRoute).where(
            ShippingRoute.supplier_id == product.supplier_id,
            ShippingRoute.destination_country == destination,
            ShippingRoute.is_approved.is_(True),
        )
    )

    supplier_price = float(product.supplier_price)
    active_exposure = await _get_active_exposure(db)

    ctx = OrderRiskContext(
        # payment
        payment_status=intake.payment_status,
        payment_pending_since=intake.payment_pending_since,
        # fraud
        shipping_address=intake.shipping_address,
        # if Amazon did not give us a billing address, do not penalize the order for it
        billing_address=intake.billing_address or intake.shipping_address,
        destination_country_code=destination,
        order_value=intake.sale_price,
        category_avg_value=float(listing.listed_price),  # proxy until real category averages exist
        is_first_order_from_customer=intake.is_first_order_from_customer,
        duplicate_payment_pattern_detected=False,  # no detection logic yet
        # stock
        quantity_available=product.stock_qty,
        stock_confirmed_at=product.last_stock_check,
        supplier_responded=product.last_stock_check is not None,
        # destination
        route_approved=route is not None,
        # margin
        sale_price=intake.sale_price,
        supplier_price=supplier_price,
        amazon_fees=intake.sale_price * AMAZON_FEE_RATE,
        shipping_cost=DEFAULT_SHIPPING_COST,
        refund_reserve=intake.sale_price * REFUND_RESERVE_RATE,
        margin_at_listing_pct=float(listing.margin_at_listing) if listing.margin_at_listing is not None else None,
        # wallet
        total_capital=STARTING_CAPITAL,
        active_exposure=active_exposure,
        emergency_reserve=EMERGENCY_RESERVE,
        order_cost=supplier_price + DEFAULT_SHIPPING_COST,
        # compliance
        compliance_flag=product.compliance_flag,
    )
    return ctx, listing