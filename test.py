# from app.services.risk.checks import check_payment
#
# result = check_payment("complete")
# print(result)  # يجب أن يطبع passed=True
#
# result2 = check_payment("pending")
# print(result2)  # يجب أن يطبع passed=False
# مع سبب

# from app.services.risk.checks import check_fraud
#
# # حالة نظيفة - يجب أن تمر
# r1 = check_fraud("Cairo, Egypt", "Cairo, Egypt", "EG", 50, 40, False)
# print(r1)
#
# # حالة مشبوهة - يجب أن تفشل
# r2 = check_fraud("Lagos, Nigeria", "Dubai, UAE", "NG", 200, 40, True, True)
# print(r2)

# from datetime import datetime, timezone, timedelta
# from app.services.risk.checks import check_stock
#
# # تأكيد حديث وكمية متوفرة - يجب أن يمر
# r1 = check_stock(12, datetime.now(timezone.utc) - timedelta(minutes=5))
# print(r1)
#
# # تأكيد قديم جدًا - يجب أن يفشل
# r2 = check_stock(12, datetime.now(timezone.utc) - timedelta(minutes=20))
# print(r2)
#
# # كمية صفر - يجب أن يفشل
# r3 = check_stock(0, datetime.now(timezone.utc) - timedelta(minutes=2))
# print(r3)

# from app.services.risk.checks import check_destination
#
# r1 = check_destination(True, "DE")
# print(r1)  # يجب أن يمر
#
# r2 = check_destination(False, "BR")
# print(r2)  # يجب أن يفشل

# from app.services.risk.checks import check_margin
#
# # هامش جيد - يجب أن يمر
# r1 = check_margin(sale_price=39.99, supplier_price=9, amazon_fees=6, shipping_cost=5, refund_reserve=2, margin_at_listing_pct=21.0)
# print(r1)
#
# # هامش منخفض جدًا - يجب أن يفشل
# r2 = check_margin(sale_price=20, supplier_price=15, amazon_fees=3, shipping_cost=1, refund_reserve=0.5)
# print(r2)

# from app.services.risk.checks import check_wallet
#
# # سيولة كافية - يجب أن يمر
# r1 = check_wallet(total_capital=100, active_exposure=20, emergency_reserve=40, order_cost=14)
# print(r1)  # available = 40، 14 <= 40 → passed
#
# # سيولة غير كافية - يجب أن يفشل
# r2 = check_wallet(total_capital=100, active_exposure=55, emergency_reserve=40, order_cost=14)
# print(r2)  # available = 5، 14 > 5 → failed

# from app.services.risk.checks import check_compliance
#
# r1 = check_compliance("clear")
# print(r1)  # passed=True
#
# r2 = check_compliance("restricted")
# print(r2)  # passed=False

from datetime import datetime, timezone, timedelta
from app.services.risk.orchestrator import OrderRiskContext, run_all_checks

ctx = OrderRiskContext(
    payment_status="pending",
    payment_pending_since=None,
    shipping_address="Berlin, Germany",
    billing_address="Berlin, Germany",
    destination_country_code="DE",
    order_value=39.99,
    category_avg_value=35,
    is_first_order_from_customer=True,
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

result = run_all_checks(ctx)
print(result.decision)        # يجب أن يطبع: authorized
for c in result.checks:
    print(c)