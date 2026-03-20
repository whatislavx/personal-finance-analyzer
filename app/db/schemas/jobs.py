from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
import datetime


class JobBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    priority: Optional[int] = 0
    result_url: Optional[str] = None


class JobCreate(JobBase):
    user_id: uuid.UUID


class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[int] = None
    result_url: Optional[str] = None


class JobRead(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None

