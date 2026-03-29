from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.deps import get_db
from app.db.models.job_events import JobEvent
from app.db.schemas.job_events import JobEventCreate, JobEventRead, JobEventUpdate

router = APIRouter(prefix="/job-events", tags=["job_events"])


@router.post("/", response_model=JobEventRead, status_code=status.HTTP_201_CREATED)
async def create_event(event_in: JobEventCreate, db: AsyncSession = Depends(get_db)):
    event = JobEvent(**event_in.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/", response_model=List[JobEventRead])
async def list_events(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JobEvent).offset(skip).limit(limit))
    items = result.scalars().all()
    return items


@router.get("/{event_id}", response_model=JobEventRead)
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    event = await db.get(JobEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=JobEventRead)
async def update_event(event_id: uuid.UUID, event_in: JobEventUpdate, db: AsyncSession = Depends(get_db)):
    event = await db.get(JobEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    update_data = event_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(event, k, v)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    event = await db.get(JobEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
    await db.commit()
    return None

