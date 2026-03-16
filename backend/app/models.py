from sqlalchemy import Column, Integer, DateTime, func, String, Boolean
from app.database import Base


class Counter(Base):
    __tablename__ = "counter"

    id = Column(Integer, primary_key=True, default=1)
    value = Column(Integer, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(100), nullable=False, index=True)
    score = Column(Integer, nullable=False, default=0)
    games_played = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
