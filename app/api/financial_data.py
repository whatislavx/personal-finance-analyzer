from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.deps import get_db
from app.db.models.financial_data import FinancialData
from app.db.schemas.financial_data import (
    FinancialDataCreate,
    FinancialDataRead,
    FinancialDataUpdate,
)
from app.core.auth import get_current_user

router = APIRouter(prefix="/financial-data", tags=["financial_data"])


@router.post("/", response_model=FinancialDataRead, status_code=status.HTTP_201_CREATED)
async def create_record(
    record_in: FinancialDataCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    record = FinancialData(**record_in.model_dump())
    record.user_id = current_user.id
    db.add(record)

    await db.commit()
    await db.refresh(record)

    return record


@router.get("/", response_model=List[FinancialDataRead])
async def list_records(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        select(FinancialData)
        .where(FinancialData.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    resp = await db.execute(q)
    items = resp.scalars().all()

    return items


@router.get("/{record_id}", response_model=FinancialDataRead)
async def get_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(FinancialData).where(
        FinancialData.id == record_id, FinancialData.user_id == current_user.id
    )
    resp = await db.execute(q)
    item = resp.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Record not found")
    return item


@router.put("/{record_id}", response_model=FinancialDataRead)
async def update_record(
    record_id: uuid.UUID,
    record_in: FinancialDataUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(FinancialData).where(
        FinancialData.id == record_id, FinancialData.user_id == current_user.id
    )
    resp = await db.execute(q)
    item = resp.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Record not found")

    update_data = record_in.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(item, key, value)

    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(FinancialData).where(
        FinancialData.id == record_id, FinancialData.user_id == current_user.id
    )
    resp = await db.execute(q)
    item = resp.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Record not found")
    await db.delete(item)
    await db.commit()
    return None
