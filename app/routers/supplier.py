from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierResponse

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(payload: SupplierCreate, db: AsyncSession = Depends(get_db)):
    supplier = Supplier(
        name=payload.name,
        platform=payload.platform,
        blind_shipping_confirmed=payload.blind_shipping_confirmed,
        contact_method=payload.contact_method,
        api_available=payload.api_available,
        approved_by=payload.approved_by,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.get("", response_model=list[SupplierResponse])
async def list_suppliers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier))
    return result.scalars().all()
