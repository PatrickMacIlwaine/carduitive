from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models import LeaderboardEntry

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


class LeaderboardEntryResponse(BaseModel):
    id: int
    group_name: str
    score: int
    games_played: int
    game_config: Optional[dict] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateLeaderboardEntryRequest(BaseModel):
    group_name: str
    score: int
    games_played: int = 1


class UpdateLeaderboardEntryRequest(BaseModel):
    score: Optional[int] = None
    games_played: Optional[int] = None


@router.get("", response_model=List[LeaderboardEntryResponse])
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100, description="Number of entries to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get top leaderboard entries sorted by score (highest first)."""
    result = await db.execute(
        select(LeaderboardEntry)
        .order_by(desc(LeaderboardEntry.score))
        .limit(limit)
    )
    entries = result.scalars().all()
    return entries


@router.post("", response_model=LeaderboardEntryResponse)
async def create_leaderboard_entry(
    entry: CreateLeaderboardEntryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new leaderboard entry or update if group_name exists."""
    # Check if group already exists
    result = await db.execute(
        select(LeaderboardEntry).where(LeaderboardEntry.group_name == entry.group_name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing entry — keep highest score, increment games played
        if entry.score > existing.score:
            existing.score = entry.score
        existing.games_played += entry.games_played
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        # Create new entry
        new_entry = LeaderboardEntry(
            group_name=entry.group_name,
            score=entry.score,
            games_played=entry.games_played
        )
        db.add(new_entry)
        await db.commit()
        await db.refresh(new_entry)
        return new_entry


@router.get("/stats", response_model=dict)
async def get_leaderboard_stats(db: AsyncSession = Depends(get_db)):
    """Get summary statistics for the leaderboard."""
    # Count total teams
    result = await db.execute(select(LeaderboardEntry))
    total_teams = len(result.scalars().all())
    
    # Get high score
    result = await db.execute(
        select(LeaderboardEntry)
        .order_by(desc(LeaderboardEntry.score))
        .limit(1)
    )
    top_entry = result.scalar_one_or_none()
    high_score = top_entry.score if top_entry else 0
    
    # Mock games today (will be replaced with real data later)
    games_today = 0
    
    return {
        "total_teams": total_teams,
        "high_score": high_score,
        "games_today": games_today
    }


@router.get("/{entry_id}", response_model=LeaderboardEntryResponse)
async def get_leaderboard_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific leaderboard entry by ID."""
    result = await db.execute(
        select(LeaderboardEntry).where(LeaderboardEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Leaderboard entry not found")
    
    return entry
