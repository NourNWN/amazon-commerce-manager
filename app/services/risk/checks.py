from datetime import datetime, timezone

from app.services.risk.types import RiskCheckResult

############# 1 ##############
# Max hours a payment is allowed to stay "pending" before it's treated as failed
# (per Risk Rules Specification, item 1: 2 hours)
MAX_PENDING_HOURS = 2

def check_payment(payment_status: str, payment_pending_since: datetime | None = None) -> RiskCheckResult:
    """
    Risk Rules Specification, item 1: Payment verification.

    - Pass: payment status is "complete" or "authorized"
    - Fail: payment still "pending" beyond MAX_PENDING_HOURS, or any other status (e.g. "flagged")
    """
    if payment_status in ("complete", "authorized"):
        return RiskCheckResult(check_name="payment", passed=True)

    if payment_status == "pending" and payment_pending_since is not None:
        hours_pending = (datetime.now(timezone.utc) - payment_pending_since).total_seconds() / 3600
        if hours_pending <= MAX_PENDING_HOURS:
            # Still within the allowed window - not confirmed yet, so it doesn't pass
            return RiskCheckResult(
                check_name="payment",
                passed=False,
                reason=f"Payment pending for {hours_pending:.1f}h, still within allowed window - retry later",
            )

    return RiskCheckResult(
        check_name="payment",
        passed=False,
        reason=f"Payment status not acceptable to proceed: {payment_status}",
    )

############# 2 ##############
# Score threshold above which an order goes to manual review instead of auto-pass
FRAUD_REVIEW_THRESHOLD = 40

HIGH_RISK_COUNTRIES = {"NG", "GH", "PK"}  # initial list, should move to configurable settings later

def check_fraud(
    shipping_address: str,
    billing_address: str,
    destination_country_code: str,
    order_value: float,
    category_avg_value: float,
    is_first_order_from_customer: bool,
    duplicate_payment_pattern_detected: bool = False,
) -> RiskCheckResult:
    """
    Risk Rules Specification, item 2: Fraud score check.

    - Pass: total score < 40
    - Fail (manual review): total score >= 40
    """
    score = 0
    reasons = []

    if shipping_address.strip().lower() != billing_address.strip().lower():
        score += 25
        reasons.append("Shipping address differs from billing address")

    if destination_country_code in HIGH_RISK_COUNTRIES:
        score += 20
        reasons.append(f"Destination country ({destination_country_code}) flagged as high risk")

    if is_first_order_from_customer and category_avg_value > 0:
        if order_value > 3 * category_avg_value:
            score += 15
            reasons.append("First order value exceeds 3x category average")

    if duplicate_payment_pattern_detected:
        score += 30
        reasons.append("Suspicious repeated payment pattern for the same product")

    passed = score < FRAUD_REVIEW_THRESHOLD
    return RiskCheckResult(
        check_name="fraud",
        passed=passed,
        value=score,
        reason="; ".join(reasons) if reasons else None,
    )

############# 3 ##############
# Max age (minutes) of a stock confirmation for it to still be considered reliable
MAX_STOCK_CHECK_AGE_MINUTES = 15

def check_stock(
    quantity_available: int,
    stock_confirmed_at: datetime | None,
    supplier_responded: bool = True,
) -> RiskCheckResult:
    """
    Risk Rules Specification, item 3: Live stock check.

    - Pass: confirmation age <= 15 minutes AND quantity >= 1
    - Fail: no recent confirmation, quantity == 0, or supplier didn't respond in time
    """
    if not supplier_responded:
        return RiskCheckResult(
            check_name="stock",
            passed=False,
            reason="Supplier did not respond within the allowed timeout",
        )

    if stock_confirmed_at is None:
        return RiskCheckResult(
            check_name="stock",
            passed=False,
            reason="No stock confirmation available",
        )

    age_minutes = (datetime.now(timezone.utc) - stock_confirmed_at).total_seconds() / 60
    if age_minutes > MAX_STOCK_CHECK_AGE_MINUTES:
        return RiskCheckResult(
            check_name="stock",
            passed=False,
            value=quantity_available,
            reason=f"Stock confirmation is {age_minutes:.1f} min old, exceeds {MAX_STOCK_CHECK_AGE_MINUTES} min limit",
        )

    if quantity_available < 1:
        return RiskCheckResult(
            check_name="stock",
            passed=False,
            value=quantity_available,
            reason="Supplier reports zero quantity available",
        )

    return RiskCheckResult(check_name="stock", passed=True, value=quantity_available)

