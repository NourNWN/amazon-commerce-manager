from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order_intake import OrderIntake, OrderIntakeResponse, RiskCheckOutcome
from app.schemas.readonly import OrderResponse
from app.services.order_context import ListingNotFoundError
from app.services.order_processing import process_order

router = APIRouter(prefix="/orders", tags=["order-intake"])


@router.post("/intake", response_model=OrderIntakeResponse)
async def intake_order(payload: OrderIntake, db: AsyncSession = Depends(get_db)):
    """
    Entry point for a new customer order. Runs the full risk engine and stores the outcome.
    Note: "authorized" only means the order may proceed to supplier purchase - nothing is bought here.
    """
    try:
        processed = await process_order(db, payload)
    except ListingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    result = processed.risk_result
    checks = []
    if result is not None:
        checks = [
            RiskCheckOutcome(
                check_name=c.check_name,
                passed=c.passed,
                value=float(c.value) if c.value is not None else None,
                reason=c.reason,
            )
            for c in result.checks
        ]

    return OrderIntakeResponse(
        order=OrderResponse.model_validate(processed.order),
        decision=processed.order.final_decision,
        failed_check=result.failed_check if result is not None else None,
        checks=checks,
        already_processed=processed.already_processed,
    )