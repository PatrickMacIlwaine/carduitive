from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Counter

router = APIRouter(prefix="/api/counter", tags=["counter"])


class CounterResponse(BaseModel):
    value: int
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=CounterResponse)
async def get_counter(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Counter).where(Counter.id == 1))
    counter = result.scalar_one_or_none()
    
    if not counter:
        counter = Counter(id=1, value=0)
        db.add(counter)
        await db.commit()
        await db.refresh(counter)
    
    return counter


@router.post("/increment", response_model=CounterResponse)
async def increment_counter(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Counter).where(Counter.id == 1))
    counter = result.scalar_one_or_none()
    
    if not counter:
        counter = Counter(id=1, value=0)
        db.add(counter)
    
    counter.value += 1
    await db.commit()
    await db.refresh(counter)
    
    # Broadcast to all connected clients (using a general broadcast if available)
    # For now, we'll skip broadcasting since the counter demo is being replaced by lobbies
    # await lobby_manager_ws.broadcast_to_lobby(json.dumps({
    #     "type": "counter_update",
    #     "value": counter.value
    # }), "general")
    
    return counter