############# 4 ##############
def check_destination(route_approved: bool, destination_country_code: str) -> RiskCheckResult:
    """
    Risk Rules Specification, item 4: Destination / shipping match.

    - Pass: an approved (supplier x destination country) route exists in shipping_routes
    - Fail: no approved route for this combination, regardless of other destinations
      being approved for the same product via a different supplier
    """
    if route_approved:
        return RiskCheckResult(check_name="destination", passed=True)

    return RiskCheckResult(
        check_name="destination",
        passed=False,
        reason=f"No approved shipping route to {destination_country_code} for this supplier",
    )

############# 5 ##############
# Minimum acceptable profit margin, as a percentage of sale price, after all fees
MIN_MARGIN_PCT = 15.0

# Maximum allowed relative drop in margin compared to margin_at_listing,
# signals a sudden supplier price change between listing time and order time
MAX_MARGIN_DROP_PCT = 20.0

def check_margin(
    sale_price: float,
    supplier_price: float,
    amazon_fees: float,
    shipping_cost: float,
    refund_reserve: float,
    margin_at_listing_pct: float | None = None,
) -> RiskCheckResult:
    """
    Risk Rules Specification, item 5: Margin safety check.

    - Pass: actual margin >= MIN_MARGIN_PCT, AND the drop vs margin_at_listing_pct
      (if provided) does not exceed MAX_MARGIN_DROP_PCT (relative drop)
    - Fail: margin too low, or margin dropped too sharply since listing time
      (a signal that the supplier price changed unexpectedly)
    """
    total_cost = supplier_price + amazon_fees + shipping_cost + refund_reserve
    profit = sale_price - total_cost
    actual_margin_pct = (profit / sale_price) * 100 if sale_price > 0 else 0.0

    if actual_margin_pct < MIN_MARGIN_PCT:
        return RiskCheckResult(
            check_name="margin",
            passed=False,
            value=actual_margin_pct,
            reason=f"Actual margin {actual_margin_pct:.1f}% is below the minimum {MIN_MARGIN_PCT}%",
        )

    if margin_at_listing_pct is not None and margin_at_listing_pct > 0:
        relative_drop_pct = ((margin_at_listing_pct - actual_margin_pct) / margin_at_listing_pct) * 100
        if relative_drop_pct > MAX_MARGIN_DROP_PCT:
            return RiskCheckResult(
                check_name="margin",
                passed=False,
                value=actual_margin_pct,
                reason=(
                    f"Margin dropped {relative_drop_pct:.1f}% relative to listing time "
                    f"({margin_at_listing_pct:.1f}% -> {actual_margin_pct:.1f}%), exceeds {MAX_MARGIN_DROP_PCT}% limit"
                ),
            )

    return RiskCheckResult(check_name="margin", passed=True, value=actual_margin_pct)

############# 6 ##############
def check_wallet(
    total_capital: float,
    active_exposure: float,
    emergency_reserve: float,
    order_cost: float,
) -> RiskCheckResult:
    """
    Risk Rules Specification, item 6: Wallet / capital safety check.

    available = total_capital - active_exposure - emergency_reserve

    - Pass: order_cost <= available
    - Fail: executing this order would eat into the emergency reserve
    """
    available = total_capital - active_exposure - emergency_reserve

    if order_cost <= available:
        return RiskCheckResult(check_name="wallet", passed=True, value=available)

    return RiskCheckResult(
        check_name="wallet",
        passed=False,
        value=available,
        reason=(
            f"Order cost {order_cost:.2f} exceeds available capital {available:.2f} "
            f"(would breach the emergency reserve of {emergency_reserve:.2f})"
        ),
    )

############# 7 ##############
def check_compliance(compliance_flag: str) -> RiskCheckResult:
    """
    Risk Rules Specification, item 7: Compliance / IP check.

    - Pass: product.compliance_flag == "clear"
    - Fail: "restricted", "blocked", or any other non-clear flag
    """
    if compliance_flag == "clear":
        return RiskCheckResult(check_name="compliance", passed=True)

    return RiskCheckResult(
        check_name="compliance",
        passed=False,
        reason=f"Product compliance flag is '{compliance_flag}', not clear for sale",
    )