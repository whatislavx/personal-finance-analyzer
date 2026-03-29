from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from app.db.deps import get_db
from app.db.models.jobs import Job
from app.db.schemas.jobs import JobCreate, JobRead, JobUpdate
from app.core.auth import get_current_user
from app.core.rabbit import send_job_message

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(job_in: JobCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    job = Job(**job_in.model_dump())
    job.user_id = current_user.id
    db.add(job)

    await db.commit()
    await db.refresh(job)

    # Publish message to RabbitMQ (fire-and-forget)
    try:
        asyncio.create_task(send_job_message({"job_id": str(job.id), "user_id": str(current_user.id)}))
    except Exception:
        # non-fatal if RabbitMQ not configured
        pass

    return job


@router.get("/", response_model=List[JobRead])
async def list_jobs(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    q = select(Job).where(Job.user_id == current_user.id).offset(skip).limit(limit)
    result = await db.execute(q)
    items = result.scalars().all()

    return items


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    job = await db.get(Job, job_id)

    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.put("/{job_id}", response_model=JobRead)
async def update_job(job_id: uuid.UUID, job_in: JobUpdate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    job = await db.get(Job, job_id)

    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = job_in.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(job, k, v)

    db.add(job)
    await db.commit()
    await db.refresh(job)

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    job = await db.get(Job, job_id)

    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    await db.delete(job)
    await db.commit()

    return None


# WebSocket endpoint to stream job events in near real-time using polling
@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_events(websocket: WebSocket, job_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    await websocket.accept()
    try:
        from app.db.models.job_events import JobEvent
        last_seen = None
        while True:
            # fetch new events for this job
            q = select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at)
            resp = await db.execute(q)
            events = resp.scalars().all()
            payload = [ {"id": str(e.id), "type": e.type, "message": e.message, "created_at": str(e.created_at)} for e in events ]
            await websocket.send_json({"events": payload})
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return
