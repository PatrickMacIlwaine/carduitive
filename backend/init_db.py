import asyncio
from sqlalchemy import text
from app.database import engine, Base

# Add new ALTER TABLE statements here as the schema evolves.
# Each must be idempotent (use IF NOT EXISTS / IF EXISTS).
MIGRATIONS = [
    "ALTER TABLE leaderboard ADD COLUMN IF NOT EXISTS game_config JSON",
]


async def init():
    async with engine.begin() as conn:
        # Create any new tables
        await conn.run_sync(Base.metadata.create_all)

        # Run incremental migrations for existing tables
        for migration in MIGRATIONS:
            await conn.execute(text(migration))

if __name__ == "__main__":
    asyncio.run(init())
    print("Database initialized successfully")
