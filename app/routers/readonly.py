"""
Read-only endpoints for tables populated by internal business logic
(the future order-processing flow), not by direct manual creation.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order
from app.models.risk_check import RiskCheck
from app.models.wallet_transaction import WalletTransaction
from app.models.account_health_snapshot import AccountHealthSnapshot
from app.schemas.readonly import (
    OrderResponse,
    RiskCheckResponse,
    WalletTransactionResponse,
    AccountHealthSnapshotResponse,
)

router = APIRouter(tags=["read-only"])


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order))
    return result.scalars().all()


@router.get("/risk-checks", response_model=list[RiskCheckResponse])
async def list_risk_checks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RiskCheck))
    return result.scalars().all()


@router.get("/wallet-transactions", response_model=list[WalletTransactionResponse])
async def list_wallet_transactions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WalletTransaction))
    return result.scalars().all()


@router.get("/account-health", response_model=list[AccountHealthSnapshotResponse])
async def list_account_health(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccountHealthSnapshot))
    return result.scalars().all()
