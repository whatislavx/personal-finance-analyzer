from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.users import User


async def get_user(db: AsyncSession, user_id) -> Optional[User]:
    return await db.get(User, user_id)


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    q = select(User).where(User.username == username)
    resp = await db.execute(q)
    return resp.scalars().first()


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    q = select(User).offset(skip).limit(limit)
    resp = await db.execute(q)
    return list(resp.scalars().all())


async def create_user(db: AsyncSession, *, username: str, email: str) -> User:
    user = User(username=username, email=email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, update_data: dict) -> User:
    for k, v in update_data.items():
        setattr(user, k, v)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()
