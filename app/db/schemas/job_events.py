from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
import datetime


class JobEventBase(BaseModel):
    type: str
    message: Optional[str] = None


class JobEventCreate(JobEventBase):
    job_id: uuid.UUID


class JobEventUpdate(BaseModel):
    type: Optional[str] = None
    message: Optional[str] = None


class JobEventRead(JobEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    created_at: datetime.datetime

