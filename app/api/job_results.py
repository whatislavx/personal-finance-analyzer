from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.deps import get_db
from app.db.models.job_results import JobResult
from app.db.schemas.job_results import JobResultCreate, JobResultRead, JobResultUpdate
from app.core.auth import get_current_user
from app.db.models.jobs import Job

router = APIRouter(prefix="/job-results", tags=["job_results"])


@router.post("/", response_model=JobResultRead, status_code=status.HTTP_201_CREATED)
async def create_result(
    result_in: JobResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await db.get(Job, result_in.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    result = JobResult(**result_in.model_dump())
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result


@router.get("/", response_model=List[JobResultRead])
async def list_results(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        select(JobResult)
        .join(Job)
        .where(Job.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    resp = await db.execute(q)
    items = resp.scalars().all()
    return items


@router.get("/{result_id}", response_model=JobResultRead)
async def get_result(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = await db.get(JobResult, result_id)
    if not item:
        raise HTTPException(status_code=404, detail="Result not found")
    job = await db.get(Job, item.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Result not found")
    return item


@router.put("/{result_id}", response_model=JobResultRead)
async def update_result(
    result_id: uuid.UUID,
    result_in: JobResultUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = await db.get(JobResult, result_id)
    if not item:
        raise HTTPException(status_code=404, detail="Result not found")
    job = await db.get(Job, item.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Result not found")
    update_data = result_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(item, k, v)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_result(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = await db.get(JobResult, result_id)
    if not item:
        raise HTTPException(status_code=404, detail="Result not found")
    job = await db.get(Job, item.job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Result not found")
    await db.delete(item)
    await db.commit()
    return None
