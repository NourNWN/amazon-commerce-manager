from dataclasses import dataclass
from datetime import datetime

from app.services.risk.types import RiskCheckResult
from app.services.risk.checks import (
    check_payment,
    check_fraud,
    check_stock,
    check_destination,
    check_margin,
    check_wallet,
    check_compliance,
)

# Fraud score threshold above which the order is stopped outright rather than
# sent to manual review (per the final decision matrix in the Risk Rules Specification)
FRAUD_HARD_STOP_THRESHOLD = 70


@dataclass
class OrderRiskContext:
    """All inputs required to run the full risk check sequence for one order."""
    # payment
    payment_status: str
    payment_pending_since: datetime | None
    # fraud
    shipping_address: str
    billing_address: str
    destination_country_code: str
    order_value: float
    category_avg_value: float
    is_first_order_from_customer: bool
    duplicate_payment_pattern_detected: bool
    # stock
    quantity_available: int
    stock_confirmed_at: datetime | None
    supplier_responded: bool
    # destination
    route_approved: bool
    # margin
    sale_price: float
    supplier_price: float
    amazon_fees: float
    shipping_cost: float
    refund_reserve: float
    margin_at_listing_pct: float | None
    # wallet
    total_capital: float
    active_exposure: float
    emergency_reserve: float
    order_cost: float
    # compliance
    compliance_flag: str


@dataclass
class RiskEngineResult:
    decision: str  # "authorized" | "stopped" | "pending_review"
    checks: list[RiskCheckResult]
    failed_check: str | None = None


def run_all_checks(ctx: OrderRiskContext) -> RiskEngineResult:
    """
    Runs the seven risk checks in sequence and stops at the first failure,
    following the final decision matrix from the Risk Rules Specification:

    - All seven pass                         -> "authorized"
    - Any check fails (except fraud 40-70)    -> "stopped"
    - Fraud score in the 40-70 band only      -> "pending_review"
    """
    results: list[RiskCheckResult] = []

    payment_result = check_payment(ctx.payment_status, ctx.payment_pending_since)
    results.append(payment_result)
    if not payment_result.passed:
        return RiskEngineResult(decision="stopped", checks=results, failed_check="payment")

    fraud_result = check_fraud(
        ctx.shipping_address,
        ctx.billing_address,
        ctx.destination_country_code,
        ctx.order_value,
        ctx.category_avg_value,
        ctx.is_first_order_from_customer,
        ctx.duplicate_payment_pattern_detected,
    )
    results.append(fraud_result)
    if not fraud_result.passed:
        score = float(fraud_result.value) if fraud_result.value is not None else 0.0
        decision = "stopped" if score >= FRAUD_HARD_STOP_THRESHOLD else "pending_review"
        return RiskEngineResult(decision=decision, checks=results, failed_check="fraud")

    stock_result = check_stock(ctx.quantity_available, ctx.stock_confirmed_at, ctx.supplier_responded)
    results.append(stock_result)
    if not stock_result.passed:
        return RiskEngineResult(decision="stopped", checks=results, failed_check="stock")

    destination_result = check_destination(ctx.route_approved, ctx.destination_country_code)
    results.append(destination_result)
    if not destination_result.passed:
        return RiskEngineResult(decision="stopped", checks=results, failed_check="destination")

    margin_result = check_margin(
        ctx.sale_price,
        ctx.supplier_price,
        ctx.amazon_fees,
        ctx.shipping_cost,
        ctx.refund_reserve,
        ctx.margin_at_listing_pct,
    )
    results.append(margin_result)
    if not margin_result.passed:
        return RiskEngineResult(decision="stopped", checks=results, failed_check="margin")

    wallet_result = check_wallet(ctx.total_capital, ctx.active_exposure, ctx.emergency_reserve, ctx.order_cost)
    results.append(wallet_result)
    if not wallet_result.passed:
        return RiskEngineResult(decision="stopped", checks=results, failed_check="wallet")

    compliance_result = check_compliance(ctx.compliance_flag)
    results.append(compliance_result)
    if not compliance_result.passed:
        return RiskEngineResult(decision="stopped", checks=results, failed_check="compliance")

    return RiskEngineResult(decision="authorized", checks=results)
