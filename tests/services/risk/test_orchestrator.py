from dataclasses import replace
from datetime import datetime, timezone, timedelta

from app.services.risk.orchestrator import OrderRiskContext, run_all_checks


def build_healthy_context() -> OrderRiskContext:
    """A context where every single check should pass, used as a baseline for other tests."""
    return OrderRiskContext(
        payment_status="complete",
        payment_pending_since=None,
        shipping_address="Berlin, Germany",
        billing_address="Berlin, Germany",
        destination_country_code="DE",
        order_value=39.99,
        category_avg_value=35,
        is_first_order_from_customer=False,
        duplicate_payment_pattern_detected=False,
        quantity_available=12,
        stock_confirmed_at=datetime.now(timezone.utc) - timedelta(minutes=4),
        supplier_responded=True,
        route_approved=True,
        sale_price=39.99,
        supplier_price=9,
        amazon_fees=6,
        shipping_cost=5,
        refund_reserve=2,
        margin_at_listing_pct=21.0,
        total_capital=100,
        active_exposure=20,
        emergency_reserve=40,
        order_cost=14,
        compliance_flag="clear",
    )


class TestRunAllChecks:
    def test_authorized_when_everything_passes(self):
        result = run_all_checks(build_healthy_context())
        assert result.decision == "authorized"
        assert result.failed_check is None
        assert len(result.checks) == 7  # all seven checks ran

    def test_stops_at_payment_and_skips_remaining_checks(self):
        ctx = replace(build_healthy_context(), payment_status="flagged")
        result = run_all_checks(ctx)
        assert result.decision == "stopped"
        assert result.failed_check == "payment"
        assert len(result.checks) == 1  # stopped immediately, nothing else ran

    def test_stops_at_stock_after_payment_and_fraud_pass(self):
        ctx = replace(build_healthy_context(), quantity_available=0)
        result = run_all_checks(ctx)
        assert result.decision == "stopped"
        assert result.failed_check == "stock"
        assert len(result.checks) == 3  # payment, fraud, stock

    def test_stops_at_destination(self):
        ctx = replace(build_healthy_context(), route_approved=False)
        result = run_all_checks(ctx)
        assert result.decision == "stopped"
        assert result.failed_check == "destination"

    def test_stops_at_margin(self):
        ctx = replace(build_healthy_context(), sale_price=20, supplier_price=15, margin_at_listing_pct=None)
        result = run_all_checks(ctx)
        assert result.decision == "stopped"
        assert result.failed_check == "margin"

    def test_stops_at_wallet(self):
        ctx = replace(build_healthy_context(), active_exposure=95)
        result = run_all_checks(ctx)
        assert result.decision == "stopped"
        assert result.failed_check == "wallet"

    def test_stops_at_compliance(self):
        ctx = replace(build_healthy_context(), compliance_flag="restricted")
        result = run_all_checks(ctx)
        assert result.decision == "stopped"
        assert result.failed_check == "compliance"

    def test_pending_review_on_moderate_fraud_score(self):
        # address mismatch (25) + high risk country (20) = 45 -> within the 40-70 review band
        ctx = replace(
            build_healthy_context(),
            shipping_address="Lagos, Nigeria",
            billing_address="Dubai, UAE",
            destination_country_code="NG",
            route_approved=True,  # irrelevant here since fraud check runs before destination
        )
        result = run_all_checks(ctx)
        assert result.decision == "pending_review"
        assert result.failed_check == "fraud"

    def test_stopped_outright_on_severe_fraud_score(self):
        # address mismatch (25) + high risk country (20) + duplicate pattern (30) = 75 -> hard stop
        ctx = replace(
            build_healthy_context(),
            shipping_address="Lagos, Nigeria",
            billing_address="Dubai, UAE",
            destination_country_code="NG",
            duplicate_payment_pattern_detected=True,
        )
        result = run_all_checks(ctx)
        assert result.decision == "stopped"
        assert result.failed_check == "fraud"
