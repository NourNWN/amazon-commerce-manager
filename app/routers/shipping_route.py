from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.shipping_route import ShippingRoute
from app.schemas.shipping_route import ShippingRouteCreate, ShippingRouteResponse

router = APIRouter(prefix="/shipping-routes", tags=["shipping-routes"])


@router.post("", response_model=ShippingRouteResponse, status_code=201)
async def create_shipping_route(payload: ShippingRouteCreate, db: AsyncSession = Depends(get_db)):
    route = ShippingRoute(**payload.model_dump())
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return route


@router.get("", response_model=list[ShippingRouteResponse])
async def list_shipping_routes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ShippingRoute))
    return result.scalars().all()
