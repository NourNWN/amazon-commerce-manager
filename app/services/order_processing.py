from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.risk_check import RiskCheck
from app.models.wallet_transaction import WalletTransaction
from app.schemas.order_intake import OrderIntake
from app.services.order_context import build_risk_context
from app.services.risk.orchestrator import RiskEngineResult, run_all_checks


@dataclass
class ProcessedOrder:
    order: Order
    risk_result: RiskEngineResult | None  # None when the order was already processed earlier
    already_processed: bool


async def process_order(db: AsyncSession, intake: OrderIntake) -> ProcessedOrder:
    """
    Runs one incoming order through the full risk engine and persists the outcome:
    the order itself, one risk_checks row per check that ran, and a capital
    reservation in the wallet when (and only when) the order is authorized.
    """
    # Idempotency: the same Amazon order must never be processed (or paid for) twice
    existing = await db.scalar(select(Order).where(Order.amazon_order_id == intake.amazon_order_id))
    if existing is not None:
        return ProcessedOrder(order=existing, risk_result=None, already_processed=True)

    ctx, listing = await build_risk_context(db, intake)
    result = run_all_checks(ctx)

    order = Order(
        amazon_order_id=intake.amazon_order_id,
        listing_id=listing.id,
        destination_country=ctx.destination_country_code,
        sale_price=intake.sale_price,
        payment_status=intake.payment_status,
        received_at=datetime.now(timezone.utc),
        final_decision=result.decision,  # "authorized" / "stopped" / "pending_review"
        delivery_status="pending",
    )
    db.add(order)
    await db.flush()  # assigns order.id so the child rows below can reference it

    # Audit trail: only the checks that actually ran are recorded (the engine stops at the first failure)
    for check in result.checks:
        db.add(
            RiskCheck(
                order_id=order.id,
                check_name=check.check_name,
                result="pass" if check.passed else "fail",
                value=check.value,
                reason=check.reason,
            )
        )

    # Reserve capital only for authorized orders, so concurrent orders cannot overspend the wallet
    if result.decision == "authorized":
        exposure_after = ctx.active_exposure + ctx.order_cost
        db.add(
            WalletTransaction(
                order_id=order.id,
                type="reserve",
                amount=ctx.order_cost,
                balance_after=ctx.total_capital - exposure_after,
            )
        )

    await db.commit()
    await db.refresh(order)
    return ProcessedOrder(order=order, risk_result=result, already_processed=False)