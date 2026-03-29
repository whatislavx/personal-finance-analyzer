from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.financial_data import FinancialData


async def get_record(db: AsyncSession, record_id) -> Optional[FinancialData]:
    return await db.get(FinancialData, record_id)


async def list_records_for_user(db: AsyncSession, user_id, skip: int = 0, limit: int = 100) -> List[FinancialData]:
    q = select(FinancialData).where(FinancialData.user_id == user_id).offset(skip).limit(limit)
    resp = await db.execute(q)
    return list(resp.scalars().all())


async def create_record(db: AsyncSession, data: dict) -> FinancialData:
    item = FinancialData(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_record(db: AsyncSession, item: FinancialData, update_data: dict) -> FinancialData:
    for k, v in update_data.items():
        setattr(item, k, v)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_record(db: AsyncSession, item: FinancialData) -> None:
    await db.delete(item)
    await db.commit()
