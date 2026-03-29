from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.jobs import Job


async def get_job(db: AsyncSession, job_id) -> Optional[Job]:
    return await db.get(Job, job_id)


async def list_jobs_for_user(db: AsyncSession, user_id, skip: int = 0, limit: int = 100) -> List[Job]:
    q = select(Job).where(Job.user_id == user_id).offset(skip).limit(limit)
    resp = await db.execute(q)
    return list(resp.scalars().all())


async def create_job(db: AsyncSession, user_id, data: dict) -> Job:
    job = Job(**data)
    job.user_id = user_id
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def update_job(db: AsyncSession, job: Job, update_data: dict) -> Job:
    for k, v in update_data.items():
        setattr(job, k, v)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def delete_job(db: AsyncSession, job: Job) -> None:
    await db.delete(job)
    await db.commit()
