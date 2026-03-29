from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.job_results import JobResult


async def get_result(db: AsyncSession, result_id) -> Optional[JobResult]:
    return await db.get(JobResult, result_id)


async def list_results_for_user(db: AsyncSession, user_id, skip: int = 0, limit: int = 100) -> List[JobResult]:
    from app.db.models.jobs import Job
    q = select(JobResult).join(Job).where(Job.user_id == user_id).offset(skip).limit(limit)
    resp = await db.execute(q)
    return list(resp.scalars().all())


async def create_result(db: AsyncSession, data: dict) -> JobResult:
    item = JobResult(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_result(db: AsyncSession, item: JobResult, update_data: dict) -> JobResult:
    for k, v in update_data.items():
        setattr(item, k, v)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_result(db: AsyncSession, item: JobResult) -> None:
    await db.delete(item)
    await db.commit()
