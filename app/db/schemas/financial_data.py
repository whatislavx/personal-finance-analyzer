from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
import datetime
from decimal import Decimal

from app.db.models.financial_data import TransactionType


class FinancialDataBase(BaseModel):
    date: Optional[datetime.datetime] = None
    category: str
    amount: Decimal
    type: TransactionType
    description: Optional[str] = None


class FinancialDataCreate(FinancialDataBase):
    job_id: Optional[uuid.UUID] = None


class FinancialDataUpdate(BaseModel):
    date: Optional[datetime.datetime] = None
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    type: Optional[TransactionType] = None
    description: Optional[str] = None


class FinancialDataRead(FinancialDataBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    created_at: datetime.datetime
