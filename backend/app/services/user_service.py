from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_google_id(self, google_id: str) -> User | None:
        """Get user by Google ID."""
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        google_id: str,
        email: str,
        name: str,
        avatar_url: str | None = None
    ) -> User:
        """Create a new user."""
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_user(
        self,
        user: User,
        name: str | None = None,
        avatar_url: str | None = None
    ) -> User:
        """Update user information."""
        if name is not None:
            user.name = name
        if avatar_url is not None:
            user.avatar_url = avatar_url
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
