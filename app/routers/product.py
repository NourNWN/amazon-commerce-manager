from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(
        supplier_id=payload.supplier_id,
        supplier_sku=payload.supplier_sku,
        title=payload.title,
        supplier_price=payload.supplier_price,
        stock_qty=payload.stock_qty,
        compliance_flag=payload.compliance_flag,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("", response_model=list[ProductResponse])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    return result.scalars().all()


@router.post("/{product_id}/refresh-stock", response_model=ProductResponse)
async def refresh_stock(product_id: UUID, stock_qty: int, db: AsyncSession = Depends(get_db)):
    """
    DEV/TEST ONLY: manually sets the stock quantity and marks it as freshly confirmed.
    To be replaced by an automated supplier sync job (API polling) later.
    """
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    now = datetime.now(timezone.utc)
    product.stock_qty = stock_qty
    product.last_stock_check = now
    product.last_price_check = now
    await db.commit()
    await db.refresh(product)
    return product