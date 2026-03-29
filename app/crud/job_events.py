from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.job_events import JobEvent


async def get_event(db: AsyncSession, event_id) -> Optional[JobEvent]:
    return await db.get(JobEvent, event_id)


async def list_events_for_user(db: AsyncSession, user_id, skip: int = 0, limit: int = 100) -> List[JobEvent]:
    # join with jobs to filter by job.owner/user_id
    from app.db.models.jobs import Job
    q = select(JobEvent).join(Job).where(Job.user_id == user_id).offset(skip).limit(limit)
    resp = await db.execute(q)
    return list(resp.scalars().all())


async def create_event(db: AsyncSession, data: dict) -> JobEvent:
    event = JobEvent(**data)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def update_event(db: AsyncSession, event: JobEvent, update_data: dict) -> JobEvent:
    for k, v in update_data.items():
        setattr(event, k, v)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def delete_event(db: AsyncSession, event: JobEvent) -> None:
    await db.delete(event)
    await db.commit()
