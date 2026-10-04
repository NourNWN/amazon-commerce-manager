from datetime import datetime, timezone, timedelta

from app.services.risk.checks import (
    check_payment,
    check_fraud,
    check_stock,
    check_destination,
    check_margin,
    check_wallet,
    check_compliance,
)


class TestCheckPayment:
    def test_passes_when_payment_complete(self):
        result = check_payment("complete")
        assert result.passed is True

    def test_passes_when_payment_authorized(self):
        result = check_payment("authorized")
        assert result.passed is True

    def test_fails_when_payment_pending_without_timestamp(self):
        result = check_payment("pending")
        assert result.passed is False

    def test_fails_when_pending_beyond_max_hours(self):
        pending_since = datetime.now(timezone.utc) - timedelta(hours=3)
        result = check_payment("pending", pending_since)
        assert result.passed is False
        assert "pending" in result.reason.lower()

    def test_fails_when_pending_within_max_hours_window(self):
        # Still not confirmed, so it should not pass even though it's within the retry window
        pending_since = datetime.now(timezone.utc) - timedelta(minutes=30)
        result = check_payment("pending", pending_since)
        assert result.passed is False

    def test_fails_on_unexpected_status(self):
        result = check_payment("flagged")
        assert result.passed is False


class TestCheckFraud:
    def test_passes_on_clean_order(self):
        result = check_fraud(
            shipping_address="Cairo, Egypt",
            billing_address="Cairo, Egypt",
            destination_country_code="EG",
            order_value=50,
            category_avg_value=40,
            is_first_order_from_customer=False,
        )
        assert result.passed is True
        assert result.value == 0

    def test_address_mismatch_adds_score(self):
        result = check_fraud(
            shipping_address="Cairo, Egypt",
            billing_address="Dubai, UAE",
            destination_country_code="EG",
            order_value=50,
            category_avg_value=40,
            is_first_order_from_customer=False,
        )
        assert result.value == 25
        assert result.passed is True  # below threshold on its own

    def test_high_risk_country_adds_score(self):
        result = check_fraud(
            shipping_address="Lagos, Nigeria",
            billing_address="Lagos, Nigeria",
            destination_country_code="NG",
            order_value=50,
            category_avg_value=40,
            is_first_order_from_customer=False,
        )
        assert result.value == 20

    def test_first_order_high_value_adds_score(self):
        result = check_fraud(
            shipping_address="Cairo, Egypt",
            billing_address="Cairo, Egypt",
            destination_country_code="EG",
            order_value=200,
            category_avg_value=40,
            is_first_order_from_customer=True,
        )
        assert result.value == 15

    def test_duplicate_payment_pattern_fails(self):
        result = check_fraud(
            shipping_address="Lagos, Nigeria",
            billing_address="Dubai, UAE",
            destination_country_code="NG",
            order_value=200,
            category_avg_value=40,
            is_first_order_from_customer=True,
            duplicate_payment_pattern_detected=True,
        )
        assert result.value == 90  # 25 + 20 + 15 + 30
        assert result.passed is False


class TestCheckStock:
    def test_passes_with_recent_confirmation_and_quantity(self):
        confirmed_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        result = check_stock(12, confirmed_at)
        assert result.passed is True

    def test_fails_when_confirmation_too_old(self):
        confirmed_at = datetime.now(timezone.utc) - timedelta(minutes=20)
        result = check_stock(12, confirmed_at)
        assert result.passed is False

    def test_fails_when_quantity_zero(self):
        confirmed_at = datetime.now(timezone.utc) - timedelta(minutes=2)
        result = check_stock(0, confirmed_at)
        assert result.passed is False

    def test_fails_when_supplier_did_not_respond(self):
        result = check_stock(12, None, supplier_responded=False)
        assert result.passed is False

    def test_fails_when_no_confirmation_at_all(self):
        result = check_stock(12, None)
        assert result.passed is False


class TestCheckDestination:
    def test_passes_when_route_approved(self):
        result = check_destination(True, "DE")
        assert result.passed is True

    def test_fails_when_route_not_approved(self):
        result = check_destination(False, "BR")
        assert result.passed is False


class TestCheckMargin:
    def test_passes_on_healthy_margin(self):
        result = check_margin(
            sale_price=39.99,
            supplier_price=9,
            amazon_fees=6,
            shipping_cost=5,
            refund_reserve=2,
            margin_at_listing_pct=21.0,
        )
        assert result.passed is True

    def test_fails_when_margin_below_minimum(self):
        result = check_margin(
            sale_price=20,
            supplier_price=15,
            amazon_fees=3,
            shipping_cost=1,
            refund_reserve=0.5,
        )
        assert result.passed is False

    def test_fails_on_sharp_margin_drop_since_listing(self):
        # margin_at_listing_pct=40 vs actual ~45% computed below would still pass,
        # so force a real drop: listing was 50%, actual is much lower but still >= 15%
        result = check_margin(
            sale_price=40,
            supplier_price=28,
            amazon_fees=4,
            shipping_cost=1,
            refund_reserve=1,
            margin_at_listing_pct=50.0,
        )
        assert result.passed is False


class TestCheckWallet:
    def test_passes_when_sufficient_liquidity(self):
        result = check_wallet(total_capital=100, active_exposure=20, emergency_reserve=40, order_cost=14)
        assert result.passed is True
        assert result.value == 40

    def test_fails_when_would_breach_reserve(self):
        result = check_wallet(total_capital=100, active_exposure=55, emergency_reserve=40, order_cost=14)
        assert result.passed is False
        assert result.value == 5


class TestCheckCompliance:
    def test_passes_when_clear(self):
        result = check_compliance("clear")
        assert result.passed is True

    def test_fails_when_restricted(self):
        result = check_compliance("restricted")
        assert result.passed is False

    def test_fails_when_blocked(self):
        result = check_compliance("blocked")
        assert result.passed is False