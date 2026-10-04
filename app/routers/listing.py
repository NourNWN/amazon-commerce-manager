from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.listing import Listing
from app.schemas.listing import ListingCreate, ListingResponse

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("", response_model=ListingResponse, status_code=201)
async def create_listing(payload: ListingCreate, db: AsyncSession = Depends(get_db)):
    listing = Listing(**payload.model_dump(), published_at=datetime.now(timezone.utc))
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing


@router.get("", response_model=list[ListingResponse])
async def list_listings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing))
    return result.scalars().all()
